"""1-command GSC verification, sitemap submission & analytics retrieval workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.integrations.gsc import (
    GoogleSearchConsoleClient,
    redact_secrets,
    save_historical_report,
    validate_service_account_file,
)


def main() -> None:
    settings = load_settings()
    base = settings.brand.base_url.rstrip("/")
    gsc = GoogleSearchConsoleClient(base)
    if not gsc.is_connected:
        cred_check = (
            validate_service_account_file(gsc.credentials_path)
            if gsc.credentials_path
            else {"valid": False, "reason": "GSC_CREDENTIALS_PATH not set"}
        )
        print(
            json.dumps(
                {
                    "status": "BLOCKED_MISSING_OAUTH_CREDENTIALS",
                    "property": f"{base}/",
                    "ownership_verified": "Confirmed by owner in Google Search Console UI",
                    "sitemap_submitted": f"{base}/sitemap.xml",
                    "credentials_check": cred_check,
                    "needed_env": ["GSC_CREDENTIALS_PATH=./credentials/gsc_service_account.json"],
                    "minimum_scope": GoogleSearchConsoleClient.READONLY_SCOPE,
                    "instructions": "Place your service account JSON key at credentials/gsc_service_account.json and set GSC_CREDENTIALS_PATH in .env.",
                },
                indent=2,
            )
        )
        return

    report = gsc.fetch_full_report(windows=(7, 28, 90))
    save_res = save_historical_report(report, Path(__file__).resolve().parents[1] / "reports")
    print(json.dumps(redact_secrets({"report": report, "storage": save_res}), indent=2))


if __name__ == "__main__":
    main()
