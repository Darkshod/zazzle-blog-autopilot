"""Conversion Optimization Agent — responsive product cards, honest CTA funnels & affiliate gating."""

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
    price_line = (
        f"Verified Price: ${product.price_usd:.2f} USD"
        if product.price_usd is not None
        else "Check current US price & customization options on Zazzle"
    )
    points_html = "".join(f"<li>{pt}</li>" for pt in (product.selling_points or [product.description]))
    rel_attr = 'rel="sponsored noopener noreferrer"' if is_aff else 'rel="noopener noreferrer"'
    link_badge = "Affiliate Partner Link" if is_aff else "Direct Zazzle Product Link"
    img_html = (
        f'<div class="rec-card-media"><img src="{product.image_url}" alt="{product.name}" width="720" height="900" loading="lazy" decoding="async" /></div>'
        if product.image_url
        else ""
    )
    return (
        f'<div class="rec-card">\n'
        f'  {img_html}\n'
        f'  <div class="rec-card-body">\n'
        f'    <span class="rec-badge">{link_badge} &middot; {product.category}</span>\n'
        f'    <h3>{product.name}</h3>\n'
        f'    <p><strong>Best For:</strong> {product.target_customer} &middot; <strong>Style:</strong> {product.design_style}</p>\n'
        f'    <p>{product.description}</p>\n'
        f'    <ul>{points_html}</ul>\n'
        f'    <p class="rec-price">{price_line}</p>\n'
        f'    <a class="zazzle-cta-card" href="{dest_url}" data-article="{article_slug}" data-product-id="{product.id or 0}" data-affiliate="{str(is_aff).lower()}" target="_blank" {rel_attr}>Customize &amp; View on Zazzle &rarr;</a>\n'
        f'  </div>\n'
        f'</div>\n'
    )


class ConversionOptimizationAgent(BaseAgent):
    name = "conversion_optimization"

    def execute(self, **kwargs: Any) -> TaskResult:
        products = self.db.list_products()
        articles = self.db.list_articles()
        return TaskResult(
            agent_name=self.name,
            task="audit_conversion_funnels",
            status="success",
            input_summary={"products": len(products), "articles": len(articles)},
            output_summary={
                "reusable_cards_available": len(products),
                "affiliate_mode_active": bool(
                    self.settings.monetization.zazzle_affiliate_approved
                    and self.settings.monetization.zazzle_affiliate_id
                ),
            },
            recommendations=[
                "Keep affiliate links explicitly tagged rel='sponsored' and visually labeled.",
                "Never invent discounts, scarcity timers, or unverified customer ratings.",
            ],
        )
