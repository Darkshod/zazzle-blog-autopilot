"""SEO Content Creation Agent — natural American English guides with topical cluster internal links."""

from __future__ import annotations

import re
from typing import Any

from ..models import Article, Product, TaskResult
from . import BaseAgent
from .competitor_analysis import CONTENT_FORMATS
from .conversion import build_product_link, render_product_card_markdown


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:72] or "article"


def _category_guidance(product: Product) -> str:
    cat = product.category.lower()
    if "card" in cat or "stationery" in cat:
        return (
            "For folded 5x7 greeting cards and 3.5x2 business stationery, keep custom text concise so "
            "the typography stays balanced inside the print safe zone. Zazzle lets you preview paper "
            "weights—such as matte or felt—before adding your order to the cart."
        )
    if "mug" in cat:
        return (
            "Classic 11oz ceramic mugs give daily-use visibility without feeling bulky on a desk or kitchen shelf. "
            "Check the 3D wrap preview on Zazzle before checkout to make sure the artwork sits centered for right- or left-handed pouring."
        )
    if "apparel" in cat or "shirt" in cat:
        return (
            "When ordering graphic apparel, compare Zazzle's garment style selector (classic unisex cotton versus tri-blend or relaxed fits) "
            "and check the chest print placement preview on light or cream fabric tones for crisp contrast."
        )
    if "art" in cat or "poster" in cat:
        return (
            "Wall prints look sharpest when matched to standard US frame sizes like 18x24 or 16x20 with a neutral mat. "
            "Review the paper finish options on Zazzle depending on whether the piece hangs near sunny windows."
        )
    return (
        "Use Zazzle's live customization preview to check cropping, bleed margins, and material finishes before placing your order."
    )


def _format_intro(content_format: str, primary_kw: str, product: Product) -> str:
    if "Comparison" in content_format:
        return (
            f"Choosing the right **{primary_kw}** comes down to matching visual craft with how the recipient will actually use it. "
            f"Below, we compare the **{product.name}** against alternative gift formats in the same aesthetic so you can pick the strongest fit."
        )
    if "Customization" in content_format or "Design" in content_format:
        return (
            f"Great personalization should look effortless—not squeezed into an awkward template. "
            f"In this practical walkthrough for **{primary_kw}**, we show how to tailor text fields cleanly and pair coordinating pieces on Zazzle."
        )
    if "Holiday" in content_format or "Occasion" in content_format:
        return (
            f"Seasonal shopping in the US rewards early planners who want thoughtful pieces instead of last-minute generic gifts. "
            f"This guide explores **{primary_kw}** through the lens of {product.design_style.lower()} craft and practical everyday gifting."
        )
    return (
        f"Finding **{primary_kw}** that feels genuinely personal—without hours of scrolling—starts with strong illustration and clear print quality. "
        f"Here is a closer look at why the **{product.name}** resonates with {product.target_customer}."
    )


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
    internal_links: list[tuple[str, str]],
) -> str:
    card_primary = render_product_card_markdown(
        product, slug, affiliate_approved, affiliate_id, affiliate_param
    )
    secondary_cards = "\n".join(
        render_product_card_markdown(rp, slug, affiliate_approved, affiliate_id, affiliate_param)
        for rp in related_products[:2]
    )
    dest_url, _ = build_product_link(product, affiliate_approved, affiliate_id, affiliate_param)
    disclosure = (
        "> **Editorial & Affiliate Disclosure:** Links labeled *Affiliate Partner Link* use an authorized referral tag (`rel=\"sponsored\"`) that may earn a commission at no extra cost to you. Ordinary product links are labeled separately."
    )
    internal_section = (
        "\n".join(f"- [{anchor}]({href})" for anchor, href in internal_links)
        if internal_links
        else "- [Browse All GRIMORA11 Guides](/blog.html)"
    )

    intro = _format_intro(content_format, primary_kw, product)
    cat_tip = _category_guidance(product)

    body = f"""{disclosure}

# {title}

{intro}

## Why {product.design_style} Fits {product.occasion_season}

Design details determine whether a gift gets displayed or tucked away in a drawer. Built around **{product.design_style.lower()}**, the **{product.name}** pairs balanced negative space with legible typography tailored for **{product.target_customer}**.

Instead of relying on loud novelty slogans, this piece works naturally for {semantic_vars[0] if semantic_vars else primary_kw} and coordinates easily with matching stationery or kitchenware.

### Quick Fit Summary

- **Designed For:** {product.target_customer}
- **Visual Style:** {product.design_style}
- **Best Occasion:** {product.occasion_season}
- **Product Format:** {product.category}
- **Related Ideas:** {', '.join(secondary_kws[:4]) if secondary_kws else primary_kw}

{card_primary}

## Practical Customization & Ordering Tips

{cat_tip}

1. **Preview Before Checkout:** Zoom in on Zazzle's live preview to verify spelling, line breaks, and margins.
2. **Coordinate a Gift Bundle:** Pair a hero item like [{product.name}]({dest_url}) with a matching card or everyday mug to raise the presentation value without guesswork.
3. **Confirm Live US Pricing & Delivery:** Always check the live Zazzle listing for current pricing, regional print facility routing (US, UK, Canada, or Australia), and production timelines.

## Coordinating Picks to Pair Together

{secondary_cards if secondary_cards else f"Browse more curated designs in {product.category} directly on Zazzle."}

## Who Should Pick This (And When to Skip)

- **Best Choice If:** You want {semantic_vars[1] if len(semantic_vars) > 1 else primary_kw} with original artwork and clean customization for {product.occasion_season}.
- **Consider Alternatives If:** You need same-day local big-box pickup rather than made-to-order printing.

## Frequently Asked Questions

### Can I personalize the text or product style on Zazzle?
Yes—open the **Personalize** or **Style** selector on the Zazzle product page to edit supported text fields, sizes, or finishes before ordering.

### Are prices, discounts, or shipping dates guaranteed here?
No. Pricing, promotions, and shipping estimates are set dynamically on Zazzle, so we never state unverified prices, fake ratings, or guaranteed delivery promises.

## Related Guides in This Topic Cluster

{internal_section}

## Sources & Verification

- Catalog record (`{product.source}`): [{product.name}]({product.url})
- Marketplace details: [Zazzle](https://www.zazzle.com/)
- Topic signals: Qualitative US market & Google Suggest research (free-tier estimates; search volumes are not fabricated).
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

        # Build planned slug list first so every article gets rich cluster internal links
        planned: list[tuple[Any, Product, str, str]] = []
        seen = set(existing_slugs)
        for idx, kw in enumerate(keywords):
            if len(planned) >= max_articles:
                break
            product = prod_by_id.get(kw.matched_product_id) or (products[0] if products else None)
            if not product:
                continue
            slug = slugify(kw.keyword)
            if slug in seen:
                continue
            seen.add(slug)
            fmt = CONTENT_FORMATS[idx % len(CONTENT_FORMATS)]
            title = f"{kw.keyword.title()}: Curated 2026 Buyer & Gift Guide"
            planned.append((kw, product, slug, fmt, title))

        created_slugs: list[str] = []
        for kw, product, slug, fmt, title in planned:
            meta_desc = (
                f"US guide to {kw.keyword}: customization tips, styling ideas, and curated {product.category.lower()} picks on Zazzle."
            )[:158]
            secondary = list(dict.fromkeys((product.search_terms or []) + product.tags[:4]))[:5]
            semantic = [
                f"custom {product.category.lower()}",
                f"{product.design_style.lower()} gifts",
                f"{product.occasion_season.lower()} gift ideas",
            ]
            related = [p for p in products if p.id != product.id][:2]

            # Cluster internal links: only link to already-published/approved guides (avoid broken links to unpublished drafts)
            published_or_approved = [a for a in existing_articles if a.status in ("published", "approved") and a.slug != slug]
            cluster_links = [
                (a.title, f"/articles/{a.slug}.html")
                for a in published_or_approved
                if a.category == product.category
            ]
            if len(cluster_links) < 3:
                cluster_links.extend(
                    (a.title, f"/articles/{a.slug}.html")
                    for a in published_or_approved
                    if (a.title, f"/articles/{a.slug}.html") not in cluster_links
                )
            if not cluster_links:
                cluster_links = [("Browse All Curated Gift Guides", "/blog.html")]
            cluster_links = cluster_links[:3]

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
                internal_links=cluster_links,
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
                internal_links=[href for _, href in cluster_links],
                sources=[product.url, "https://www.zazzle.com/"],
                affiliate_disclosure_included=True,
                status="draft",
            )
            self.db.upsert_article(article)
            created_slugs.append(slug)

        return TaskResult(
            agent_name=self.name,
            task="generate_seo_article_drafts",
            status="success",
            input_summary={"max_articles": max_articles, "available_keywords": len(keywords)},
            output_summary={"articles_created": len(created_slugs), "slugs": created_slugs},
            recommendations=["Run Editorial QA Agent before moving drafts into awaiting_approval."],
        )
