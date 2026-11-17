"""Google Search Console REST API client (Search Analytics & URL Inspection)."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


def validate_service_account_file(cred_path: str | Path) -> dict[str, Any]:
    """Validate a Google service account JSON file without exposing private keys."""
    p = Path(cred_path)
    if not p.exists():
        return {"valid": False, "reason": "Credentials file not found."}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"valid": False, "reason": f"Invalid JSON: {exc}"}
    if not isinstance(data, dict) or data.get("type") != "service_account":
        return {"valid": False, "reason": "Credential type must be 'service_account'."}
    required = ("client_email", "private_key", "token_uri")
    missing = [k for k in required if not str(data.get(k) or "").strip()]
    if missing:
        return {"valid": False, "reason": f"Missing required fields: {', '.join(missing)}"}
    return {
        "valid": True,
        "type": "service_account",
        "project_id": str(data.get("project_id") or ""),
        "client_email": str(data.get("client_email") or ""),
        "has_private_key": True,
    }


def date_range_for_window(days: int, delay_days: int = 2, today: date | None = None) -> tuple[date, date]:
    """Return (start_date, end_date) accounting for Google Search Console reporting delay."""
    ref_today = today or datetime.now(timezone.utc).date()
    end_date = ref_today - timedelta(days=max(0, delay_days))
    start_date = end_date - timedelta(days=max(1, days) - 1)
    return start_date, end_date


def redact_secrets(value: Any) -> Any:
    """Recursively redact sensitive keys and bearer tokens from dicts/lists/strings."""
    secret_keys = {"private_key", "access_token", "refresh_token", "client_secret", "token"}
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if str(k).lower() in secret_keys else redact_secrets(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer [REDACTED]", value)
        if "BEGIN PRIVATE KEY" in value:
            return "[REDACTED_PRIVATE_KEY]"
    return value


def save_historical_report(report: dict[str, Any], reports_dir: Path) -> dict[str, Any]:
    """Persist timestamped GSC reports safely without overwriting valid history with empty/failed runs."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    history_dir = reports_dir / "gsc_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = reports_dir / "gsc_latest.json"

    if not report.get("connected"):
        return {"saved": False, "reason": "Disconnected report not written over historical data."}

    clean = redact_secrets(report)
    windows = clean.get("windows", {})
    has_rows = any(
        bool(w.get(dim, {}).get("rows"))
        for w in windows.values()
        if isinstance(w, dict)
        for dim in ("totals", "query_page", "country", "device", "daily")
    )
    if latest_path.exists() and not has_rows:
        try:
            prev = json.loads(latest_path.read_text(encoding="utf-8"))
            if prev.get("connected"):
                prev_has_rows = any(
                    bool(w.get(dim, {}).get("rows"))
                    for w in prev.get("windows", {}).values()
                    if isinstance(w, dict)
                    for dim in ("totals", "query_page", "country", "device", "daily")
                )
                if prev_has_rows:
                    return {"saved": False, "reason": "Preserved existing non-empty historical report."}
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    clean.setdefault("generated_at", now.isoformat())
    # Deduplicate identical same-day snapshot
    day_prefix = now.strftime("%Y%m%d")
    comparable = {k: v for k, v in clean.items() if k != "generated_at"}
    for existing in sorted(history_dir.glob(f"gsc_report_{day_prefix}_*.json")):
        try:
            prev_obj = json.loads(existing.read_text(encoding="utf-8"))
            if {k: v for k, v in prev_obj.items() if k != "generated_at"} == comparable:
                return {"saved": False, "reason": "Duplicate same-day report skipped.", "path": str(existing)}
        except Exception:
            pass

    hist_path = history_dir / f"gsc_report_{now.strftime('%Y%m%d_%H%M%S')}.json"
    serialized = json.dumps(clean, indent=2)
    hist_path.write_text(serialized, encoding="utf-8")
    latest_path.write_text(serialized, encoding="utf-8")
    return {"saved": True, "history_path": str(hist_path), "latest_path": str(latest_path)}


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

    def _request_with_retry(self, method: str, url: str, max_retries: int = 2, **kwargs: Any) -> requests.Response:
        for attempt in range(max_retries + 1):
            resp = requests.request(method, url, timeout=15, **kwargs)
            if resp.status_code not in (429, 500, 502, 503) or attempt == max_retries:
                return resp
            time.sleep(0.2 * (attempt + 1))
        return resp  # pragma: no cover

    def list_verified_sites(self) -> dict[str, Any]:
        if not self.is_connected:
            return {"connected": False, "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured.", "sites": []}
        resp = self._request_with_retry(
            "GET",
            "https://www.googleapis.com/webmasters/v3/sites",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        if resp.status_code != 200:
            return {"connected": False, "reason": f"GSC API HTTP {resp.status_code}", "sites": []}
        return {"connected": True, "sites": resp.json().get("siteEntry", [])}

    def fetch_search_analytics(
        self,
        days: int = 28,
        row_limit: int = 50,
        dimensions: list[str] | None = None,
        delay_days: int = 2,
    ) -> dict[str, Any]:
        if not self.is_connected:
            return {
                "connected": False,
                "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured. See docs/GSC_SETUP_GUIDE.md.",
                "rows": [],
            }

        start_date, end_date = date_range_for_window(days=days, delay_days=delay_days)
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

        resp = self._request_with_retry(
            "POST",
            endpoint,
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json=payload,
        )
        if resp.status_code != 200:
            return {"connected": False, "reason": f"GSC API HTTP {resp.status_code}", "rows": []}

        data = resp.json()
        return {
            "connected": True,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rows": data.get("rows", []),
        }

    def list_sitemaps(self) -> dict[str, Any]:
        if not self.is_connected:
            return {"connected": False, "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured.", "sitemaps": []}
        encoded_site = quote(self.site_url, safe="")
        endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/sitemaps"
        resp = self._request_with_retry(
            "GET", endpoint, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if resp.status_code != 200:
            return {"connected": False, "reason": f"GSC API HTTP {resp.status_code}", "sitemaps": []}
        return {"connected": True, "sitemaps": resp.json().get("sitemap", [])}

    def fetch_full_report(self, windows: tuple[int, ...] = (7, 28, 90), delay_days: int = 2) -> dict[str, Any]:
        if not self.is_connected:
            return {
                "connected": False,
                "reason": "GSC_ACCESS_TOKEN / GSC_CREDENTIALS_PATH not configured.",
                "windows": {},
            }
        sites_res = self.list_verified_sites()
        sitemaps_res = self.list_sitemaps()
        out: dict[str, Any] = {
            "connected": bool(sites_res.get("connected") or sitemaps_res.get("connected")),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "reporting_delay_days": delay_days,
            "sites": sites_res,
            "sitemaps": sitemaps_res,
            "windows": {},
        }
        if not out["connected"]:
            out["reason"] = sites_res.get("reason") or sitemaps_res.get("reason") or "GSC API request failed."
        for w in windows:
            out["windows"][f"{w}d"] = {
                "totals": self.fetch_search_analytics(days=w, row_limit=1, dimensions=[], delay_days=delay_days),
                "query_page": self.fetch_search_analytics(days=w, row_limit=100, dimensions=["query", "page"], delay_days=delay_days),
                "country": self.fetch_search_analytics(days=w, row_limit=50, dimensions=["country"], delay_days=delay_days),
                "device": self.fetch_search_analytics(days=w, row_limit=10, dimensions=["device"], delay_days=delay_days),
                "daily": self.fetch_search_analytics(days=w, row_limit=100, dimensions=["date"], delay_days=delay_days),
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
