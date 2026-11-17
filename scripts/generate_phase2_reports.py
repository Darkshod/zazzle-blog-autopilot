"""Phase 2 Priorities 3, 5 & 6: Keyword-Article Map, Topical Clusters, Pinterest Queue & Growth Report."""

from __future__ import annotations

import json
import os
from pathlib import Path

from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.db import Database


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = load_settings(root / "config" / "settings.yaml")
    db = Database(root / "data" / "autopilot.db")
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    articles = db.list_articles()
    keywords = db.list_keywords(limit=100)
    pins = db.list_pins()
    metrics = db.get_dashboard_metrics()

    # Priority 3: Keyword-to-Article Mapping & Topical Clusters
    clusters: dict[str, list[str]] = {}
    map_lines = [
        "# Keyword-to-Article Mapping, Topical Clusters & Weekly SEO Report",
        "",
        f"**GSC Connected:** {bool(os.getenv('GSC_CREDENTIALS_PATH'))} (connect `GSC_CREDENTIALS_PATH` for verified impressions, clicks, and average position)",
        "",
        "| Primary Keyword | Article Title | Category | Format | Word Count | QA Score | Live URL |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for a in articles:
        url = f"{settings.brand.base_url}/articles/{a.slug}.html"
        map_lines.append(
            f"| {a.primary_keyword} | {a.title} | {a.category} | {a.content_format} | {a.word_count} | {a.qa_score}/100 | {url} |"
        )
        clusters.setdefault(a.category, []).append(f"[{a.title}]({url})")

    matched_kws = {a.primary_keyword.lower() for a in articles}
    content_gaps = [k.keyword for k in keywords if k.keyword.lower() not in matched_kws]

    map_lines.extend(["", "## Topical Clusters"])
    for cat, links in clusters.items():
        map_lines.append(f"### {cat}")
        map_lines.extend(f"- {lnk}" for lnk in links)

    map_lines.extend(["", "## Content Gaps (Queued Unwritten Keywords)"])
    map_lines.extend(f"- {kw}" for kw in content_gaps[:15])
    (reports_dir / "keyword_article_map.md").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    # Priority 5: Pinterest Publishing Queue (39 concepts, all pending_approval)
    queue = [
        {
            "id": p.id,
            "article_slug": p.article_slug,
            "title": p.title,
            "description": p.description,
            "hashtags": p.hashtags,
            "image_concept": p.image_concept,
            "image_path": p.image_path,
            "destination_url": p.destination_url,
            "status": p.status,
        }
        for p in pins
    ]
    (reports_dir / "pinterest_publishing_queue.json").write_text(
        json.dumps({"total_pins": len(queue), "approval_required": True, "queue": queue}, indent=2),
        encoding="utf-8",
    )

    # Priority 6: Honest Growth Report
    growth_lines = [
        "# GRIMORA11 Weekly Growth & Revenue Report",
        "",
        "| Metric | Value | Source / Verification Note |",
        "|---|---:|---|",
        f"| Published Articles | {metrics['articles_published']} | Verified in SQLite + `dist/articles/` |",
        "| Google Impressions | Unconnected | Connect `GSC_CREDENTIALS_PATH` for verified GSC data |",
        "| Google Clicks | Unconnected | Connect `GSC_CREDENTIALS_PATH` for verified GSC data |",
        "| Average Ranking Position | Unconnected | Connect `GSC_CREDENTIALS_PATH` for verified GSC data |",
        "| Pinterest Impressions | Unconnected | Connect `PINTEREST_ACCESS_TOKEN` or inspect `analytics.pinterest.com` |",
        f"| Outbound Zazzle Clicks | {metrics['product_outbound_clicks']} | Tracked via local `/api/track-click` |",
        f"| Affiliate Clicks | {metrics['affiliate_clicks']} | Tracked via local `/api/track-click` |",
        "| Verified Commissions | Unconnected | Verify in Zazzle Creator Earnings dashboard |",
        "",
        "## Best-Performing Articles",
        *(
            [f"- `{row['article_slug']}`: {row['clicks']} tracked clicks" for row in metrics["top_articles"]]
            or ["- No tracked article clicks yet (only verified analytics events are reported)."]
        ),
    ]
    (reports_dir / "growth_report.md").write_text("\n".join(growth_lines) + "\n", encoding="utf-8")
    print(f"Generated reports: {len(articles)} articles mapped, {len(queue)} pins queued, {len(content_gaps)} content gaps.")


if __name__ == "__main__":
    main()
