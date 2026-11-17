"""Financial Reporting Agent — separates revenue streams and expenses; never fabricates income."""

from __future__ import annotations

from typing import Any

from ..models import TaskResult
from . import BaseAgent


class FinancialReportingAgent(BaseAgent):
    name = "financial_reporting"

    def execute(self, **kwargs: Any) -> TaskResult:
        summary = self.db.get_financial_summary()
        return TaskResult(
            agent_name=self.name,
            task="compile_financial_ledger",
            status="success",
            input_summary={"ledger_entries": summary["entry_count"]},
            output_summary=summary,
            recommendations=[
                "Only record verified Zazzle sales/commissions from official earnings statements.",
                "Unconnected revenue streams remain labeled NOT VERIFIED.",
            ],
        )
