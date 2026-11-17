"""Phase 4 Master OS tests: 17-agent orchestration, Emergency Stop, Financial Ledger, Security & Weekly Report."""

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from zazzle_blog_autopilot.agents.manager import ManagerAgent
from zazzle_blog_autopilot.config import load_settings
from zazzle_blog_autopilot.dashboard import create_app
from zazzle_blog_autopilot.db import Database


def test_17_agent_manager_and_emergency_stop(tmp_path: Path) -> None:
    settings = load_settings()
    db = Database(tmp_path / "os.db")
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_products.csv"

    mgr = ManagerAgent(db=db, settings=settings, work_dir=tmp_path)
    out = mgr.run_all(csv_path=csv_path, run_id="os_run", resume=False, max_articles=2)
    assert out["agents_registered"] == 17
    assert len(out["steps_executed"]) == 15
    assert len(db.list_executive_tasks()) == 15

    # Financial ledger should honestly show NOT VERIFIED when empty, and sum only verified entries
    fin_empty = db.get_financial_summary()
    assert fin_empty["gross_revenue_usd"] == 0.0
    assert "NOT VERIFIED" in fin_empty["status_label"]

    db.record_financial_entry("affiliate_commissions", 12.50, verified=True, note="Verified Zazzle payout")
    db.record_financial_entry("product_sales", 99.00, verified=False, note="Unverified estimate")
    fin_verified = db.get_financial_summary()
    assert fin_verified["gross_revenue_usd"] == 12.50

    # Emergency stop blocks runs until cleared
    db.set_system_flag("emergency_stop", "true")
    blocked = mgr.run_all(csv_path=csv_path, run_id="os_blocked", resume=False)
    assert blocked["status"] == "EMERGENCY_STOP_ACTIVE"


def test_executive_dashboard_weekly_and_emergency_endpoints(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    (tmp_path / "config").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy2(repo_root / "config" / "settings.yaml", tmp_path / "config" / "settings.yaml")
    shutil.copy2(repo_root / "data" / "sample_products.csv", tmp_path / "data" / "sample_products.csv")

    client = TestClient(create_app(root_dir=tmp_path))
    assert client.get("/").status_code == 200
    weekly = client.post("/api/run-weekly-report").json()
    assert weekly["gsc"]["connected"] is False
    assert client.post("/api/emergency-stop?active=true").json()["emergency_stop"] is True
    assert client.post("/api/emergency-stop?active=false").json()["emergency_stop"] is False
