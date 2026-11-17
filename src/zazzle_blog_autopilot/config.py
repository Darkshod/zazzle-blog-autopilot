"""Configuration loader combining config/settings.yaml and environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = ROOT_DIR / "config" / "settings.yaml"


class BrandConfig(BaseModel):
    name: str = "Your Brand Name"
    tagline: str = "Thoughtful Gift Guides, Custom Stationery & Artisan Home Finds"
    contact_email: str = "hello@example.com"
    base_url: str = "https://example.pages.dev"
    primary_market: str = "US"
    secondary_markets: list[str] = Field(default_factory=lambda: ["GB", "CA", "AU"])


class MonetizationConfig(BaseModel):
    zazzle_affiliate_approved: bool = False
    zazzle_affiliate_id: str = ""
    zazzle_affiliate_param: str = "rf"
    adsense_ready_pages: bool = True
    applicant_country: str = "MA"


class PublishingConfig(BaseModel):
    require_human_approval: bool = True
    min_word_count: int = 750
    max_keyword_density_pct: float = 2.8
    auto_publish_approved: bool = False


class ScheduleJob(BaseModel):
    time: str
    agent: str
    description: str


class ScheduleConfig(BaseModel):
    timezone: str = "America/New_York"
    jobs: list[ScheduleJob] = Field(default_factory=list)


class AppSettings(BaseModel):
    brand: BrandConfig = Field(default_factory=BrandConfig)
    monetization: MonetizationConfig = Field(default_factory=MonetizationConfig)
    publishing: PublishingConfig = Field(default_factory=PublishingConfig)
    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "search_demand": 0.25,
            "buyer_intent": 0.25,
            "competition_difficulty": 0.20,
            "product_relevance": 0.15,
            "seasonal_opportunity": 0.10,
            "ranking_feasibility": 0.05,
        }
    )
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)


def load_settings(path: Path | None = None) -> AppSettings:
    """Load YAML settings and apply non-secret environment overrides."""
    cfg_path = path or DEFAULT_SETTINGS_PATH
    raw: dict[str, Any] = {}
    if cfg_path.exists():
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    settings = AppSettings.model_validate(raw)

    if env_brand := os.getenv("BRAND_NAME"):
        settings.brand.name = env_brand
    if env_url := os.getenv("SITE_BASE_URL"):
        settings.brand.base_url = env_url.rstrip("/")
    if env_aff := os.getenv("ZAZZLE_AFFILIATE_ID"):
        settings.monetization.zazzle_affiliate_id = env_aff
    if env_approved := os.getenv("ZAZZLE_AFFILIATE_APPROVED"):
        settings.monetization.zazzle_affiliate_approved = env_approved.lower() == "true"

    return settings
