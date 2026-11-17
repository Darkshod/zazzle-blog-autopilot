"""Product Intelligence & Research Agent for Zazzle catalogs."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..models import Product, TaskResult
from . import BaseAgent

ZAZZLE_HOSTS = {"www.zazzle.com", "zazzle.com", "www.zazzle.co.uk", "www.zazzle.ca", "www.zazzle.com.au"}


def is_valid_zazzle_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme == "https" and parsed.netloc.lower() in ZAZZLE_HOSTS and len(parsed.path) > 1


def _split_list(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;|,]", raw or "") if item.strip()]


class ProductResearchAgent(BaseAgent):
    name = "product_research"

    def import_csv(self, csv_path: Path) -> tuple[int, list[str]]:
        imported = 0
        errors: list[str] = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for idx, row in enumerate(reader, start=2):
                url = (row.get("url") or "").strip()
                if not is_valid_zazzle_url(url):
                    errors.append(f"Row {idx}: invalid or non-Zazzle URL '{url}'")
                    continue
                price_raw = (row.get("price_usd") or "").strip()
                price_usd = float(price_raw) if price_raw else None
                product = Product(
                    name=row["name"].strip(),
                    category=row["category"].strip(),
                    url=url,
                    description=row["description"].strip(),
                    tags=_split_list(row.get("tags", "")),
                    target_customer=row.get("target_customer", "US gift shoppers").strip(),
                    design_style=row.get("design_style", "Illustrated").strip(),
                    occasion_season=row.get("occasion_season", "Evergreen").strip(),
                    price_usd=price_usd,
                    selling_points=_split_list(row.get("selling_points", "")),
                    search_terms=_split_list(row.get("search_terms", "")),
                    image_url=(row.get("image_url") or "").strip() or None,
                    source="csv",
                )
                self.db.upsert_product(product)
                imported += 1
        return imported, errors

    def add_manual_product(
        self,
        name: str,
        category: str,
        url: str,
        description: str,
        tags: list[str] | None = None,
        target_customer: str = "US shoppers",
        design_style: str = "Original illustration",
        occasion_season: str = "Evergreen",
        price_usd: float | None = None,
        selling_points: list[str] | None = None,
        search_terms: list[str] | None = None,
    ) -> int:
        if not is_valid_zazzle_url(url):
            raise ValueError(f"Invalid Zazzle URL: {url}")
        product = Product(
            name=name.strip(),
            category=category.strip(),
            url=url.strip(),
            description=description.strip(),
            tags=tags or [],
            target_customer=target_customer.strip(),
            design_style=design_style.strip(),
            occasion_season=occasion_season.strip(),
            price_usd=price_usd,
            selling_points=selling_points or [],
            search_terms=search_terms or [name.lower()],
            source="manual",
        )
        return self.db.upsert_product(product)

    def execute(self, csv_path: Path | None = None, **kwargs: Any) -> TaskResult:
        errors: list[str] = []
        imported = 0
        if csv_path and csv_path.exists():
            imported, errors = self.import_csv(csv_path)
        products = self.db.list_products()
        return TaskResult(
            agent_name=self.name,
            task="import_and_analyze_products",
            status="warning" if errors else "success",
            input_summary={"csv_path": str(csv_path) if csv_path else "none"},
            output_summary={"imported_now": imported, "total_products": len(products)},
            errors=errors,
            recommendations=[
                "Leave price_usd blank unless verified from an authorized Zazzle feed or public listing."
            ],
        )
