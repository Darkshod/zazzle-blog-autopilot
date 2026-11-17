"""Market Research Agent — US-first seasonal & buyer-intent discovery using free sources."""

from __future__ import annotations

from typing import Any

import requests

from ..models import TaskResult
from . import BaseAgent


def fetch_google_autocomplete(query: str, country: str = "US", timeout: float = 3.0) -> list[str]:
    """Query public Google Suggest endpoint (free, no API key). Returns [] on network failure."""
    try:
        resp = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "hl": "en", "gl": country.lower(), "q": query},
            timeout=timeout,
        )
        if resp.status_code == 200:
            payload = resp.json()
            if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list):
                return [str(s).strip() for s in payload[1][:8] if str(s).strip()]
    except Exception:
        return []
    return []


class MarketResearchAgent(BaseAgent):
    name = "market_research"

    def execute(self, enable_live_autocomplete: bool = False, **kwargs: Any) -> TaskResult:
        products = self.db.list_products()
        categories = sorted({p.category for p in products})
        occasions = sorted({p.occasion_season for p in products})

        trends: list[dict[str, Any]] = []
        for product in products:
            seed_terms = product.search_terms or [product.name.lower()]
            suggestions: list[str] = []
            if enable_live_autocomplete:
                suggestions = fetch_google_autocomplete(seed_terms[0], country=self.settings.brand.primary_market)
            trends.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "occasion": product.occasion_season,
                    "seed_terms": seed_terms,
                    "autocomplete_suggestions": suggestions,
                    "market": self.settings.brand.primary_market,
                }
            )

        return TaskResult(
            agent_name=self.name,
            task="research_us_market_opportunities",
            status="success",
            input_summary={"market": self.settings.brand.primary_market, "live_autocomplete": enable_live_autocomplete},
            output_summary={
                "categories_covered": categories,
                "occasions_covered": occasions,
                "opportunities_discovered": len(trends),
                "trends": trends,
            },
            recommendations=[
                "Prioritize Q4 holiday, hobbyist mugs, and customizable B2B stationery for US buyers.",
                "Metrics from free tools are qualitative signals; never fabricate exact monthly search volumes.",
            ],
        )
