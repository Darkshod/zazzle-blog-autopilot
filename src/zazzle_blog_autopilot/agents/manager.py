"""Manager Agent — orchestrates all 11 specialized agents with resume & retry support."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import AppSettings
from ..db import Database
from ..models import TaskResult
from .analytics import AnalyticsAgent
from .competitor_analysis import CompetitorAnalysisAgent
from .conversion import ConversionOptimizationAgent
from .editorial_qa import EditorialQAAgent
from .image_creation import ImageCreationAgent
from .keyword_research import KeywordResearchAgent
from .market_research import MarketResearchAgent
from .pinterest_distribution import PinterestDistributionAgent
from .product_research import ProductResearchAgent
from .seo_content import SEOContentAgent
from .technical_seo import TechnicalSEODoctor


class ManagerAgent:
    """Coordinates the full autonomous blogging pipeline with idempotent resumable steps."""

    def __init__(self, db: Database, settings: AppSettings, work_dir: Path | None = None) -> None:
        self.db = db
        self.settings = settings
        self.work_dir = work_dir or Path.cwd()
        self.product_agent = ProductResearchAgent(db, settings)
        self.market_agent = MarketResearchAgent(db, settings)
        self.keyword_agent = KeywordResearchAgent(db, settings)
        self.competitor_agent = CompetitorAnalysisAgent(db, settings)
        self.content_agent = SEOContentAgent(db, settings)
        self.qa_agent = EditorialQAAgent(db, settings)
        self.image_agent = ImageCreationAgent(db, settings)
        self.conversion_agent = ConversionOptimizationAgent(db, settings)
        self.pinterest_agent = PinterestDistributionAgent(db, settings)
        self.analytics_agent = AnalyticsAgent(db, settings)
        self.seo_doctor = TechnicalSEODoctor(db, settings)

    def run_all(
        self,
        csv_path: Path | None = None,
        run_id: str | None = None,
        resume: bool = True,
        enable_live_autocomplete: bool = False,
        max_articles: int = 4,
    ) -> dict[str, Any]:
        active_run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d")
        completed = self.db.get_completed_steps(active_run_id) if resume else set()
        results: dict[str, TaskResult] = {}

        def _exec(step: str, fn: Any) -> TaskResult | None:
            if resume and step in completed:
                return None
            try:
                res = fn()
                self.db.record_job_step(active_run_id, step, "completed")
                results[step] = res
                return res
            except Exception as exc:
                self.db.record_job_step(active_run_id, step, "failed", str(exc))
                raise

        _exec("product_research", lambda: self.product_agent.run(csv_path=csv_path))
        mkt = _exec("market_research", lambda: self.market_agent.run(enable_live_autocomplete=enable_live_autocomplete))
        trends = mkt.output_summary.get("trends", []) if mkt else []
        _exec("keyword_research", lambda: self.keyword_agent.run(market_trends=trends))
        _exec("competitor_analysis", lambda: self.competitor_agent.run())
        _exec("seo_content", lambda: self.content_agent.run(max_articles=max_articles))
        _exec("editorial_qa", lambda: self.qa_agent.run())
        _exec("image_creation", lambda: self.image_agent.run(output_dir=self.work_dir / "site" / "assets" / "generated"))
        _exec("conversion_optimization", lambda: self.conversion_agent.run())
        _exec("pinterest_distribution", lambda: self.pinterest_agent.run())
        _exec("analytics", lambda: self.analytics_agent.run())

        return {
            "run_id": active_run_id,
            "steps_executed": list(results.keys()),
            "results": {k: v.model_dump() for k, v in results.items()},
        }
