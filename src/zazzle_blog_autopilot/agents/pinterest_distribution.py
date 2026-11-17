"""Pinterest Distribution Agent — generates 3 pin concepts per article with approval gating."""

from __future__ import annotations

import os
from typing import Any

from ..models import PinterestPin, TaskResult
from . import BaseAgent


class PinterestDistributionAgent(BaseAgent):
    name = "pinterest_distribution"

    def execute(self, **kwargs: Any) -> TaskResult:
        articles = self.db.list_articles()
        base_url = self.settings.brand.base_url.rstrip("/")
        created = 0

        for article in articles:
            dest_url = f"{base_url}/articles/{article.slug}.html"
            concepts = [
                (
                    f"{article.primary_keyword.title()} | 2026 Gift Guide",
                    f"Discover curated {article.primary_keyword} ideas, customization tips, and gift pairings for US shoppers. Read the full guide.",
                    ["#giftguide", "#zazzlefinds", f"#{article.category.lower().replace(' ', '')}"],
                    f"2:3 editorial flatlay hero featuring {article.category} and serif title header",
                ),
                (
                    f"How to Customize {article.category} for {article.primary_keyword.title()}",
                    f"Step-by-step guide to personalizing {article.primary_keyword} designs cleanly before ordering on Zazzle.",
                    ["#customgifts", "#personalizedgifts", "#shopusa"],
                    f"2:3 clean step-by-step visual checklist with {article.primary_keyword} inspiration",
                ),
                (
                    f"Best {article.category} Ideas for Gift Buyers",
                    f"Compare top {article.category.lower()} styles and find the best fit for {article.primary_keyword}.",
                    ["#giftideas", "#thoughtfulgifts", "#holidayshopping"],
                    f"2:3 three-panel comparison collage linking to {article.title}",
                ),
            ]
            for title, desc, hashtags, img_concept in concepts:
                pin = PinterestPin(
                    article_slug=article.slug,
                    title=title[:100],
                    description=desc[:490],
                    hashtags=hashtags,
                    image_concept=img_concept,
                    image_path=f"/assets/generated/{article.slug}-pinterest-pin.jpg",
                    destination_url=dest_url,
                    status="pending_approval",
                )
                self.db.upsert_pin(pin)
                created += 1

        api_configured = bool(os.getenv("PINTEREST_ACCESS_TOKEN"))
        return TaskResult(
            agent_name=self.name,
            task="generate_pinterest_pin_concepts",
            status="success",
            input_summary={"articles": len(articles)},
            output_summary={"pins_prepared": created, "pinterest_api_configured": api_configured},
            recommendations=[
                "Pins remain in 'pending_approval' until human review or authorized Pinterest API v5 testing."
            ],
        )
