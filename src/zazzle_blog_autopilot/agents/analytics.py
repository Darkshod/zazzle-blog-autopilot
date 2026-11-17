"""Analytics Agent — aggregates traffic, clicks, and content refresh recommendations."""

from __future__ import annotations

import os
from typing import Any

from ..models import TaskResult
from . import BaseAgent


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    def execute(self, **kwargs: Any) -> TaskResult:
        metrics = self.db.get_dashboard_metrics()
        ga_connected = bool(os.getenv("GA4_MEASUREMENT_ID"))
        gsc_connected = bool(os.getenv("GSC_CREDENTIALS_PATH"))

        articles = self.db.list_articles()
        refresh_candidates = [
            a.slug for a in articles if a.status == "published" and a.qa_score < 90
        ]

        return TaskResult(
            agent_name=self.name,
            task="generate_performance_report",
            status="success",
            input_summary={"ga4_connected": ga_connected, "gsc_connected": gsc_connected},
            output_summary={
                "metrics": metrics,
                "content_refresh_candidates": refresh_candidates,
            },
            recommendations=[
                "Connect GA4_MEASUREMENT_ID and GSC_CREDENTIALS_PATH to replace placeholder organic metrics with verified data."
            ],
        )
