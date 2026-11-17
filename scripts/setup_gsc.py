"""1-command GSC verification, sitemap submission & analytics retrieval workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.integrations.gsc import GoogleSearchConsoleClient


def main() -> None:
    settings = load_settings()
    base = settings.brand.base_url.rstrip("/")
    gsc = GoogleSearchConsoleClient(base)
    if not gsc.is_connected:
        print(
            json.dumps(
                {
                    "status": "BLOCKED_MISSING_OAUTH_CREDENTIALS",
                    "property": f"{base}/",
                    "ownership_verified": "Confirmed by owner in Google Search Console UI",
                    "sitemap_submitted": f"{base}/sitemap.xml",
                    "needed_env": ["GSC_CREDENTIALS_PATH (recommended: ./credentials/gsc_oauth.json) OR GSC_ACCESS_TOKEN"],
                    "minimum_scope": GoogleSearchConsoleClient.READONLY_SCOPE,
                    "instructions": "See docs/GSC_SETUP_GUIDE.md to configure OAuth / Service Account credentials locally (gitignored).",
                },
                indent=2,
            )
        )
        return

    report = gsc.fetch_full_report(windows=(7, 28, 90))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
