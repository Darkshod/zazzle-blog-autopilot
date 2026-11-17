"""1-command GSC verification, sitemap submission & analytics retrieval workflow."""

from __future__ import annotations

import json
import os

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
                    "status": "BLOCKED_MISSING_CREDENTIALS",
                    "needed_env": ["GSC_ACCESS_TOKEN", "GSC_VERIFICATION_TOKEN (optional HTML meta)"],
                    "sitemap_to_submit": f"{base}/sitemap.xml",
                    "instructions": "See docs/GSC_SETUP.md to generate an OAuth access token and verify ownership.",
                },
                indent=2,
            )
        )
        return

    sm_res = gsc.submit_sitemap(f"{base}/sitemap.xml")
    data = gsc.fetch_search_analytics(days=28)
    print(json.dumps({"sitemap": sm_res, "analytics": data}, indent=2))


if __name__ == "__main__":
    main()
