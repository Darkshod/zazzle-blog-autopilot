"""Stage 2 tests: all 12 agents, scoring weights, QA gates, affiliate gating, and Manager resume."""

from pathlib import Path

from zazzle_blog_autopilot.agents.conversion import build_product_link
from zazzle_blog_autopilot.agents.editorial_qa import evaluate_article_quality
from zazzle_blog_autopilot.agents.manager import ManagerAgent
from zazzle_blog_autopilot.agents.product_research import is_valid_zazzle_url
from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.db import Database
from zazzle_blog_autopilot.models import Article, Product


def test_zazzle_url_validation_and_affiliate_gating() -> None:
    assert is_valid_zazzle_url("https://www.zazzle.com/test_card-256123")
    assert not is_valid_zazzle_url("https://evil.example.com/card")
    assert not is_valid_zazzle_url("http://www.zazzle.com/insecure")

    p = Product(
        name="Card",
        category="Cards",
        url="https://www.zazzle.com/test_card-256123",
        description="Desc",
        target_customer="US",
        design_style="Ink",
        occasion_season="Holiday",
    )
    url_plain, is_aff_plain = build_product_link(p, affiliate_approved=False, affiliate_id="238999")
    assert is_aff_plain is False
    assert "rf=" not in url_plain

    url_aff, is_aff_true = build_product_link(p, affiliate_approved=True, affiliate_id="238999")
    assert is_aff_true is True
    assert "rf=238999" in url_aff


def test_editorial_qa_rejects_thin_and_fabricated_content() -> None:
    thin = Article(
        slug="thin-test",
        title="Thin Article",
        meta_description="Short meta description that is at least one hundred and ten characters long for testing purposes right here.",
        content_format="Guide",
        search_intent="commercial",
        primary_keyword="test mug",
        category="Mugs",
        markdown_body="# Thin\n\n5 out of 5 stars guaranteed overnight shipping.",
        word_count=9,
    )
    score, passed, notes = evaluate_article_quality(thin, all_titles=[thin.title])
    assert not passed
    assert score < 80
    assert any("Thin content" in n for n in notes)
    assert any("Banned" in n for n in notes)


def test_manager_full_pipeline_and_resume(tmp_path: Path) -> None:
    settings = load_settings()
    db = Database(tmp_path / "autopilot.db")
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_products.csv"

    mgr = ManagerAgent(db=db, settings=settings, work_dir=tmp_path)
    out = mgr.run_all(csv_path=csv_path, run_id="test_run_1", resume=True, max_articles=3)

    assert len(db.list_products()) == 8
    assert len(db.list_keywords()) >= 8
    articles = db.list_articles()
    assert len(articles) == 3
    assert all(a.qa_passed and a.status == "awaiting_approval" for a in articles)
    assert len(db.list_pins()) == 9  # 3 pins per article
    assert (tmp_path / "site" / "assets" / "generated" / "image_manifest.json").exists()

    # Resume with same run_id should skip already completed steps
    out_resume = mgr.run_all(csv_path=csv_path, run_id="test_run_1", resume=True, max_articles=3)
    assert out_resume["steps_executed"] == []
