"""Competitor Analysis Agent — identifies structural content gaps without copying."""

from __future__ import annotations

from typing import Any

from ..models import TaskResult
from . import BaseAgent

CONTENT_FORMATS = [
    "Best gift ideas for specific audiences",
    "Personalized gift guides",
    "Product comparison articles",
    "Occasion-based shopping guides",
    "Design and customization guides",
    "Product inspiration articles",
    "Holiday shopping guides",
    "Niche-specific buying guides",
]


class CompetitorAnalysisAgent(BaseAgent):
    name = "competitor_analysis"

    def execute(self, **kwargs: Any) -> TaskResult:
        keywords = self.db.list_keywords(limit=25)
        gaps = []
        for idx, kw in enumerate(keywords):
            fmt = CONTENT_FORMATS[idx % len(CONTENT_FORMATS)]
            gaps.append(
                {
                    "keyword": kw.keyword,
                    "recommended_format": fmt,
                    "differentiator": "Original lifestyle photography + direct Zazzle customization walkthrough",
                }
            )
        return TaskResult(
            agent_name=self.name,
            task="analyze_topic_gaps",
            status="success",
            input_summary={"keywords_reviewed": len(keywords)},
            output_summary={"content_blueprints": len(gaps), "formats_available": CONTENT_FORMATS},
            recommendations=[
                "Never copy competitor copy; differentiate with customization tips and honest buyer fit notes."
            ],
        )
