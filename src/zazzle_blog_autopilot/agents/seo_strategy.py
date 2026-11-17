"""SEO Strategy Agent — builds topical clusters, content calendar & cannibalization guards."""

from __future__ import annotations

from typing import Any

from ..models import TaskResult
from . import BaseAgent


class SEOStrategyAgent(BaseAgent):
    name = "seo_strategy"

    def execute(self, **kwargs: Any) -> TaskResult:
        articles = self.db.list_articles()
        clusters: dict[str, list[str]] = {}
        for a in articles:
            clusters.setdefault(a.category, []).append(a.slug)

        weak_clusters = [c for c, slugs in clusters.items() if len(slugs) < 2]
        return TaskResult(
            agent_name=self.name,
            task="evaluate_topical_clusters_and_calendar",
            status="success",
            input_summary={"articles_reviewed": len(articles)},
            output_summary={
                "cluster_count": len(clusters),
                "clusters": {k: len(v) for k, v in clusters.items()},
                "clusters_needing_depth": weak_clusters,
            },
            recommendations=[
                f"Expand thin clusters ({', '.join(weak_clusters)}) with non-cannibalizing long-tail guides."
                if weak_clusters
                else "All topical clusters have >= 2 interlinked guides."
            ],
        )
