"""Stage 3 tests: static site builder, AdSense legal pages, sitemap, JSON-LD, and SEO audit."""

from pathlib import Path

from zazzle_blog_autopilot.agents.manager import ManagerAgent
from zazzle_blog_autopilot.agents.technical_seo import audit_built_site
from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.db import Database
from zazzle_blog_autopilot.site_builder import StaticBlogBuilder


def test_build_site_and_technical_seo_audit(tmp_path: Path) -> None:
    settings = load_settings()
    db = Database(tmp_path / "autopilot.db")
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_products.csv"

    mgr = ManagerAgent(db=db, settings=settings, work_dir=tmp_path)
    mgr.run_all(csv_path=csv_path, run_id="stage3", resume=False, max_articles=3)

    # Human approval step
    for art in db.list_articles():
        db.set_article_status(art.slug, "approved")

    builder = StaticBlogBuilder(db=db, settings=settings, root_dir=tmp_path)
    build_info = builder.build(include_approved=True)
    assert build_info["articles_built"] == 3

    dist = tmp_path / "dist"
    for page in ("index.html", "about.html", "contact.html", "privacy-policy.html", "editorial-standards.html", "sitemap.xml", "robots.txt"):
        assert (dist / page).exists(), f"Missing {page}"

    seo_report = audit_built_site(dist)
    assert seo_report["healthy"] is True, f"SEO issues: {seo_report['issues']}"
    assert seo_report["sitemap_valid"] is True
    assert seo_report["pages_checked"] >= 10
