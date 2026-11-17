"""Phase 2 Priority 1: Live website crawler & auditor for https://darkshod.github.io/."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://darkshod.github.io"


def audit_live(base_url: str = BASE_URL) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = "ZazzleBlogAutopilot-Auditor/1.0"

    sitemap_url = f"{base_url}/sitemap.xml"
    sm_resp = session.get(sitemap_url, timeout=15)
    issues: list[str] = []
    if sm_resp.status_code != 200:
        return {"healthy": False, "issues": [f"Sitemap HTTP {sm_resp.status_code}"]}

    root = ET.fromstring(sm_resp.text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [loc.text.strip() for loc in root.findall(".//sm:loc", ns) if loc.text]
    article_urls = [u for u in urls if "/articles/" in u]

    checked_assets: dict[str, int] = {}
    titles: dict[str, str] = {}
    article_results: list[dict] = []

    for url in [f"{base_url}/", f"{base_url}/blog.html", *article_urls]:
        r = session.get(url, timeout=15)
        entry = {"url": url, "status": r.status_code, "zazzle_ctas": [], "broken_images": []}
        if r.status_code != 200:
            issues.append(f"{url}: HTTP {r.status_code}")
            article_results.append(entry)
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else ""
        if not title:
            issues.append(f"{url}: missing <title>")
        elif title in titles:
            issues.append(f"{url}: duplicate title with {titles[title]}")
        else:
            titles[title] = url

        canonical = soup.find("link", rel="canonical")
        if not canonical or not canonical.get("href"):
            issues.append(f"{url}: missing canonical tag")

        vp = soup.find("meta", attrs={"name": "viewport"})
        if not vp:
            issues.append(f"{url}: missing mobile viewport meta")

        for sc in soup.find_all("script", type="application/ld+json"):
            try:
                json.loads(sc.string or "{}")
            except json.JSONDecodeError as exc:
                issues.append(f"{url}: invalid JSON-LD ({exc})")

        for img in soup.find_all("img"):
            src = (img.get("src") or "").strip()
            if not src:
                continue
            full_img = urljoin(url, src)
            if full_img not in checked_assets:
                ir = session.head(full_img, timeout=10, allow_redirects=True)
                checked_assets[full_img] = ir.status_code
            if checked_assets[full_img] != 200:
                entry["broken_images"].append(f"{full_img} ({checked_assets[full_img]})")
                issues.append(f"{url}: broken image {full_img} ({checked_assets[full_img]})")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "zazzle.com" in href:
                entry["zazzle_ctas"].append(href)
                if not href.startswith("https://www.zazzle.com/"):
                    issues.append(f"{url}: non-canonical zazzle URL {href}")

        article_results.append(entry)

    return {
        "healthy": len(issues) == 0,
        "sitemap_urls": len(urls),
        "articles_crawled": len(article_urls),
        "images_checked": len(checked_assets),
        "issues": issues,
        "articles": article_results,
    }


if __name__ == "__main__":
    report = audit_live()
    out_path = Path("reports/live_site_audit.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "articles"}, indent=2))
    sys.exit(0 if report["healthy"] else 1)
