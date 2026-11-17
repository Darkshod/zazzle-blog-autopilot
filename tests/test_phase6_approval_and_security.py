"""Section 7 tests: GA4 validation, Pinterest 20-pin approval persistence, exclusion & Dashboard status."""

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from zazzle_blog_autopilot.config import validate_ga4_measurement_id
from zazzle_blog_autopilot.dashboard import create_app


def test_ga4_measurement_id_validation() -> None:
    assert validate_ga4_measurement_id("G-AB12CD34EF") is True
    assert validate_ga4_measurement_id("UA-123456-1") is False
    assert validate_ga4_measurement_id("invalid-id") is False


def test_pinterest_approval_persistence_and_exclusions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("GA4_MEASUREMENT_ID", raising=False)
    monkeypatch.delenv("GSC_ACCESS_TOKEN", raising=False)
    repo_root = Path(__file__).resolve().parents[1]
    (tmp_path / "config").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy2(repo_root / "config" / "settings.yaml", tmp_path / "config" / "settings.yaml")
    shutil.copy2(repo_root / "data" / "sample_products.csv", tmp_path / "data" / "sample_products.csv")

    # Seed 3 pins in pinterest_approval_state.json
    state = {
        "account": "@rafafo1225",
        "total_pins": 3,
        "batch_authorized": False,
        "audit_log": [],
        "pins": [
            {"pin_number": 1, "title": "Pin 1", "url_http_status": 200, "decision": "pending_approval"},
            {"pin_number": 2, "title": "Pin 2", "url_http_status": 200, "decision": "pending_approval"},
            {"pin_number": 3, "title": "Pin 3", "url_http_status": 200, "decision": "pending_approval"},
        ],
    }
    (tmp_path / "pinterest_approval_state.json").write_text(json.dumps(state), encoding="utf-8")

    client = TestClient(create_app(root_dir=tmp_path))

    # Cannot authorize batch when 0 pins are approved
    assert client.post("/api/pinterest/authorize-batch").status_code == 400

    assert client.post("/api/pinterest/decision", json={"pin_number": 1, "decision": "approved"}).status_code == 200
    assert client.post("/api/pinterest/decision", json={"pin_number": 2, "decision": "rejected"}).status_code == 200
    assert client.post("/api/pinterest/decision", json={"pin_number": 3, "decision": "needs_edit", "edit_note": "New image"}).status_code == 200

    auth = client.post("/api/pinterest/authorize-batch").json()
    assert auth["batch_authorized"] is True
    assert auth["approved_count"] == 1
    assert auth["excluded_rejected"] == 1
    assert auth["excluded_needs_edit"] == 1

    # Dashboard integration status must accurately report NOT CONFIGURED when tokens missing
    status = client.get("/api/integration-status").json()
    assert status["google_analytics"]["status"] == "NOT CONFIGURED"
    assert status["google_search_console"]["status"] == "NOT CONFIGURED"
    assert status["google_search_console"]["ownership_verified"] is False
