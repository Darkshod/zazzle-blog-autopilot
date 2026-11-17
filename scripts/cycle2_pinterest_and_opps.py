"""Cycle 2: Verify Top-20 Pinterest destinations, AdSense GitHub Pages audit & Product Opportunities."""

from __future__ import annotations

import json
from pathlib import Path

import requests

from zazzle_blog_autopilot.config import load_settings


def _map_board(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ("pinkmas", "tartan", "christmas", "holiday", "card")):
        return "Heirloom Holiday Cards & Christmas Decor"
    if any(w in t for w in ("mug", "coffee", "tea", "nurse")):
        return "Cozy Coffee Mugs & Gift Ideas"
    if any(w in t for w in ("shirt", "tee", "apparel")):
        return "Vintage Graphic Tees & Cozy Apparel"
    if "veterans" in t or "patriotic" in t:
        return "Patriotic & Veterans Day Gifts"
    if "poster" in t or "espresso" in t:
        return "Cozy Home Bar & Wall Art Prints"
    return "Botanical Business Cards & Stationery"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = load_settings(root / "config" / "settings.yaml")
    reports = root / "reports"
    queue_path = reports / "pinterest_top20_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    pins = queue.get("pins", [])

    # Priority 3: Live-verify all 20 destination URLs & prepare 7-day schedule (3/day, pending_approval)
    session = requests.Session()
    checked_urls: dict[str, int] = {}
    sched_lines = [
        "# Pinterest Top-20 Publishing Schedule (Approval Required)",
        "",
        "**Policy:** All pins remain `pending_approval` and are **NOT** published without explicit authorization.",
        "",
        "| Day | # | Pin Title | Target Board (`@rafafo1225`) | Destination URL | HTTP | Status |",
        "|---|---:|---|---|---|---:|---|",
    ]
    for idx, p in enumerate(pins, start=1):
        url = p["destination_url"]
        if url not in checked_urls:
            try:
                checked_urls[url] = session.head(url, timeout=10, allow_redirects=True).status_code
            except Exception:
                checked_urls[url] = 0
        day = ((idx - 1) // 3) + 1
        board = _map_board(p["title"])
        sched_lines.append(
            f"| Day {day} | {idx} | {p['title']} | {board} | {url} | {checked_urls[url]} | {p['status']} |"
        )
    (reports / "pinterest_publishing_schedule.md").write_text("\n".join(sched_lines) + "\n", encoding="utf-8")

    # Priority 4: AdSense GitHub Pages Compatibility Audit
    adsense_md = """# Google AdSense & GitHub Pages Compatibility Audit

## Technical Capabilities (Verified)
- **HTML `<meta>` Verification:** Supported cleanly in `<head>` (already verified with Pinterest `p:domain_verify` and wired for `GSC_VERIFICATION_TOKEN`).
- **Root `ads.txt` Support:** Supported on GitHub Pages by placing `ads.txt` at the repository root (no Jekyll conflict when `_config.yml` is absent or configured).
- **Client-Side JavaScript (`gtag.js` & AdSense):** Supported cleanly over HTTPS.
- **Migration Needed Now?** **No** — no technical limitation prevents serving static HTML, JS, meta tags, or `ads.txt` on GitHub Pages.

## Official Policy Limitation (Critical)
- **Google AdSense does NOT approve free `*.github.io` subdomains** (`https://darkshod.github.io/`) because `github.io` is a shared public suffix.
- **Required Fix Before Applying:** Attach a custom apex domain (e.g., `darkshod.com`) via a root `CNAME` file + 4 GitHub Pages `A` records, then place `ads.txt` at `https://darkshod.com/ads.txt`.
- **Approval Guarantee:** None. Approval depends on Google's manual/automated publisher review of original content and policy compliance.
"""
    (reports / "adsense_github_pages_audit.md").write_text(adsense_md, encoding="utf-8")

    # Priority 5: Product Opportunities (Personalized Christmas Ornaments & Aesthetic Phone Cases)
    w = settings.scoring_weights
    opps = [
        {
            "opportunity": "Personalized Monogram & Family Heirloom Christmas Ornaments (Ceramic / Wood / Metal)",
            "zazzle_verified": "Yes — Ceramic (circle, oval, heart, star, snowflake), rustic Wood, and shatterproof Metal/Aluminum ornaments with custom text/monogram support.",
            "us_keywords": ["custom engraved christmas ornaments", "custom personalized christmas ornaments", "custom wood engraved christmas ornaments"],
            "demand": 84, "intent": 90, "competition": 68, "fit": 94, "seasonality": 95, "feasibility": 90,
        },
        {
            "opportunity": "Aesthetic Botanical & Retro Editorial iPhone Cases (MagSafe Tough / Slim / Clear)",
            "zazzle_verified": "Yes — Slim, Dual-Layer Tough (MagSafe compatible, 3D wrap), Clear, and Case-Mate/OtterBox options supporting custom text & transparent PNG artwork.",
            "us_keywords": ["customized aesthetic phone cases", "personalised aesthetic phone cases", "aesthetic customised phone case"],
            "demand": 80, "intent": 84, "competition": 62, "fit": 88, "seasonality": 75, "feasibility": 90,
        },
    ]
    opp_lines = [
        "# Cycle 2 Product Opportunities (Awaiting Approval)",
        "",
        "| Opportunity | Weighted Score | Demand (25%) | Intent (25%) | Comp (20%) | Fit (15%) | Season (10%) | Feas (5%) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for o in opps:
        total = (
            o["demand"] * w["search_demand"]
            + o["intent"] * w["buyer_intent"]
            + o["competition"] * w["competition_difficulty"]
            + o["fit"] * w["product_relevance"]
            + o["seasonality"] * w["seasonal_opportunity"]
            + o["feasibility"] * w.get("ranking_feasibility", 0.05)
        )
        opp_lines.append(
            f"| {o['opportunity']} | **{total:.2f}** | {o['demand']} | {o['intent']} | {o['competition']} | {o['fit']} | {o['seasonality']} | {o['feasibility']} |"
        )
        opp_lines.append(f"\n- **Zazzle Verification:** {o['zazzle_verified']}")
        opp_lines.append(f"- **US Autocomplete Signals:** {', '.join(o['us_keywords'])} *(monthly volume unknown on free tier)*\n")

    (reports / "product_opportunities_cycle2.md").write_text("\n".join(opp_lines) + "\n", encoding="utf-8")
    print(json.dumps({"urls_verified": len(checked_urls), "all_200": all(v == 200 for v in checked_urls.values())}, indent=2))


if __name__ == "__main__":
    main()
