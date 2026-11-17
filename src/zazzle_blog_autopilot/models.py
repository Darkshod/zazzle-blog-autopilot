"""Structured Pydantic domain models for all agents and pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Product(BaseModel):
    id: int | None = None
    name: str
    category: str
    url: str
    description: str
    tags: list[str] = Field(default_factory=list)
    target_customer: str
    design_style: str
    occasion_season: str
    price_usd: float | None = None  # Only populated when publicly verified
    selling_points: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    image_url: str | None = None
    source: str = "csv"
    created_at: str = Field(default_factory=utc_now_iso)


class KeywordOpportunity(BaseModel):
    id: int | None = None
    keyword: str
    market: str = "US"
    search_intent: Literal["commercial", "transactional", "informational", "navigational"] = "commercial"
    source: str = "autocomplete_estimate"
    search_demand_score: float = 0.0
    buyer_intent_score: float = 0.0
    competition_difficulty_score: float = 0.0
    product_relevance_score: float = 0.0
    seasonal_opportunity_score: float = 0.0
    ranking_feasibility_score: float = 0.0
    total_score: float = 0.0
    search_volume_label: str = "unknown (free-tier estimate)"
    keyword_difficulty_label: str = "unknown (free-tier estimate)"
    matched_product_id: int | None = None
    status: Literal["new", "queued", "drafted"] = "new"
    created_at: str = Field(default_factory=utc_now_iso)


class Article(BaseModel):
    id: int | None = None
    slug: str
    title: str
    meta_description: str
    content_format: str
    search_intent: str
    primary_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    semantic_variations: list[str] = Field(default_factory=list)
    category: str
    tags: list[str] = Field(default_factory=list)
    markdown_body: str
    word_count: int = 0
    matched_product_ids: list[int] = Field(default_factory=list)
    image_path: str | None = None
    image_alt: str = ""
    internal_links: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    affiliate_disclosure_included: bool = True
    qa_score: int = 0
    qa_passed: bool = False
    qa_notes: list[str] = Field(default_factory=list)
    status: Literal["draft", "awaiting_approval", "approved", "published", "rejected"] = "draft"
    created_at: str = Field(default_factory=utc_now_iso)
    published_at: str | None = None


class PinterestPin(BaseModel):
    id: int | None = None
    article_slug: str
    title: str
    description: str
    hashtags: list[str] = Field(default_factory=list)
    image_concept: str
    image_path: str | None = None
    destination_url: str
    status: Literal["pending_approval", "approved", "published"] = "pending_approval"
    created_at: str = Field(default_factory=utc_now_iso)


class TaskResult(BaseModel):
    agent_name: str
    task: str
    status: Literal["success", "warning", "error", "skipped"] = "success"
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=utc_now_iso)
