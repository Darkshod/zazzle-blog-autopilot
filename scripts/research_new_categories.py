"""Research new US Zazzle categories (invitations, stickers, phone cases, personalized gifts) via Google Suggest."""

from __future__ import annotations

import json
from pathlib import Path

from zazzle_blog_autopilot.agents.market_research import fetch_google_autocomplete


def main() -> None:
    seeds = [
        ("Invitations", "custom wedding invitation zazzle"),
        ("Invitations", "bridal shower invitation template"),
        ("Stickers", "custom waterproof laptop sticker"),
        ("Phone Cases", "personalized aesthetic iphone case"),
        ("Personalized Gifts", "custom monogrammed christmas ornament"),
        ("Stationery", "botanical thank you card template"),
    ]
    lines = [
        "# US Market Opportunity Research (Google Suggest Signals)",
        "",
        "> **Data Classification:** Verified live US Google Suggest autocomplete queries (`client=firefox&gl=us`). Monthly search volumes remain **UNKNOWN** (free tier).",
        "",
        "| Category | Seed Query | Verified US Autocomplete Suggestions |",
        "|---|---|---|",
    ]
    raw_out = []
    for cat, seed in seeds:
        suggs = fetch_google_autocomplete(seed, country="US")
        lines.append(f"| {cat} | `{seed}` | {', '.join(suggs[:5]) if suggs else 'offline / none'} |")
        raw_out.append({"category": cat, "seed": seed, "suggestions": suggs})

    out_md = Path("reports/us_market_opportunities.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(raw_out, indent=2))


if __name__ == "__main__":
    main()
