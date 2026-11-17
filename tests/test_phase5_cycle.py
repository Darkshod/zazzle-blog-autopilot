"""Phase 5 tests: GA4 & GSC meta injection, outbound click tracker JS, and GSC sitemap gating."""

from pathlib import Path

from zazzle_blog_autopilot.agents.manager import ManagerAgent
from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.db import Database
from zazzle_blog_autopilot.integrations.gsc import GoogleSearchConsoleClient
from zazzle_blog_autopilot.site_builder import StaticBlogBuilder


def test_ga4_and_gsc_meta_rendering_in_site_builder(tmp_path: Path) -> None:
    settings = load_settings()
    settings.brand.ga4_measurement_id = "G-TEST123456"
    settings.brand.gsc_verification_token = "verify-token-xyz"
    db = Database(tmp_path / "ga4.db")
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_products.csv"

    mgr = ManagerAgent(db=db, settings=settings, work_dir=tmp_path)
    mgr.run_all(csv_path=csv_path, run_id="ga4_test", resume=False, max_articles=1)
    for a in db.list_articles():
        db.set_article_status(a.slug, "approved")

    builder = StaticBlogBuilder(db=db, settings=settings, root_dir=tmp_path)
    builder.build(include_approved=True)

    article_files = list((tmp_path / "dist" / "articles").glob("*.html"))
    assert len(article_files) == 1
    html = article_files[0].read_text(encoding="utf-8")
    assert "G-TEST123456" in html
    assert "zazzle_outbound_click" in html
    assert "zazzle_affiliate_click" in html
    assert 'name="google-site-verification" content="verify-token-xyz"' in html


def test_gsc_sitemap_submit_blocked_without_token() -> None:
    gsc = GoogleSearchConsoleClient("https://darkshod.github.io", access_token="")
    res = gsc.submit_sitemap("https://darkshod.github.io/sitemap.xml")
    assert res["submitted"] is False
