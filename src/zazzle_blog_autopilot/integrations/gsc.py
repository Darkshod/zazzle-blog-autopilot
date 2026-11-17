"""Google Search Console REST API client (Search Analytics & URL Inspection)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import requests


class GoogleSearchConsoleClient:
    """Queries Google Search Console when an OAuth access token or credentials file is configured."""

    READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

    def __init__(self, site_url: str, access_token: str | None = None) -> None:
        self.site_url = site_url.rstrip("/") + "/"
        self.credentials_path = (os.getenv("GSC_CREDENTIALS_PATH") or "").strip()
        self.access_token = (access_token or os.getenv("GSC_ACCESS_TOKEN") or "").strip()
        if not self.access_token and self.credentials_path:
            self.access_token = self._token_from_credentials(self.credentials_path)

    @classmethod
    def _token_from_credentials(cls, cred_path: str) -> str:
        if not os.path.exists(cred_path):
            return ""
        try:
            import json
            data = json.loads(open(cred_path, encoding="utf-8").read())
            if data.get("type") == "service_account":
                from google.oauth2 import service_account
                from google.auth.transport.requests import Request as GoogleRequest

                creds = service_account.Credentials.from_service_account_file(
                    cred_path, scopes=[cls.READONLY_SCOPE]
                )
                creds.refresh(GoogleRequest())
                return creds.token or ""
            if data.get("refresh_token") and data.get("client_id") and data.get("client_secret"):
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request as GoogleRequest

                creds = Credentials.from_authorized_user_info(data, scopes=[cls.READONLY_SCOPE])
                if not creds.valid:
                    creds.refresh(GoogleRequest())
                return creds.token or ""
            return str(data.get("token") or data.get("access_token") or "").strip()
        except Exception:
            return ""

    @property
    def is_connected(self) -> bool:
        return bool(self.access_token)

    def fetch_search_analytics(
        self,
        days: int = 28,
        row_limit: int = 50,
        dimensions: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.is_connected:
            return {
                "connected": False,
                "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured. See docs/GSC_SETUP_GUIDE.md.",
                "rows": [],
            }

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
        encoded_site = quote(self.site_url, safe="")
        endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"

        payload: dict[str, Any] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rowLimit": row_limit,
        }
        if dimensions is not None:
            payload["dimensions"] = dimensions
        else:
            payload["dimensions"] = ["query", "page"]

        resp = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if resp.status_code != 200:
            return {"connected": False, "reason": f"GSC API HTTP {resp.status_code}", "rows": []}

        data = resp.json()
        return {"connected": True, "rows": data.get("rows", [])}

    def list_sitemaps(self) -> dict[str, Any]:
        if not self.is_connected:
            return {"connected": False, "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured.", "sitemaps": []}
        encoded_site = quote(self.site_url, safe="")
        endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/sitemaps"
        resp = requests.get(endpoint, headers={"Authorization": f"Bearer {self.access_token}"}, timeout=15)
        if resp.status_code != 200:
            return {"connected": False, "reason": f"GSC API HTTP {resp.status_code}", "sitemaps": []}
        return {"connected": True, "sitemaps": resp.json().get("sitemap", [])}

    def fetch_full_report(self, windows: tuple[int, ...] = (7, 28, 90)) -> dict[str, Any]:
        if not self.is_connected:
            return {
                "connected": False,
                "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured.",
                "windows": {},
            }
        out: dict[str, Any] = {"connected": True, "sitemaps": self.list_sitemaps(), "windows": {}}
        for w in windows:
            out["windows"][f"{w}d"] = {
                "totals": self.fetch_search_analytics(days=w, row_limit=1, dimensions=[]),
                "query_page": self.fetch_search_analytics(days=w, row_limit=100, dimensions=["query", "page"]),
                "country": self.fetch_search_analytics(days=w, row_limit=50, dimensions=["country"]),
                "device": self.fetch_search_analytics(days=w, row_limit=10, dimensions=["device"]),
            }
        return out

    def inspect_url(self, page_url: str) -> dict[str, Any]:
        if not self.is_connected:
            return {"connected": False, "url": page_url, "index_status": "unknown (GSC unconnected)"}

        resp = requests.post(
            "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json={"inspectionUrl": page_url, "siteUrl": self.site_url},
            timeout=15,
        )
        if resp.status_code != 200:
            return {"connected": False, "url": page_url, "index_status": f"HTTP {resp.status_code}"}
        result = resp.json().get("inspectionResult", {}).get("indexStatusResult", {})
        return {
            "connected": True,
            "url": page_url,
            "index_status": result.get("verdict", "UNKNOWN"),
            "coverage_state": result.get("coverageState", ""),
        }

    def submit_sitemap(self, sitemap_url: str) -> dict[str, Any]:
        if not self.is_connected:
            return {"submitted": False, "reason": "GSC_ACCESS_TOKEN not configured."}
        encoded_site = quote(self.site_url, safe="")
        encoded_sm = quote(sitemap_url, safe="")
        endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/sitemaps/{encoded_sm}"
        resp = requests.put(endpoint, headers={"Authorization": f"Bearer {self.access_token}"}, timeout=15)
        return {"submitted": resp.status_code in (200, 204), "status_code": resp.status_code}
