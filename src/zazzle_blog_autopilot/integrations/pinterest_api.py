"""Compliant Pinterest API v5 distribution client & Top-20 pin prioritizer."""

from __future__ import annotations

import os
from typing import Any

import requests

from ..models import PinterestPin


def prioritize_top_pins(pins: list[PinterestPin], limit: int = 20, max_per_article: int = 2) -> list[PinterestPin]:
    """Score pending pins by buyer-intent signals and cap per-article frequency to avoid spam."""
    def _score(p: PinterestPin) -> tuple[int, int]:
        t = p.title.lower()
        intent_pts = sum(2 for w in ("gift", "guide", "custom", "card", "mug", "shirt", "christmas", "holiday") if w in t)
        return (intent_pts, len(p.description))

    ranked = sorted(pins, key=_score, reverse=True)
    selected: list[PinterestPin] = []
    per_article: dict[str, int] = {}
    for p in ranked:
        cnt = per_article.get(p.article_slug, 0)
        if cnt >= max_per_article:
            continue
        selected.append(p)
        per_article[p.article_slug] = cnt + 1
        if len(selected) >= limit:
            break
    return selected


class PinterestAPIClient:
    """Publishes ONLY human-approved pins via official Pinterest API v5."""

    def __init__(self, access_token: str | None = None, board_id: str | None = None) -> None:
        self.access_token = (access_token or os.getenv("PINTEREST_ACCESS_TOKEN") or "").strip()
        self.board_id = (board_id or os.getenv("PINTEREST_BOARD_ID") or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.board_id)

    def publish_pin(self, pin: PinterestPin, public_image_url: str) -> dict[str, Any]:
        if pin.status != "approved":
            return {"published": False, "reason": "Pin must be 'approved' before publishing."}
        if not self.is_configured:
            return {"published": False, "reason": "PINTEREST_ACCESS_TOKEN / PINTEREST_BOARD_ID not configured."}

        resp = requests.post(
            "https://api.pinterest.com/v5/pins",
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json={
                "board_id": self.board_id,
                "title": pin.title[:100],
                "description": f"{pin.description} {' '.join(pin.hashtags)}"[:500],
                "link": pin.destination_url,
                "media_source": {"source_type": "image_url", "url": public_image_url},
            },
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return {"published": True, "pin_id": resp.json().get("id")}
        return {"published": False, "reason": f"Pinterest API HTTP {resp.status_code}"}
