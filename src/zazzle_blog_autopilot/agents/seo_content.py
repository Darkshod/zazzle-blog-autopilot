"""SEO Content Creation Agent — natural US-English long-form buying & gift guides."""

from __future__ import annotations

import re
from typing import Any

from ..models import Article, KeywordOpportunity, Product, TaskResult
from . import BaseAgent
from .competitor_analysis import CONTENT_FORMATS
from .conversion import build_product_link, render_product_card_markdown


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:72] or "article"


def _build_article_body(
    title: str,
    primary_kw: str,
    secondary_kws: list[str],
    semantic_vars: list[str],
    content_format: str,
    product: Product,
    related_products: list[Product],
    slug: str,
    affiliate_approved: bool,
    affiliate_id: str,
    affiliate_param: str,
    internal_links: list[str],
) -> str:
    card_primary = render_product_card_markdown(
        product, slug, affiliate_approved, affiliate_id, affiliate_param
    )
    secondary_cards = "\n".join(
        render_product_card_markdown(rp, slug, affiliate_approved, affiliate_id, affiliate_param)
        for rp in related_products[:2]
    )
    dest_url, is_aff = build_product_link(product, affiliate_approved, affiliate_id, affiliate_param)
    disclosure = (
        "> **Disclosure:** This guide features products hosted on Zazzle. If affiliate tracking is active and you purchase through a qualifying link, we may earn a small commission at no extra cost to you. Ordinary editorial product links are never disguised."
    )
    internal_section = (
        "\n".join(f"- [{lnk.strip('/').replace('-', ' ').title()}]({lnk})" for lnk in internal_links)
        if internal_links
        else "- [Browse All Curated Gift Guides](/)"
    )

    body = f"""{disclosure}

# {title}

Finding a gift or stationery piece that feels personal without spending hours browsing generic big-box catalogs can be surprisingly difficult. Shoppers across the United States increasingly look for **{primary_kw}** options that combine distinct illustration craft with easy online personalization. In this {content_format.lower()}, we break down what makes a design stand out, who it suits best, and how to customize your order directly on Zazzle.

## Why {product.design_style} Stands Out for {product.occasion_season}

When evaluating {semantic_vars[0] if semantic_vars else primary_kw}, visual balance and material fit matter just as much as the artwork itself. Designs rooted in **{product.design_style.lower()}** hold up across physical formats—whether printed on textured cardstock, everyday ceramic mugs, or soft cotton apparel.

Instead of relying on fleeting novelty templates, the **{product.name}** is built specifically for **{product.target_customer}**. Its palette and layout are structured so text remains legible at arm's length while keeping the central illustration crisp.

### Key Design & Material Highlights

- **Primary Audience:** {product.target_customer}
- **Aesthetic Direction:** {product.design_style}
- **Ideal Occasion:** {product.occasion_season}
- **Category:** {product.category}
- **Related Search Themes:** {', '.join(secondary_kws[:4]) if secondary_kws else primary_kw}

{card_primary}

## How to Customize and Choose the Right Format

One of the biggest advantages of ordering through Zazzle's print-on-demand marketplace is the ability to tailor text fields, paper finishes, or product styles before checkout. Before finalizing your order, review these practical steps:

1. **Check Text Hierarchy & Margins:** If you are customizing a card or business stationery template, keep names and dates concise so they match the original typographic proportions.
2. **Match Product Format to the Recipient:** For hosts or frequent travelers, ceramic mugs and practical accessories offer daily utility. For milestone celebrations, 5x7 folded cards or framed wall prints create a lasting keepsake.
3. **Verify Print Details Directly on Zazzle:** Always check the live product page for current pricing, available sizes, paper stocks, and estimated fulfillment timelines in your region (United States, UK, Canada, or Australia).

## Complementary Ideas to Pair Together

Gift buyers often increase the thoughtfulness of a present by pairing a hero item with a coordinating card or everyday accessory from the same visual family. Below are complementary picks worth considering alongside [{product.name}]({dest_url}):

{secondary_cards if secondary_cards else f"Explore more coordinated pieces in the {product.category} category directly on Zazzle."}

## Who Should Choose This Design (and Who Shouldn't)

To help you make a confident decision, consider how the recipient actually uses their favorite items:

- **Great Fit:** Shoppers seeking {semantic_vars[1] if len(semantic_vars) > 1 else primary_kw} with genuine illustrated character, clean typography, and customizable options for {product.occasion_season}.
- **Skip If:** You need overnight bulk wholesale shipping from a local warehouse rather than made-to-order printing, or prefer plain, unillustrated minimalist goods.

## Frequently Asked Questions

### Can I personalize the text before ordering?
Yes—many Zazzle templates allow you to edit names, greetings, or studio contact details directly inside Zazzle's online customizer prior to adding the item to your cart. Check the "Personalize" panel on the live product page to confirm editable fields.

### Are prices or shipping times guaranteed in this guide?
No. Because print-on-demand pricing, seasonal promotions, and regional shipping estimates change on Zazzle, we never state unverified prices or delivery promises here. Always confirm final pricing and shipping options on Zazzle at checkout.

### Where is the artwork printed?
Zazzle fulfills orders through its global print-on-demand network, serving shoppers across the United States as well as the UK, Canada, and Australia depending on the selected product and shipping destination.

## Related Guides on This Site

{internal_section}

## Sources & Editorial Notes

- Product metadata verified from catalog import (`{product.source}`): [{product.name}]({product.url})
- Marketplace customization & fulfillment context: [Zazzle Help & Marketplace](https://www.zazzle.com/)
- Market intent signals: US Google Suggest & seasonal category research (free-tier qualitative signals; exact search volumes are not fabricated).
"""
    return body.strip() + "\n"


class SEOContentAgent(BaseAgent):
    name = "seo_content"

    def execute(self, max_articles: int = 4, **kwargs: Any) -> TaskResult:
        products = self.db.list_products()
        keywords = self.db.list_keywords(limit=50)
        existing_articles = self.db.list_articles()
        existing_slugs = {a.slug for a in existing_articles}
        prod_by_id = {p.id: p for p in products}

        created_slugs: list[str] = []
        for idx, kw in enumerate(keywords):
            if len(created_slugs) >= max_articles:
                break
            product = prod_by_id.get(kw.matched_product_id) or (products[0] if products else None)
            if not product:
                continue

            fmt = CONTENT_FORMATS[idx % len(CONTENT_FORMATS)]
            title = f"{kw.keyword.title()}: Curated 2026 Buyer & Gift Guide"
            slug = slugify(kw.keyword)
            if slug in existing_slugs:
                continue

            meta_desc = (
                f"Explore our US-focused guide to {kw.keyword}. Compare styles, customization tips, and curated {product.category.lower()} picks on Zazzle."
            )[:158]
            secondary = list(dict.fromkeys((product.search_terms or []) + product.tags[:4]))[:5]
            semantic = [
                f"custom {product.category.lower()}",
                f"{product.design_style.lower()} gifts",
                f"{product.occasion_season.lower()} gift ideas",
            ]
            related = [p for p in products if p.id != product.id][:2]
            internal_links = [f"/articles/{a.slug}.html" for a in existing_articles[:2]]

            body = _build_article_body(
                title=title,
                primary_kw=kw.keyword,
                secondary_kws=secondary,
                semantic_vars=semantic,
                content_format=fmt,
                product=product,
                related_products=related,
                slug=slug,
                affiliate_approved=self.settings.monetization.zazzle_affiliate_approved,
                affiliate_id=self.settings.monetization.zazzle_affiliate_id,
                affiliate_param=self.settings.monetization.zazzle_affiliate_param,
                internal_links=internal_links,
            )
            wc = len(re.findall(r"\b\w+\b", body))
            article = Article(
                slug=slug,
                title=title,
                meta_description=meta_desc,
                content_format=fmt,
                search_intent=kw.search_intent,
                primary_keyword=kw.keyword,
                secondary_keywords=secondary,
                semantic_variations=semantic,
                category=product.category,
                tags=list(dict.fromkeys(product.tags[:5] + [product.occasion_season.lower()])),
                markdown_body=body,
                word_count=wc,
                matched_product_ids=[p.id for p in [product, *related] if p.id is not None],
                image_alt=f"{product.name} editorial lifestyle showcase for {kw.keyword}",
                internal_links=internal_links,
                sources=[product.url, "https://www.zazzle.com/"],
                affiliate_disclosure_included=True,
                status="draft",
            )
            self.db.upsert_article(article)
            existing_slugs.add(slug)
            created_slugs.append(slug)

        return TaskResult(
            agent_name=self.name,
            task="generate_seo_article_drafts",
            status="success",
            input_summary={"max_articles": max_articles, "available_keywords": len(keywords)},
            output_summary={"articles_created": len(created_slugs), "slugs": created_slugs},
            recommendations=["Run Editorial QA Agent before moving drafts into awaiting_approval."],
        )
