"""Static Blog Site Builder — renders portable Markdown + fast mobile-first HTML for Cloudflare Pages."""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt

from .config import AppSettings
from .db import Database
from .models import Article


def _base_template(
    title: str,
    description: str,
    canonical_url: str,
    brand_name: str,
    brand_tagline: str,
    body_html: str,
    og_image: str = "",
    json_ld: list[dict[str, Any]] | None = None,
    ga4_id: str = "",
    gsc_token: str = "",
) -> str:
    ld_scripts = "\n  ".join(
        f'<script type="application/ld+json">{json.dumps(obj)}</script>' for obj in (json_ld or [])
    )
    og_img_tag = f'<meta property="og:image" content="{html.escape(og_image)}" />' if og_image else ""
    gsc_tag = f'<meta name="google-site-verification" content="{html.escape(gsc_token)}" />' if gsc_token else ""
    ga4_script = (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={html.escape(ga4_id)}"></script>\n'
        f'  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{html.escape(ga4_id)}",{{"anonymize_ip":true}});</script>'
        if ga4_id
        else ""
    )
    click_tracker_js = """<script>
(function(){if(window.__darkshodClickInit)return;window.__darkshodClickInit=true;document.addEventListener('click',function(e){var a=e.target.closest('a[href*="zazzle.com"]');if(!a||!a.href||a.href.indexOf('zazzle.com')===-1)return;var isAff=a.dataset.affiliate==='true'||a.href.indexOf('rf=')!==-1;var slug=a.dataset.article||(location.pathname.split('/').pop()||'home').replace('.html','')||'home';var payload={event_type:isAff?'affiliate_click':'outbound_product',article_slug:slug,product_id:a.dataset.productId||'',href:a.href};if(typeof gtag==='function'){gtag('event',isAff?'zazzle_affiliate_click':'zazzle_outbound_click',payload);}});})();
</script>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  {gsc_tag}
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <link rel="canonical" href="{html.escape(canonical_url)}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{html.escape(title)}" />
  <meta property="og:description" content="{html.escape(description)}" />
  <meta property="og:url" content="{html.escape(canonical_url)}" />
  {og_img_tag}
  <link rel="stylesheet" href="/assets/style.css" />
  {ga4_script}
  {ld_scripts}
</head>
<body>
  <header class="site-header">
    <div class="container nav-wrap">
      <a class="brand" href="/">{html.escape(brand_name)}</a>
      <nav aria-label="Primary navigation">
        <a href="/">Home</a>
        <a href="/categories/index.html">Categories</a>
        <a href="/about.html">About</a>
        <a href="/editorial-standards.html">Editorial Standards</a>
        <a href="/contact.html">Contact</a>
      </nav>
    </div>
  </header>
  <main class="container">
    {body_html}
  </main>
  <footer class="site-footer">
    <div class="container">
      <p><strong>{html.escape(brand_name)}</strong> &mdash; {html.escape(brand_tagline)}</p>
      <p class="footer-links">
        <a href="/privacy-policy.html">Privacy &amp; Cookie Policy</a> &middot;
        <a href="/editorial-standards.html">Editorial &amp; Affiliate Disclosure</a> &middot;
        <a href="/about.html">About</a> &middot;
        <a href="/contact.html">Contact</a> &middot;
        <a href="/sitemap.xml">Sitemap</a>
      </p>
    </div>
  </footer>
  {click_tracker_js}
</body>
</html>
"""


BLOG_CSS = """
:root{--bg:#faf8f4;--surface:#fff;--ink:#1b221e;--muted:#5b635e;--accent:#22382c;--gold:#a9864c;--border:#e5dfd4}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink);line-height:1.65}
a{color:var(--accent)}
.container{max-width:1040px;margin:0 auto;padding:0 1.25rem}
.site-header{background:var(--surface);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10}
.nav-wrap{display:flex;align-items:center;justify-content:space-between;padding:.9rem 1.25rem;gap:1rem;flex-wrap:wrap}
.brand{font-family:Georgia,serif;font-weight:700;font-size:1.25rem;text-decoration:none;color:var(--accent)}
nav{display:flex;gap:1rem;flex-wrap:wrap;font-size:.9rem}
nav a{text-decoration:none;color:var(--muted)}
nav a:hover{color:var(--ink)}
.hero{padding:2.5rem 0 2rem;border-bottom:1px solid var(--border);margin-bottom:2rem}
.hero h1{font-family:Georgia,serif;font-size:clamp(1.8rem,4vw,2.7rem);margin:0 0 .6rem;line-height:1.15}
.search-box{width:100%;max-width:440px;padding:.7rem 1rem;border:1px solid var(--border);border-radius:999px;font-size:.95rem;margin-top:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.5rem;margin:1.5rem 0 3rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;height:180px;object-fit:cover;display:block}
.card-body{padding:1.1rem;display:flex;flex-direction:column;flex:1}
.badge{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:var(--gold);font-weight:700}
.card h2,.card h3{font-family:Georgia,serif;font-size:1.2rem;margin:.35rem 0 .5rem}
.article-wrap{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:2rem;margin:2rem 0}
.article-wrap img{max-width:100%;height:auto;border-radius:8px}
.zazzle-cta-card{display:inline-block;margin:.6rem 0;padding:.75rem 1.4rem;background:var(--accent);color:#fff!important;border-radius:999px;text-decoration:none;font-weight:600}
.cta-secondary-btn{display:inline-block;margin:.6rem 0;padding:.72rem 1.3rem;background:#fff;color:var(--accent)!important;border:1px solid var(--accent);border-radius:999px;text-decoration:none;font-weight:600}
.top-cta-bar{display:flex;flex-wrap:wrap;gap:.75rem;align-items:center;margin:1rem 0 1.25rem;padding:.9rem 1.1rem;background:#faf8f4;border:1px solid var(--border);border-radius:10px}
.bottom-cta-box{margin:2rem 0 1.5rem;padding:1.5rem;background:#22382c;color:#faf8f4;border-radius:12px;text-align:center}
.bottom-cta-box h2,.bottom-cta-box h3{color:#fff;font-family:Georgia,serif;margin:0 0 .5rem}
.bottom-cta-box p{color:#e7e1d7;margin:0 auto .9rem;max-width:560px}
.bottom-cta-box .zazzle-cta-card{background:#a9864c;color:#fff!important}
.bottom-cta-box-actions{display:flex;flex-wrap:wrap;justify-content:center;gap:.75rem}
.rec-card{display:grid;grid-template-columns:210px 1fr;gap:1.25rem;background:#faf8f4;border:1px solid var(--border);border-radius:10px;padding:1rem;margin:1.25rem 0;align-items:start}
.rec-card-media img{width:100%;aspect-ratio:4/5;object-fit:cover;border-radius:8px;display:block}
.rec-badge{font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:var(--gold);font-weight:700;display:block;margin-bottom:.25rem}
.rec-card-body h3{margin:.15rem 0 .45rem;font-family:Georgia,serif}
.rec-price{font-weight:600;font-size:.92rem;color:var(--accent)}
blockquote{margin:1rem 0;padding:.8rem 1rem;background:#f4efe6;border-left:4px solid var(--gold);border-radius:4px}
.breadcrumb{font-size:.85rem;color:var(--muted);margin-bottom:1rem}
.site-footer{border-top:1px solid var(--border);padding:2rem 0;margin-top:3rem;text-align:center;font-size:.85rem;color:var(--muted)}
.footer-links a{margin:0 .35rem}
@media(max-width:640px){.article-wrap{padding:1.25rem}.rec-card{grid-template-columns:1fr}}
""".strip()


def _slug_part(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "general"


class StaticBlogBuilder:
    """Exports Markdown sources + builds fast static HTML site with AdSense-ready pages."""

    def __init__(self, db: Database, settings: AppSettings, root_dir: Path | None = None) -> None:
        self.db = db
        self.settings = settings
        self.root_dir = root_dir or Path.cwd()

    def build(self, include_approved: bool = True) -> dict[str, Any]:
        dist_dir = self.root_dir / "dist"
        content_dir = self.root_dir / "content" / "articles"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        (dist_dir / "articles").mkdir(parents=True, exist_ok=True)
        (dist_dir / "categories").mkdir(parents=True, exist_ok=True)
        (dist_dir / "tags").mkdir(parents=True, exist_ok=True)
        (dist_dir / "assets" / "generated").mkdir(parents=True, exist_ok=True)
        content_dir.mkdir(parents=True, exist_ok=True)

        (dist_dir / "assets" / "style.css").write_text(BLOG_CSS, encoding="utf-8")

        # Copy generated images if present
        gen_src = self.root_dir / "site" / "assets" / "generated"
        if gen_src.exists():
            for file in gen_src.iterdir():
                if file.is_file():
                    shutil.copy2(file, dist_dir / "assets" / "generated" / file.name)

        articles = [
            a
            for a in self.db.list_articles()
            if a.status == "published" or (include_approved and a.status == "approved")
        ]

        base_url = self.settings.brand.base_url.rstrip("/")
        brand = self.settings.brand.name
        tagline = self.settings.brand.tagline
        urls_for_sitemap: list[str] = [
            f"{base_url}/",
            f"{base_url}/about.html",
            f"{base_url}/contact.html",
            f"{base_url}/privacy-policy.html",
            f"{base_url}/editorial-standards.html",
            f"{base_url}/categories/index.html",
        ]

        search_index: list[dict[str, str]] = []
        by_category: dict[str, list[Article]] = {}
        by_tag: dict[str, list[Article]] = {}

        for art in articles:
            # 1. Write portable Markdown source
            md_frontmatter = (
                f"---\ntitle: \"{art.title}\"\nslug: \"{art.slug}\"\n"
                f"description: \"{art.meta_description}\"\ncategory: \"{art.category}\"\n"
                f"primary_keyword: \"{art.primary_keyword}\"\n---\n\n"
            )
            (content_dir / f"{art.slug}.md").write_text(md_frontmatter + art.markdown_body, encoding="utf-8")

            # 2. Render HTML article
            rendered = MarkdownIt().render(art.markdown_body)
            cat_slug = _slug_part(art.category)
            canonical = f"{base_url}/articles/{art.slug}.html"
            og_img = f"{base_url}{art.image_path}" if art.image_path else ""
            hero_img = (
                f'<img src="{html.escape(art.image_path)}" alt="{html.escape(art.image_alt)}" loading="eager" width="1200" height="630" />'
                if art.image_path
                else ""
            )
            related = [a for a in articles if a.slug != art.slug][:3]
            related_html = "".join(
                f'<li><a href="/articles/{r.slug}.html">{html.escape(r.title)}</a></li>' for r in related
            )
            cta_match = re.search(
                r'<a class="zazzle-cta-card" href="([^"]+)" data-article="([^"]+)" data-product-id="([^"]+)" data-affiliate="([^"]+)" target="_blank" (rel="[^"]+")>',
                rendered,
            )
            top_cta_html = ""
            bottom_cta_html = ""
            if cta_match:
                c_href, c_art, c_pid, c_aff, c_rel = cta_match.groups()
                top_cta_html = (
                    f'<div class="top-cta-bar">'
                    f'<a class="zazzle-cta-card" href="{c_href}" data-article="{c_art}" data-product-id="{c_pid}" data-affiliate="{c_aff}" target="_blank" {c_rel}>Shop &amp; Customize on Zazzle &rarr;</a>'
                    f'<a class="cta-secondary-btn" href="#gift-picks">Jump to Curated Picks &darr;</a>'
                    f"</div>"
                )
                bottom_cta_html = (
                    f'<section class="bottom-cta-box">'
                    f"<h3>Ready to Customize This Gift on Zazzle?</h3>"
                    f"<p>Preview live personalization, finishes, and current US pricing directly on Zazzle before ordering.</p>"
                    f'<div class="bottom-cta-box-actions">'
                    f'<a class="zazzle-cta-card" href="{c_href}" data-article="{c_art}" data-product-id="{c_pid}" data-affiliate="{c_aff}" target="_blank" {c_rel}>Customize &amp; Order on Zazzle &rarr;</a>'
                    f'<a class="cta-secondary-btn" href="/">Explore All Gift Guides &rarr;</a>'
                    f"</div></section>"
                )
            rendered_with_anchor = rendered.replace('<div class="rec-card">', '<div id="gift-picks" class="rec-card">', 1)
            article_html = f"""
            <div class="article-wrap">
              <div class="breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/categories/{cat_slug}.html">{html.escape(art.category)}</a> &rsaquo; {html.escape(art.title)}</div>
              {hero_img}
              {top_cta_html}
              {rendered_with_anchor}
              {bottom_cta_html}
              <section><h3>More Gift &amp; Shopping Guides</h3><ul>{related_html or '<li><a href="/">Browse All Guides</a></li>'}</ul></section>
            </div>
            """
            json_ld = [
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": art.title,
                    "description": art.meta_description,
                    "author": {"@type": "Organization", "name": brand},
                    "mainEntityOfPage": canonical,
                },
                {
                    "@context": "https://schema.org",
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{base_url}/"},
                        {"@type": "ListItem", "position": 2, "name": art.category, "item": f"{base_url}/categories/{cat_slug}.html"},
                        {"@type": "ListItem", "position": 3, "name": art.title, "item": canonical},
                    ],
                },
            ]
            (dist_dir / "articles" / f"{art.slug}.html").write_text(
                _base_template(
                    art.title,
                    art.meta_description,
                    canonical,
                    brand,
                    tagline,
                    article_html,
                    og_img,
                    json_ld,
                    ga4_id=self.settings.brand.ga4_measurement_id,
                    gsc_token=self.settings.brand.gsc_verification_token,
                ),
                encoding="utf-8",
            )
            urls_for_sitemap.append(canonical)
            search_index.append(
                {
                    "title": art.title,
                    "slug": art.slug,
                    "category": art.category,
                    "description": art.meta_description,
                }
            )
            by_category.setdefault(art.category, []).append(art)
            for tag in art.tags:
                by_tag.setdefault(tag, []).append(art)

        # 3. Category pages
        cat_cards = []
        for cat_name, cat_arts in by_category.items():
            cslug = _slug_part(cat_name)
            cat_url = f"{base_url}/categories/{cslug}.html"
            urls_for_sitemap.append(cat_url)
            items = "".join(
                f'<li><a href="/articles/{a.slug}.html">{html.escape(a.title)}</a></li>' for a in cat_arts
            )
            (dist_dir / "categories" / f"{cslug}.html").write_text(
                _base_template(
                    f"{cat_name} Guides | {brand}",
                    f"Browse curated {cat_name} shopping guides and Zazzle gift ideas.",
                    cat_url,
                    brand,
                    tagline,
                    f"<h1>{html.escape(cat_name)}</h1><ul>{items}</ul>",
                ),
                encoding="utf-8",
            )
            cat_cards.append(f'<li><a href="/categories/{cslug}.html">{html.escape(cat_name)} ({len(cat_arts)})</a></li>')

        (dist_dir / "categories" / "index.html").write_text(
            _base_template(
                f"Categories | {brand}",
                f"Explore all shopping guide categories on {brand}.",
                f"{base_url}/categories/index.html",
                brand,
                tagline,
                f"<h1>Categories</h1><ul>{''.join(cat_cards) or '<li>No published categories yet.</li>'}</ul>",
            ),
            encoding="utf-8",
        )

        # 4. Tag pages
        for tag_name, tag_arts in by_tag.items():
            tslug = _slug_part(tag_name)
            turl = f"{base_url}/tags/{tslug}.html"
            urls_for_sitemap.append(turl)
            items = "".join(
                f'<li><a href="/articles/{a.slug}.html">{html.escape(a.title)}</a></li>' for a in tag_arts
            )
            (dist_dir / "tags" / f"{tslug}.html").write_text(
                _base_template(
                    f"Tag: {tag_name} | {brand}",
                    f"Articles tagged {tag_name} on {brand}.",
                    turl,
                    brand,
                    tagline,
                    f"<h1>#{html.escape(tag_name)}</h1><ul>{items}</ul>",
                ),
                encoding="utf-8",
            )

        # 5. Homepage with internal search
        cards_html = "".join(
            f"""
            <article class="card" data-search="{html.escape((a.title + ' ' + a.category + ' ' + a.primary_keyword).lower())}">
              {f'<img src="{html.escape(a.image_path)}" alt="{html.escape(a.image_alt)}" loading="lazy" width="1200" height="630" />' if a.image_path else ''}
              <div class="card-body">
                <span class="badge">{html.escape(a.category)}</span>
                <h2><a href="/articles/{a.slug}.html">{html.escape(a.title)}</a></h2>
                <p>{html.escape(a.meta_description)}</p>
              </div>
            </article>
            """
            for a in articles
        )
        home_body = f"""
        <section class="hero">
          <h1>{html.escape(brand)}</h1>
          <p>{html.escape(tagline)}</p>
          <input id="siteSearch" class="search-box" type="search" placeholder="Search gift guides, cards, mugs, tees..." aria-label="Search guides" />
        </section>
        <section class="grid" id="articleGrid">{cards_html or '<p>No published articles yet. Approve drafts in the dashboard to publish.</p>'}</section>
        <script>
        const inp=document.getElementById('siteSearch');
        if(inp){{inp.addEventListener('input',()=>{{const q=inp.value.toLowerCase().trim();document.querySelectorAll('#articleGrid .card').forEach(c=>{{c.style.display=!q||c.dataset.search.includes(q)?'flex':'none';}});}});}}
        </script>
        """
        (dist_dir / "index.html").write_text(
            _base_template(
                f"{brand} | Curated Gift Guides & Zazzle Finds",
                tagline,
                f"{base_url}/",
                brand,
                tagline,
                home_body,
                ga4_id=self.settings.brand.ga4_measurement_id,
                gsc_token=self.settings.brand.gsc_verification_token,
            ),
            encoding="utf-8",
        )

        # 6. AdSense-Ready Legal & Trust Pages
        legal_pages = {
            "about.html": (
                f"About | {brand}",
                f"Learn about {brand} and our editorial curation process.",
                f"<h1>About {html.escape(brand)}</h1><p>{html.escape(brand)} publishes original US-focused shopping guides, customization walkthroughs, and curated gift ideas featuring independent designs hosted on Zazzle.</p>",
            ),
            "contact.html": (
                f"Contact | {brand}",
                f"Contact {brand} editorial team.",
                f"<h1>Contact Us</h1><p>Questions, corrections, or partnership inquiries? Email us at <a href=\"mailto:{html.escape(self.settings.brand.contact_email)}\">{html.escape(self.settings.brand.contact_email)}</a>.</p>",
            ),
            "privacy-policy.html": (
                f"Privacy & Cookie Policy | {brand}",
                "Privacy policy, cookies, analytics, and advertising disclosure.",
                f"<h1>Privacy &amp; Cookie Policy</h1><p>{html.escape(brand)} respects visitor privacy. We do not sell personal data. When analytics or third-party advertising networks (such as Google AdSense) are enabled, cookies may be used to measure aggregate traffic or display relevant ads in accordance with applicable law.</p>",
            ),
            "editorial-standards.html": (
                f"Editorial Standards & Disclosure | {brand}",
                "Our commitment to accurate product guides and transparent disclosures.",
                "<h1>Editorial Standards &amp; Affiliate Disclosure</h1><p>Every guide is reviewed before publication. We never fabricate customer reviews, star ratings, fake discounts, or unverified shipping guarantees. When eligible affiliate links are used, they are clearly marked and disclosed.</p>",
            ),
        }
        for fname, (ptitle, pdesc, pbody) in legal_pages.items():
            (dist_dir / fname).write_text(
                _base_template(ptitle, pdesc, f"{base_url}/{fname}", brand, tagline, pbody),
                encoding="utf-8",
            )

        # 7. Sitemap.xml & Robots.txt
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        url_nodes = "\n".join(
            f"  <url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>"
            for u in dict.fromkeys(urls_for_sitemap)
        )
        sitemap_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{url_nodes}\n</urlset>\n'
        (dist_dir / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
        (dist_dir / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n",
            encoding="utf-8",
        )
        (dist_dir / "search-index.json").write_text(json.dumps(search_index, indent=2), encoding="utf-8")

        # 8. RSS 2.0 Feed for Pinterest / Flipboard / Feed Syndication
        rss_items = "\n".join(
            f"""    <item>
      <title>{html.escape(a.title)}</title>
      <link>{html.escape(f"{base_url}/articles/{a.slug}.html")}</link>
      <guid>{html.escape(f"{base_url}/articles/{a.slug}.html")}</guid>
      <description>{html.escape(a.meta_description)}</description>
    </item>"""
            for a in articles
        )
        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{html.escape(brand)} — Curated US Gift Guides</title>
    <link>{html.escape(base_url)}/</link>
    <description>{html.escape(tagline)}</description>
    <language>en-us</language>
{rss_items}
  </channel>
</rss>
"""
        (dist_dir / "rss.xml").write_text(rss_xml, encoding="utf-8")

        return {
            "dist_dir": str(dist_dir),
            "articles_built": len(articles),
            "sitemap_urls": len(urls_for_sitemap),
        }
