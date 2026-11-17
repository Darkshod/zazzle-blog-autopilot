"""Keyword Research Agent — 6-factor weighted scoring and product matching."""

from __future__ import annotations

from typing import Any

from ..models import KeywordOpportunity, Product, TaskResult
from . import BaseAgent

BUYER_MODIFIERS = ("gift", "card", "mug", "shirt", "tee", "poster", "template", "custom", "best", "ideas")
SEASONAL_KEYWORDS = ("christmas", "holiday", "pinkmas", "tartan", "winter", "veterans", "martini")


def score_keyword_opportunity(
    keyword: str,
    product: Product,
    weights: dict[str, float],
    has_autocomplete_signal: bool = False,
) -> KeywordOpportunity:
    kw_lower = keyword.lower().strip()
    words = kw_lower.split()

    # Heuristic 0-100 sub-scores (honestly labeled as estimates; never fake volumes)
    search_demand = 78.0 if has_autocomplete_signal else (72.0 if len(words) <= 5 else 64.0)
    buyer_intent = 88.0 if any(m in kw_lower for m in BUYER_MODIFIERS) else 62.0
    competition_difficulty = 82.0 if len(words) >= 4 else 58.0  # Long-tail = easier to rank
    overlap = len(set(words) & set((product.name + " " + " ".join(product.tags)).lower().split()))
    product_relevance = min(98.0, 65.0 + overlap * 8.0)
    seasonal_opportunity = 90.0 if any(s in kw_lower for s in SEASONAL_KEYWORDS) else 68.0
    ranking_feasibility = 84.0 if len(words) >= 4 else 60.0

    total = (
        search_demand * weights.get("search_demand", 0.25)
        + buyer_intent * weights.get("buyer_intent", 0.25)
        + competition_difficulty * weights.get("competition_difficulty", 0.20)
        + product_relevance * weights.get("product_relevance", 0.15)
        + seasonal_opportunity * weights.get("seasonal_opportunity", 0.10)
        + ranking_feasibility * weights.get("ranking_feasibility", 0.05)
    )

    intent = "transactional" if any(t in kw_lower for t in ("template", "custom", "buy", "card", "mug", "shirt")) else "commercial"
    return KeywordOpportunity(
        keyword=kw_lower,
        market="US",
        search_intent=intent,
        source="google_autocomplete" if has_autocomplete_signal else "free_heuristic_estimate",
        search_demand_score=round(search_demand, 2),
        buyer_intent_score=round(buyer_intent, 2),
        competition_difficulty_score=round(competition_difficulty, 2),
        product_relevance_score=round(product_relevance, 2),
        seasonal_opportunity_score=round(seasonal_opportunity, 2),
        ranking_feasibility_score=round(ranking_feasibility, 2),
        total_score=round(total, 2),
        search_volume_label="unknown (free-tier estimate)",
        keyword_difficulty_label="low-competition long-tail (estimate)" if len(words) >= 4 else "moderate (estimate)",
        matched_product_id=product.id,
        status="new",
    )


class KeywordResearchAgent(BaseAgent):
    name = "keyword_research"

    def execute(self, market_trends: list[dict[str, Any]] | None = None, **kwargs: Any) -> TaskResult:
        products = self.db.list_products()
        weights = self.settings.scoring_weights
        saved = 0

        trend_by_pid = {t["product_id"]: t for t in (market_trends or []) if "product_id" in t}

        for product in products:
            t_info = trend_by_pid.get(product.id, {})
            auto_terms = t_info.get("autocomplete_suggestions", [])
            candidates = list(dict.fromkeys(product.search_terms + auto_terms))
            if not candidates:
                candidates = [f"{product.name.lower()} gift idea"]

            for term in candidates[:4]:
                opp = score_keyword_opportunity(
                    keyword=term,
                    product=product,
                    weights=weights,
                    has_autocomplete_signal=term in auto_terms,
                )
                self.db.upsert_keyword(opp)
                saved += 1

        top_kws = self.db.list_keywords(limit=10)
        return TaskResult(
            agent_name=self.name,
            task="score_and_match_keywords",
            status="success",
            input_summary={"products_count": len(products)},
            output_summary={
                "keywords_saved": saved,
                "top_keywords": [{"keyword": k.keyword, "score": k.total_score} for k in top_kws[:5]],
            },
            recommendations=["Target keywords with >=4 words first for faster US long-tail rankings."],
        )
