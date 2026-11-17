"""Stage 4 tests: FastAPI dashboard and every button endpoint."""

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from zazzle_blog_autopilot.dashboard import create_app


def test_dashboard_all_buttons_end_to_end(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    (tmp_path / "config").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy2(repo_root / "config" / "settings.yaml", tmp_path / "config" / "settings.yaml")
    shutil.copy2(repo_root / "data" / "sample_products.csv", tmp_path / "data" / "sample_products.csv")

    app = create_app(root_dir=tmp_path)
    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert client.post("/api/research-products").json()["output_summary"]["total_products"] >= 8
    assert client.post("/api/find-keywords").json()["output_summary"]["keywords_saved"] >= 8

    gen = client.post("/api/generate-articles").json()
    assert gen["content"]["output_summary"]["articles_created"] >= 1

    slug = gen["content"]["output_summary"]["slugs"][0]
    assert client.post(f"/api/articles/{slug}/approve").json()["status"] == "approved"

    pub = client.post("/api/publish-approved").json()
    assert pub["published_count"] == 1
    assert pub["seo_audit"]["output_summary"]["healthy"] is True

    assert client.post("/api/generate-pins").json()["output_summary"]["pins_prepared"] >= 3
    assert client.post("/api/run-seo-audit").json()["output_summary"]["healthy"] is True

    client.post(f"/api/track-click?event_type=outbound_product&article_slug={slug}&product_id=1&is_affiliate=false")
    rep = client.post("/api/export-reports").json()
    assert Path(rep["report_file"]).exists()
    assert Path(rep["backup"]).exists()
    assert rep["metrics"]["product_outbound_clicks"] == 1
