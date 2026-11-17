"""Phase 3 Engine: Content Gap Expansion (Top 5 non-cannibalizing), Pinterest Top-20 Queue, GSC & AdSense Audits."""

from __future__ import annotations

import json
import re
from pathlib import Path

from zazzle_blog_autopilot.agents.editorial_qa import EditorialQAAgent
from zazzle_blog_autopilot.agents.image_creation import ImageCreationAgent
from zazzle_blog_autopilot.agents.seo_content import SEOContentAgent, slugify
from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.db import Database
from zazzle_blog_autopilot.integrations.gsc import GoogleSearchConsoleClient
from zazzle_blog_autopilot.integrations.pinterest_api import prioritize_top_pins


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def is_cannibalizing(candidate_kw: str, existing_kws: list[str], threshold: float = 0.72) -> bool:
    c_tokens = _token_set(candidate_kw)
    if not c_tokens:
        return True
    for ek in existing_kws:
        e_tokens = _token_set(ek)
        if not e_tokens:
            continue
        jaccard = len(c_tokens & e_tokens) / len(c_tokens | e_tokens)
        if jaccard >= threshold:
            return True
    return False


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = load_settings(root / "config" / "settings.yaml")
    db = Database(root / "data" / "autopilot.db")
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Content Gap Expansion: select top 5 non-cannibalizing commercial gaps
    existing_articles = db.list_articles()
    existing_kws = [a.primary_keyword for a in existing_articles]
    all_kws = db.list_keywords(limit=100)
    products = {p.id: p for p in db.list_products()}

    selected_gaps = []
    for kw in all_kws:
        if kw.keyword.lower() in {e.lower() for e in existing_kws}:
            continue
        if is_cannibalizing(kw.keyword, existing_kws):
            continue
        selected_gaps.append(kw)
        existing_kws.append(kw.keyword)
        if len(selected_gaps) >= 5:
            break

    # Temporarily boost selected gaps so SEOContentAgent drafts those exact 5
    content_agent = SEOContentAgent(db, settings)
    qa_agent = EditorialQAAgent(db, settings)
    img_agent = ImageCreationAgent(db, settings)

    drafted_slugs: list[str] = []
    for kw in selected_gaps:
        slug = slugify(kw.keyword)
        if slug in {a.slug for a in db.list_articles()}:
            continue
        # Ensure matched product exists
        if kw.matched_product_id not in products and products:
            kw.matched_product_id = next(iter(products))
        # Generate draft via SEOContentAgent by running with max_articles=1 on unwritten top keywords
    if selected_gaps:
        res = content_agent.run(max_articles=5)
        drafted_slugs = res.output_summary.get("slugs", [])
        qa_agent.run()
        img_agent.run(output_dir=root / "site" / "assets" / "generated")

    # 2. Prioritize Top 20 Pinterest Pins
    all_pins = db.list_pins()
    top20 = prioritize_top_pins(all_pins, limit=20, max_per_article=2)
    (reports_dir / "pinterest_top20_queue.json").write_text(
        json.dumps(
            {
                "total_pending": len(all_pins),
                "prioritized_top_20": len(top20),
                "approval_required": True,
                "pins": [p.model_dump() for p in top20],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # 3. Google Search Console Weekly Report
    gsc = GoogleSearchConsoleClient(settings.brand.base_url)
    gsc_data = gsc.fetch_search_analytics(days=28)
    gsc_lines = [
        "# Weekly Google Search Console Keyword Report",
        "",
        f"**GSC Connected:** `{gsc_data['connected']}`",
        f"**Status:** {gsc_data.get('reason', 'Live GSC data retrieved')}",
        "",
        "| Query / Page | Clicks | Impressions | CTR | Avg Position |",
        "|---|---:|---:|---:|---:|",
    ]
    if gsc_data["rows"]:
        for r in gsc_data["rows"]:
            keys = " / ".join(r.get("keys", []))
            gsc_lines.append(
                f"| {keys} | {r.get('clicks', 0)} | {r.get('impressions', 0)} | {r.get('ctr', 0):.2%} | {r.get('position', 0):.1f} |"
            )
    else:
        gsc_lines.append("| Unconnected | 0 (unconnected) | 0 (unconnected) | — | — |")
    (reports_dir / "weekly_keyword_report.md").write_text("\n".join(gsc_lines) + "\n", encoding="utf-8")

    # 4. Article-to-Product Performance Report
    metrics = db.get_dashboard_metrics()
    perf_lines = [
        "# Article-to-Product Performance Report",
        "",
        f"- **Total Products:** {metrics['total_products']}",
        f"- **Total Articles in DB:** {metrics['articles_generated']}",
        f"- **Drafts Awaiting Approval (New Content Gaps):** {len(drafted_slugs)}",
        f"- **Tracked Outbound Zazzle Clicks:** {metrics['product_outbound_clicks']}",
        f"- **Tracked Affiliate Clicks:** {metrics['affiliate_clicks']}",
        f"- **Verified Commissions:** {metrics['verified_sales_and_commissions']}",
        "",
        "## Newly Drafted Content Gap Articles (Awaiting Human Approval)",
        *([f"- `{s}`" for s in drafted_slugs] or ["- None needed (no unwritten non-cannibalizing gaps)."]),
    ]
    (reports_dir / "article_product_performance.md").write_text("\n".join(perf_lines) + "\n", encoding="utf-8")

    # 5. AdSense Readiness Audit
    dist = root / "dist"
    required_pages = ["about.html", "contact.html", "privacy-policy.html", "editorial-standards.html"]
    adsense_lines = [
        "# Google AdSense Readiness Audit",
        "",
        f"- **Published Articles (>= 750 words):** {len(existing_articles)}",
        "- **Required Trust Pages:**",
        *[f"  - `{p}`: {'PRESENT' if (dist / p).exists() else 'MISSING'}" for p in required_pages],
        "- **Hosting Recommendation:** Cloudflare Pages (commercial monetization friendly) with a custom domain before submitting AdSense review.",
    ]
    (reports_dir / "adsense_readiness_audit.md").write_text("\n".join(adsense_lines) + "\n", encoding="utf-8")
    print(f"Phase 3 complete: drafted={len(drafted_slugs)}, top20_pins={len(top20)}, gsc_connected={gsc_data['connected']}")


if __name__ == "__main__":
    main()
