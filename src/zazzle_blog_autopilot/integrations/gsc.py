"""Google Search Console REST API client (Search Analytics & URL Inspection)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import requests


class GoogleSearchConsoleClient:
    """Queries Google Search Console when an OAuth access token is configured."""

    def __init__(self, site_url: str, access_token: str | None = None) -> None:
        self.site_url = site_url.rstrip("/") + "/"
        self.access_token = (access_token or os.getenv("GSC_ACCESS_TOKEN") or "").strip()
        self.credentials_path = (os.getenv("GSC_CREDENTIALS_PATH") or "").strip()

    @property
    def is_connected(self) -> bool:
        return bool(self.access_token)

    def fetch_search_analytics(self, days: int = 28, row_limit: int = 50) -> dict[str, Any]:
        if not self.is_connected:
            return {
                "connected": False,
                "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured. See docs/GSC_SETUP.md.",
                "rows": [],
            }

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
        encoded_site = quote(self.site_url, safe="")
        endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"

        resp = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json={
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["query", "page"],
                "rowLimit": row_limit,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return {"connected": False, "reason": f"GSC API HTTP {resp.status_code}", "rows": []}

        data = resp.json()
        return {"connected": True, "rows": data.get("rows", [])}

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
