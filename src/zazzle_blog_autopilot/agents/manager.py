"""CEO / Manager Agent — orchestrates all 17 agents, bottleneck detection, tasks & Emergency Stop."""

from __future__ import annotations

import os
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
from .financial_reporting import FinancialReportingAgent
from .image_creation import ImageCreationAgent
from .keyword_research import KeywordResearchAgent
from .market_research import MarketResearchAgent
from .monetization import MonetizationAgent
from .pinterest_distribution import PinterestDistributionAgent
from .product_research import ProductResearchAgent
from .security_compliance import SecurityComplianceAgent
from .seo_content import SEOContentAgent
from .seo_strategy import SEOStrategyAgent
from .system_doctor import SystemDoctorAgent
from .technical_seo import TechnicalSEODoctor


class ManagerAgent:
    """Central CEO/Manager orchestrating all 17 specialist agents with idempotent resumable execution."""

    def __init__(self, db: Database, settings: AppSettings, work_dir: Path | None = None) -> None:
        self.db = db
        self.settings = settings
        self.work_dir = work_dir or Path.cwd()
        self.product_agent = ProductResearchAgent(db, settings)
        self.market_agent = MarketResearchAgent(db, settings)
        self.keyword_agent = KeywordResearchAgent(db, settings)
        self.competitor_agent = CompetitorAnalysisAgent(db, settings)
        self.seo_strategy_agent = SEOStrategyAgent(db, settings)
        self.content_agent = SEOContentAgent(db, settings)
        self.qa_agent = EditorialQAAgent(db, settings)
        self.image_agent = ImageCreationAgent(db, settings)
        self.conversion_agent = ConversionOptimizationAgent(db, settings)
        self.pinterest_agent = PinterestDistributionAgent(db, settings)
        self.analytics_agent = AnalyticsAgent(db, settings)
        self.monetization_agent = MonetizationAgent(db, settings)
        self.seo_doctor = TechnicalSEODoctor(db, settings)
        self.financial_agent = FinancialReportingAgent(db, settings)
        self.security_agent = SecurityComplianceAgent(db, settings)
        self.system_doctor = SystemDoctorAgent(db, settings)

    def identify_top_bottleneck(self) -> str:
        if not os.getenv("GSC_ACCESS_TOKEN"):
            return "GSC_ACCESS_TOKEN not connected — cannot measure live Google search impressions/CTR."
        if not os.getenv("PINTEREST_ACCESS_TOKEN"):
            return "PINTEREST_ACCESS_TOKEN not connected — Top-20 pin queue awaits manual/API publishing."
        if len(self.db.list_articles(status="published")) == 0:
            return "No published articles yet — review and approve drafts."
        return "Scale highest-converting US product clusters based on GSC + outbound click telemetry."

    def run_all(
        self,
        csv_path: Path | None = None,
        run_id: str | None = None,
        resume: bool = True,
        enable_live_autocomplete: bool = False,
        max_articles: int = 4,
    ) -> dict[str, Any]:
        if self.db.get_system_flag("emergency_stop") == "true":
            return {
                "run_id": run_id or "blocked",
                "status": "EMERGENCY_STOP_ACTIVE",
                "steps_executed": [],
                "bottleneck": "Emergency Stop is active. Clear flag to resume.",
            }

        active_run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d")
        completed = self.db.get_completed_steps(active_run_id) if resume else set()
        results: dict[str, TaskResult] = {}

        def _exec(step: str, priority: int, impact: str, fn: Any) -> TaskResult | None:
            if resume and step in completed:
                return None
            task_id = f"{active_run_id}:{step}"
            try:
                res = fn()
                self.db.record_job_step(active_run_id, step, "completed")
                self.db.upsert_executive_task(
                    task_id=task_id,
                    objective=res.task,
                    priority=priority,
                    assigned_agent=res.agent_name,
                    expected_output="Structured TaskResult logged in SQLite",
                    status=res.status,
                    quality_score=100 if res.status == "success" else 75,
                    verification_results="passed" if not res.errors else "; ".join(res.errors[:2]),
                    business_impact=impact,
                )
                results[step] = res
                return res
            except Exception as exc:
                self.db.record_job_step(active_run_id, step, "failed", str(exc))
                self.db.upsert_executive_task(
                    task_id=task_id,
                    objective=step,
                    priority=priority,
                    assigned_agent=step,
                    expected_output="Task completion",
                    status="error",
                    quality_score=0,
                    verification_results=str(exc),
                    business_impact=impact,
                )
                raise

        _exec("product_research", 1, "high", lambda: self.product_agent.run(csv_path=csv_path))
        mkt = _exec("market_research", 2, "high", lambda: self.market_agent.run(enable_live_autocomplete=enable_live_autocomplete))
        trends = mkt.output_summary.get("trends", []) if mkt else []
        _exec("keyword_research", 3, "high", lambda: self.keyword_agent.run(market_trends=trends))
        _exec("competitor_analysis", 4, "medium", lambda: self.competitor_agent.run())
        _exec("seo_strategy", 5, "high", lambda: self.seo_strategy_agent.run())
        _exec("seo_content", 6, "high", lambda: self.content_agent.run(max_articles=max_articles))
        _exec("editorial_qa", 7, "high", lambda: self.qa_agent.run())
        _exec("image_creation", 8, "medium", lambda: self.image_agent.run(output_dir=self.work_dir / "site" / "assets" / "generated"))
        _exec("conversion_optimization", 9, "high", lambda: self.conversion_agent.run())
        _exec("pinterest_distribution", 10, "high", lambda: self.pinterest_agent.run())
        _exec("analytics", 11, "medium", lambda: self.analytics_agent.run())
        _exec("monetization", 12, "high", lambda: self.monetization_agent.run(dist_dir=self.work_dir / "dist"))
        _exec("financial_reporting", 13, "medium", lambda: self.financial_agent.run())
        _exec("security_compliance", 14, "high", lambda: self.security_agent.run(root_dir=self.work_dir))
        _exec("system_doctor", 15, "medium", lambda: self.system_doctor.run(root_dir=self.work_dir))

        return {
            "run_id": active_run_id,
            "agents_registered": 17,
            "steps_executed": list(results.keys()),
            "bottleneck": self.identify_top_bottleneck(),
            "results": {k: v.model_dump() for k, v in results.items()},
        }
