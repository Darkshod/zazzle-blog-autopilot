"""Cycle 3 Step 1: Full live verification of repos, all 64 sitemap URLs, all 13 articles, and all 20 Pinterest pins."""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    base = "https://darkshod.github.io"
    session = requests.Session()
    session.headers["User-Agent"] = "DARKSHOD-Cycle3-Verifier/1.0"

    main_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True).strip()
    site_repo = Path(r"C:\Users\pc\.gemini\antigravity\brain\cdb56a36-10a7-44da-aa37-8e26447c7146\scratch\darkshod.github.io")
    site_hash = (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=site_repo, text=True).strip()
        if site_repo.exists()
        else "unknown"
    )

    sm = session.get(f"{base}/sitemap.xml", timeout=15)
    xml_root = ET.fromstring(sm.text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = [el.text.strip() for el in xml_root.findall(".//sm:loc", ns) if el.text]

    sitemap_results = []
    for u in sitemap_urls:
        try:
            code = session.head(u, timeout=10, allow_redirects=True).status_code
        except Exception:
            code = 0
        sitemap_results.append({"url": u, "http_status": code})

    article_urls = [u for u in sitemap_urls if "/articles/" in u]
    article_checks = []
    for aurl in article_urls:
        r = session.get(aurl, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tracker_count = r.text.count("zazzle_outbound_click")
        ga_present = "googletagmanager.com/gtag/js" in r.text
        gsc_meta = bool(soup.find("meta", attrs={"name": "google-site-verification"}))
        zazzle_links = [a["href"] for a in soup.find_all("a", href=True) if "zazzle.com" in a["href"]]
        article_checks.append(
            {
                "url": aurl,
                "http_status": r.status_code,
                "outbound_tracker_count": tracker_count,
                "duplicate_tracker": tracker_count > 1,
                "ga4_tag_injected": ga_present,
                "gsc_meta_injected": gsc_meta,
                "zazzle_cta_count": len(zazzle_links),
            }
        )

    # Pin-by-pin verification for all 20 pins in pinterest_top20_queue.json
    q = json.loads((root / "reports" / "pinterest_top20_queue.json").read_text(encoding="utf-8"))
    pin_checks = []
    for idx, p in enumerate(q.get("pins", []), start=1):
        dest = p["destination_url"]
        try:
            st = session.head(dest, timeout=10, allow_redirects=True).status_code
        except Exception:
            st = 0
        pin_checks.append(
            {
                "pin_index": idx,
                "article_slug": p["article_slug"],
                "title": p["title"],
                "destination_url": dest,
                "http_status": st,
                "status": p["status"],
            }
        )

    out = {
        "repo_commits": {"zazzle-blog-autopilot": main_hash, "darkshod.github.io": site_hash},
        "sitemap_total": len(sitemap_urls),
        "sitemap_all_200": all(x["http_status"] == 200 for x in sitemap_results),
        "articles_total": len(article_checks),
        "articles_all_200": all(x["http_status"] == 200 for x in article_checks),
        "duplicate_trackers_found": any(x["duplicate_tracker"] for x in article_checks),
        "pins_total": len(pin_checks),
        "unique_pin_destinations": len({x["destination_url"] for x in pin_checks}),
        "pins_all_200": all(x["http_status"] == 200 for x in pin_checks),
        "articles": article_checks,
        "pins": pin_checks,
    }
    (root / "reports" / "cycle3_live_verification.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("articles", "pins")}, indent=2))


if __name__ == "__main__":
    main()
