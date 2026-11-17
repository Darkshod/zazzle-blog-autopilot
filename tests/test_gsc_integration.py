"""Phase 7 GSC integration tests: validation, auth errors, responses, dates, storage, redaction, gitignore."""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from zazzle_blog_autopilot.integrations.gsc import (
    GoogleSearchConsoleClient,
    date_range_for_window,
    redact_secrets,
    save_historical_report,
    validate_service_account_file,
)


def test_credential_file_validation_and_missing(tmp_path: Path) -> None:
    missing = validate_service_account_file(tmp_path / "missing.json")
    assert missing["valid"] is False

    bad_type = tmp_path / "bad.json"
    bad_type.write_text(json.dumps({"type": "authorized_user"}), encoding="utf-8")
    assert validate_service_account_file(bad_type)["valid"] is False

    valid_sa = tmp_path / "sa.json"
    valid_sa.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "darkshod-seo",
                "client_email": "gsc@darkshod-seo.iam.gserviceaccount.com",
                "private_key": "-----BEGIN PRIVATE KEY-----\nFAKE_KEY_FOR_TEST\n-----END PRIVATE KEY-----\n",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        ),
        encoding="utf-8",
    )
    res = validate_service_account_file(valid_sa)
    assert res["valid"] is True
    assert res["client_email"] == "gsc@darkshod-seo.iam.gserviceaccount.com"
    assert "private_key" not in res


def test_date_range_calculations_with_gsc_delay() -> None:
    start, end = date_range_for_window(days=7, delay_days=2, today=date(2026, 11, 17))
    assert end == date(2026, 11, 15)
    assert start == date(2026, 11, 9)

    start28, end28 = date_range_for_window(days=28, delay_days=2, today=date(2026, 11, 17))
    assert (end28 - start28).days == 27


def test_gsc_auth_failure_and_api_errors(monkeypatch) -> None:
    def fake_request(method, url, **kwargs):
        resp = MagicMock()
        resp.status_code = 401
        return resp

    monkeypatch.setattr("requests.request", fake_request)
    client = GoogleSearchConsoleClient("https://darkshod.github.io", access_token="bad-token")
    res = client.fetch_search_analytics(days=7)
    assert res["connected"] is False
    assert "401" in res["reason"]


def test_gsc_rate_limit_retry_then_error(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_request(method, url, **kwargs):
        calls["n"] += 1
        resp = MagicMock()
        resp.status_code = 429
        return resp

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    monkeypatch.setattr("requests.request", fake_request)
    client = GoogleSearchConsoleClient("https://darkshod.github.io", access_token="tok")
    res = client.list_sitemaps()
    assert calls["n"] == 3
    assert res["connected"] is False
    assert "429" in res["reason"]


def test_gsc_successful_and_empty_responses(monkeypatch) -> None:
    def fake_request(method, url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if url.endswith("/sites"):
            resp.json.return_value = {"siteEntry": [{"siteUrl": "https://darkshod.github.io/", "permissionLevel": "siteRestrictedUser"}]}
        elif "/sitemaps" in url:
            resp.json.return_value = {"sitemap": [{"path": "https://darkshod.github.io/sitemap.xml", "isPending": False}]}
        else:
            dims = (kwargs.get("json") or {}).get("dimensions", [])
            if dims == ["country"]:
                resp.json.return_value = {"rows": [{"keys": ["usa"], "clicks": 3, "impressions": 45}]}
            else:
                resp.json.return_value = {"rows": []}
        return resp

    monkeypatch.setattr("requests.request", fake_request)
    client = GoogleSearchConsoleClient("https://darkshod.github.io", access_token="valid-tok")
    report = client.fetch_full_report(windows=(7,))
    assert report["connected"] is True
    assert report["sites"]["sites"][0]["siteUrl"] == "https://darkshod.github.io/"
    assert report["windows"]["7d"]["country"]["rows"][0]["keys"] == ["usa"]
    assert report["windows"]["7d"]["query_page"]["rows"] == []


def test_historical_report_storage_and_secret_redaction(tmp_path: Path) -> None:
    non_empty = {
        "connected": True,
        "token": "secret-tok-123",
        "auth_header": "Bearer ya29.secret_value",
        "windows": {"7d": {"country": {"rows": [{"keys": ["usa"], "clicks": 2}]}}},
    }
    res1 = save_historical_report(non_empty, tmp_path)
    assert res1["saved"] is True
    saved_text = (tmp_path / "gsc_latest.json").read_text(encoding="utf-8")
    assert "secret-tok-123" not in saved_text
    assert "ya29.secret_value" not in saved_text
    assert "[REDACTED]" in saved_text

    # Empty connected report must not overwrite existing non-empty history
    empty_report = {"connected": True, "windows": {"7d": {"country": {"rows": []}}}}
    res2 = save_historical_report(empty_report, tmp_path)
    assert res2["saved"] is False
    assert "Preserved" in res2["reason"]

    # Disconnected report must not overwrite history
    res3 = save_historical_report({"connected": False}, tmp_path)
    assert res3["saved"] is False


def test_git_exclusion_of_credentials() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    for target in (".env", "credentials/gsc_service_account.json"):
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "check-ignore", target],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"{target} is not gitignored!"
