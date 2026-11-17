"""Monetization Agent — verifies program eligibility, Morocco payout constraints & AdSense readiness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..models import TaskResult
from . import BaseAgent


class MonetizationAgent(BaseAgent):
    name = "monetization"

    def execute(self, dist_dir: Path | None = None, **kwargs: Any) -> TaskResult:
        target_dist = dist_dir or (Path.cwd() / "dist")
        trust_pages = ["about.html", "contact.html", "privacy-policy.html", "editorial-standards.html"]
        missing_pages = [p for p in trust_pages if not (target_dist / p).exists()]
        published = len(self.db.list_articles(status="published")) + len(self.db.list_articles(status="approved"))

        return TaskResult(
            agent_name=self.name,
            task="audit_monetization_and_payout_eligibility",
            status="success" if not missing_pages else "warning",
            input_summary={"country": self.settings.monetization.applicant_country},
            output_summary={
                "zazzle_affiliate_approved": self.settings.monetization.zazzle_affiliate_approved,
                "zazzle_supported_payouts_for_MA": ["PayPal ($50 min)", "Check by Mail ($100 min - discouraged)"],
                "unsupported_payouts": ["Payoneer", "Wise", "SWIFT/ACH"],
                "adsense_trust_pages_missing": missing_pages,
                "published_or_approved_articles": published,
                "ga4_connected": bool(os.getenv("GA4_MEASUREMENT_ID")),
            },
            recommendations=[
                "Verify Moroccan PayPal USD withdrawal capability before relying on affiliate payouts.",
                "Migrate dist/ to Cloudflare Pages (free tier) before submitting Google AdSense application.",
            ],
        )
