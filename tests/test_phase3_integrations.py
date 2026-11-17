"""Phase 3 tests: GSC honesty gating, Pinterest Top-20 prioritizer, and anti-cannibalization."""

import sys
from pathlib import Path

from zazzle_blog_autopilot.integrations.gsc import GoogleSearchConsoleClient
from zazzle_blog_autopilot.integrations.pinterest_api import PinterestAPIClient, prioritize_top_pins
from zazzle_blog_autopilot.models import PinterestPin


def test_gsc_unconnected_never_fabricates() -> None:
    client = GoogleSearchConsoleClient("https://darkshod.github.io", access_token="")
    res = client.fetch_search_analytics()
    assert res["connected"] is False
    assert res["rows"] == []


def test_pinterest_prioritizer_and_approval_gate() -> None:
    pins = [
        PinterestPin(
            article_slug="art-1",
            title=f"Gift Guide Pin {i}",
            description="Curated holiday gift guide",
            image_concept="2:3 flatlay",
            destination_url="https://darkshod.github.io/articles/art-1.html",
            status="pending_approval",
        )
        for i in range(5)
    ]
    top = prioritize_top_pins(pins, limit=20, max_per_article=2)
    assert len(top) == 2

    api = PinterestAPIClient(access_token="fake", board_id="123")
    res = api.publish_pin(top[0], "https://darkshod.github.io/images/pinkmas-card.jpg")
    assert res["published"] is False
    assert "approved" in res["reason"].lower()


def test_cannibalization_detector() -> None:
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from phase3_engine import is_cannibalizing  # type: ignore

    existing = ["pinkmas christmas card", "old money christmas card"]
    assert is_cannibalizing("pinkmas christmas card", existing) is True
    assert is_cannibalizing("ceramic pottery studio mug", existing) is False
