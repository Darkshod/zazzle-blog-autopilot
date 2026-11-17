"""Conversion Optimization Agent — reusable product cards, honest CTA funnels & affiliate gating."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from ..models import Product, TaskResult
from . import BaseAgent


def build_product_link(product: Product, affiliate_approved: bool, affiliate_id: str, param: str = "rf") -> tuple[str, bool]:
    """Return (destination_url, is_affiliate_link). Never disguises or forces unapproved affiliate tags."""
    url = product.url.strip()
    if affiliate_approved and affiliate_id.strip():
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query))
        query[param] = affiliate_id.strip()
        new_url = urlunparse(parsed._replace(query=urlencode(query)))
        return new_url, True
    return url, False


def render_product_card_markdown(
    product: Product,
    article_slug: str,
    affiliate_approved: bool,
    affiliate_id: str,
    param: str = "rf",
) -> str:
    dest_url, is_aff = build_product_link(product, affiliate_approved, affiliate_id, param)
    price_line = f"**Verified Price:** ${product.price_usd:.2f} USD" if product.price_usd is not None else "**Price:** Check current US listing price on Zazzle"
    points = "\n".join(f"- {pt}" for pt in (product.selling_points or [product.description]))
    rel_attr = 'rel="sponsored noopener noreferrer"' if is_aff else 'rel="noopener noreferrer"'
    img_html = (
        f'<p><img src="{product.image_url}" alt="{product.name}" loading="lazy" style="max-width:340px;width:100%;border-radius:10px;" /></p>\n'
        if product.image_url
        else ""
    )
    return (
        f"### Featured Pick: {product.name}\n\n"
        f"{img_html}"
        f"- **Best For:** {product.target_customer}\n"
        f"- **Style & Occasion:** {product.design_style} ({product.occasion_season})\n"
        f"- {price_line}\n\n"
        f"**Why It Fits:** {product.description}\n\n"
        f"{points}\n\n"
        f'<a class="zazzle-cta-card" href="{dest_url}" data-article="{article_slug}" data-product-id="{product.id or 0}" data-affiliate="{str(is_aff).lower()}" target="_blank" {rel_attr}>View {product.name} on Zazzle &rarr;</a>\n'
    )


class ConversionOptimizationAgent(BaseAgent):
    name = "conversion_optimization"

    def execute(self, **kwargs: Any) -> TaskResult:
        products = self.db.list_products()
        articles = self.db.list_articles()
        cards_ready = len(products)
        return TaskResult(
            agent_name=self.name,
            task="audit_conversion_funnels",
            status="success",
            input_summary={"products": len(products), "articles": len(articles)},
            output_summary={
                "reusable_cards_available": cards_ready,
                "affiliate_mode_active": bool(
                    self.settings.monetization.zazzle_affiliate_approved
                    and self.settings.monetization.zazzle_affiliate_id
                ),
            },
            recommendations=[
                "Keep affiliate links explicitly tagged rel='sponsored' and disclose them above the fold.",
                "Never invent discounts, scarcity timers, or unverified customer ratings.",
            ],
        )
