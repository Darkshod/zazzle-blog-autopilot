"""Stage 1 tests: configuration, domain models, SQLite deduplication, and atomic backup."""

from pathlib import Path

from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.db import Database
from zazzle_blog_autopilot.models import Product, TaskResult


def test_load_settings_defaults() -> None:
    from zazzle_blog_autopilot.config import AppSettings

    default_settings = AppSettings()
    assert default_settings.monetization.zazzle_affiliate_approved is False

    settings = load_settings()
    assert settings.brand.primary_market == "US"
    assert abs(sum(settings.scoring_weights.values()) - 1.0) < 1e-6


def test_db_product_dedup_and_backup(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    p = Product(
        name="Test Ceramic Mug",
        category="Coffee Mugs",
        url="https://www.zazzle.com/test_mug-123456",
        description="Hand-illustrated mug",
        tags=["ceramic mug", "gift"],
        target_customer="US coffee drinkers",
        design_style="Linocut",
        occasion_season="Evergreen",
        price_usd=None,
        selling_points=["11oz ceramic"],
        search_terms=["ceramic coffee mug gift"],
    )
    id1 = db.upsert_product(p)
    id2 = db.upsert_product(p)
    assert id1 == id2
    assert len(db.list_products()) == 1

    db.log_agent_result(TaskResult(agent_name="test_agent", task="unit_test", status="success"))
    assert len(db.list_agent_logs()) == 1

    backup_file = db.backup(tmp_path / "backups")
    assert backup_file.exists()
    assert backup_file.stat().st_size > 0
