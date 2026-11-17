"""SQLite database layer with deduplication, agent logging, click tracking, and safe backups."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import Article, KeywordOpportunity, PinterestPin, Product, TaskResult, utc_now_iso

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    target_customer TEXT NOT NULL,
    design_style TEXT NOT NULL,
    occasion_season TEXT NOT NULL,
    price_usd REAL,
    selling_points_json TEXT NOT NULL,
    search_terms_json TEXT NOT NULL,
    image_url TEXT,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    market TEXT NOT NULL,
    search_intent TEXT NOT NULL,
    source TEXT NOT NULL,
    search_demand_score REAL NOT NULL,
    buyer_intent_score REAL NOT NULL,
    competition_difficulty_score REAL NOT NULL,
    product_relevance_score REAL NOT NULL,
    seasonal_opportunity_score REAL NOT NULL,
    ranking_feasibility_score REAL NOT NULL,
    total_score REAL NOT NULL,
    search_volume_label TEXT NOT NULL,
    keyword_difficulty_label TEXT NOT NULL,
    matched_product_id INTEGER,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    meta_description TEXT NOT NULL,
    content_format TEXT NOT NULL,
    search_intent TEXT NOT NULL,
    primary_keyword TEXT NOT NULL,
    secondary_keywords_json TEXT NOT NULL,
    semantic_variations_json TEXT NOT NULL,
    category TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    markdown_body TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    matched_product_ids_json TEXT NOT NULL,
    image_path TEXT,
    image_alt TEXT NOT NULL,
    internal_links_json TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    affiliate_disclosure_included INTEGER NOT NULL,
    qa_score INTEGER NOT NULL,
    qa_passed INTEGER NOT NULL,
    qa_notes_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT
);

CREATE TABLE IF NOT EXISTS pinterest_pins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_slug TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    hashtags_json TEXT NOT NULL,
    image_concept TEXT NOT NULL,
    image_path TEXT,
    destination_url TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(article_slug, title)
);

CREATE TABLE IF NOT EXISTS click_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    article_slug TEXT NOT NULL,
    product_id INTEGER,
    is_affiliate INTEGER NOT NULL DEFAULT 0,
    destination_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task TEXT NOT NULL,
    status TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    errors_json TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 1,
    error_message TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(run_id, step_name)
);
"""


class Database:
    """Central SQLite repository preventing duplicate work and tracking all agent activity."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def backup(self, backup_dir: Path) -> Path:
        """Create an atomic SQLite backup file."""
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = utc_now_iso().replace(":", "-").split(".")[0]
        dest = backup_dir / f"autopilot_backup_{stamp}.db"
        with self._connect() as src, sqlite3.connect(dest) as dst:
            src.backup(dst)
        return dest

    def upsert_product(self, product: Product) -> int:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO products (
                    name, category, url, description, tags_json, target_customer,
                    design_style, occasion_season, price_usd, selling_points_json,
                    search_terms_json, image_url, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    description=excluded.description,
                    tags_json=excluded.tags_json,
                    target_customer=excluded.target_customer,
                    design_style=excluded.design_style,
                    occasion_season=excluded.occasion_season,
                    price_usd=COALESCE(excluded.price_usd, products.price_usd),
                    selling_points_json=excluded.selling_points_json,
                    search_terms_json=excluded.search_terms_json,
                    image_url=COALESCE(excluded.image_url, products.image_url)
                """,
                (
                    product.name,
                    product.category,
                    product.url,
                    product.description,
                    json.dumps(product.tags),
                    product.target_customer,
                    product.design_style,
                    product.occasion_season,
                    product.price_usd,
                    json.dumps(product.selling_points),
                    json.dumps(product.search_terms),
                    product.image_url,
                    product.source,
                    product.created_at,
                ),
            )
            row = conn.execute("SELECT id FROM products WHERE url = ?", (product.url,)).fetchone()
            return int(row["id"])

    def list_products(self) -> list[Product]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
        return [
            Product(
                id=r["id"],
                name=r["name"],
                category=r["category"],
                url=r["url"],
                description=r["description"],
                tags=json.loads(r["tags_json"]),
                target_customer=r["target_customer"],
                design_style=r["design_style"],
                occasion_season=r["occasion_season"],
                price_usd=r["price_usd"],
                selling_points=json.loads(r["selling_points_json"]),
                search_terms=json.loads(r["search_terms_json"]),
                image_url=r["image_url"],
                source=r["source"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def upsert_keyword(self, kw: KeywordOpportunity) -> int:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO keywords (
                    keyword, market, search_intent, source, search_demand_score,
                    buyer_intent_score, competition_difficulty_score, product_relevance_score,
                    seasonal_opportunity_score, ranking_feasibility_score, total_score,
                    search_volume_label, keyword_difficulty_label, matched_product_id,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(keyword) DO UPDATE SET
                    total_score=excluded.total_score,
                    matched_product_id=COALESCE(excluded.matched_product_id, keywords.matched_product_id)
                """,
                (
                    kw.keyword.lower().strip(),
                    kw.market,
                    kw.search_intent,
                    kw.source,
                    kw.search_demand_score,
                    kw.buyer_intent_score,
                    kw.competition_difficulty_score,
                    kw.product_relevance_score,
                    kw.seasonal_opportunity_score,
                    kw.ranking_feasibility_score,
                    kw.total_score,
                    kw.search_volume_label,
                    kw.keyword_difficulty_label,
                    kw.matched_product_id,
                    kw.status,
                    kw.created_at,
                ),
            )
            row = conn.execute(
                "SELECT id FROM keywords WHERE keyword = ?", (kw.keyword.lower().strip(),)
            ).fetchone()
            return int(row["id"])

    def list_keywords(self, limit: int = 100) -> list[KeywordOpportunity]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM keywords ORDER BY total_score DESC, id ASC LIMIT ?", (limit,)
            ).fetchall()
        return [
            KeywordOpportunity(
                id=r["id"],
                keyword=r["keyword"],
                market=r["market"],
                search_intent=r["search_intent"],
                source=r["source"],
                search_demand_score=r["search_demand_score"],
                buyer_intent_score=r["buyer_intent_score"],
                competition_difficulty_score=r["competition_difficulty_score"],
                product_relevance_score=r["product_relevance_score"],
                seasonal_opportunity_score=r["seasonal_opportunity_score"],
                ranking_feasibility_score=r["ranking_feasibility_score"],
                total_score=r["total_score"],
                search_volume_label=r["search_volume_label"],
                keyword_difficulty_label=r["keyword_difficulty_label"],
                matched_product_id=r["matched_product_id"],
                status=r["status"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def upsert_article(self, article: Article) -> int:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO articles (
                    slug, title, meta_description, content_format, search_intent,
                    primary_keyword, secondary_keywords_json, semantic_variations_json,
                    category, tags_json, markdown_body, word_count, matched_product_ids_json,
                    image_path, image_alt, internal_links_json, sources_json,
                    affiliate_disclosure_included, qa_score, qa_passed, qa_notes_json,
                    status, created_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title=excluded.title,
                    meta_description=excluded.meta_description,
                    markdown_body=excluded.markdown_body,
                    word_count=excluded.word_count,
                    image_path=COALESCE(excluded.image_path, articles.image_path),
                    image_alt=excluded.image_alt,
                    internal_links_json=excluded.internal_links_json,
                    qa_score=excluded.qa_score,
                    qa_passed=excluded.qa_passed,
                    qa_notes_json=excluded.qa_notes_json,
                    status=CASE WHEN articles.status = 'published' THEN 'published' ELSE excluded.status END,
                    published_at=COALESCE(articles.published_at, excluded.published_at)
                """,
                (
                    article.slug,
                    article.title,
                    article.meta_description,
                    article.content_format,
                    article.search_intent,
                    article.primary_keyword,
                    json.dumps(article.secondary_keywords),
                    json.dumps(article.semantic_variations),
                    article.category,
                    json.dumps(article.tags),
                    article.markdown_body,
                    article.word_count,
                    json.dumps(article.matched_product_ids),
                    article.image_path,
                    article.image_alt,
                    json.dumps(article.internal_links),
                    json.dumps(article.sources),
                    int(article.affiliate_disclosure_included),
                    article.qa_score,
                    int(article.qa_passed),
                    json.dumps(article.qa_notes),
                    article.status,
                    article.created_at,
                    article.published_at,
                ),
            )
            row = conn.execute("SELECT id FROM articles WHERE slug = ?", (article.slug,)).fetchone()
            return int(row["id"])

    def list_articles(self, status: str | None = None) -> list[Article]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM articles WHERE status = ? ORDER BY id DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM articles ORDER BY id DESC").fetchall()
        return [
            Article(
                id=r["id"],
                slug=r["slug"],
                title=r["title"],
                meta_description=r["meta_description"],
                content_format=r["content_format"],
                search_intent=r["search_intent"],
                primary_keyword=r["primary_keyword"],
                secondary_keywords=json.loads(r["secondary_keywords_json"]),
                semantic_variations=json.loads(r["semantic_variations_json"]),
                category=r["category"],
                tags=json.loads(r["tags_json"]),
                markdown_body=r["markdown_body"],
                word_count=r["word_count"],
                matched_product_ids=json.loads(r["matched_product_ids_json"]),
                image_path=r["image_path"],
                image_alt=r["image_alt"],
                internal_links=json.loads(r["internal_links_json"]),
                sources=json.loads(r["sources_json"]),
                affiliate_disclosure_included=bool(r["affiliate_disclosure_included"]),
                qa_score=r["qa_score"],
                qa_passed=bool(r["qa_passed"]),
                qa_notes=json.loads(r["qa_notes_json"]),
                status=r["status"],
                created_at=r["created_at"],
                published_at=r["published_at"],
            )
            for r in rows
        ]

    def set_article_status(self, slug: str, status: str) -> None:
        pub_at = utc_now_iso() if status == "published" else None
        with self._connect() as conn:
            conn.execute(
                "UPDATE articles SET status = ?, published_at = COALESCE(?, published_at) WHERE slug = ?",
                (status, pub_at, slug),
            )

    def upsert_pin(self, pin: PinterestPin) -> int:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pinterest_pins (
                    article_slug, title, description, hashtags_json,
                    image_concept, image_path, destination_url, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(article_slug, title) DO UPDATE SET
                    description=excluded.description,
                    image_path=COALESCE(excluded.image_path, pinterest_pins.image_path),
                    destination_url=excluded.destination_url
                """,
                (
                    pin.article_slug,
                    pin.title,
                    pin.description,
                    json.dumps(pin.hashtags),
                    pin.image_concept,
                    pin.image_path,
                    pin.destination_url,
                    pin.status,
                    pin.created_at,
                ),
            )
            row = conn.execute(
                "SELECT id FROM pinterest_pins WHERE article_slug = ? AND title = ?",
                (pin.article_slug, pin.title),
            ).fetchone()
            return int(row["id"])

    def list_pins(self) -> list[PinterestPin]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM pinterest_pins ORDER BY id DESC").fetchall()
        return [
            PinterestPin(
                id=r["id"],
                article_slug=r["article_slug"],
                title=r["title"],
                description=r["description"],
                hashtags=json.loads(r["hashtags_json"]),
                image_concept=r["image_concept"],
                image_path=r["image_path"],
                destination_url=r["destination_url"],
                status=r["status"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def record_click(
        self,
        event_type: str,
        article_slug: str,
        product_id: int | None = None,
        is_affiliate: bool = False,
        destination_url: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO click_events (event_type, article_slug, product_id, is_affiliate, destination_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_type, article_slug, product_id, int(is_affiliate), destination_url, utc_now_iso()),
            )

    def log_agent_result(self, result: TaskResult) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_logs (
                    agent_name, task, status, input_json, output_json,
                    errors_json, recommendations_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.agent_name,
                    result.task,
                    result.status,
                    json.dumps(result.input_summary),
                    json.dumps(result.output_summary),
                    json.dumps(result.errors),
                    json.dumps(result.recommendations),
                    result.timestamp,
                ),
            )

    def list_agent_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def record_job_step(self, run_id: str, step_name: str, status: str, error_message: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO job_runs (run_id, step_name, status, attempts, error_message, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(run_id, step_name) DO UPDATE SET
                    status=excluded.status,
                    attempts=job_runs.attempts + 1,
                    error_message=excluded.error_message,
                    updated_at=excluded.updated_at
                """,
                (run_id, step_name, status, error_message, utc_now_iso()),
            )

    def get_completed_steps(self, run_id: str) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT step_name FROM job_runs WHERE run_id = ? AND status = 'completed'", (run_id,)
            ).fetchall()
        return {r["step_name"] for r in rows}

    def get_dashboard_metrics(self) -> dict[str, Any]:
        with self._connect() as conn:
            total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            articles_total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            articles_published = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE status = 'published'"
            ).fetchone()[0]
            articles_awaiting = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE status IN ('draft', 'awaiting_approval', 'approved')"
            ).fetchone()[0]
            total_keywords = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
            total_pins = conn.execute("SELECT COUNT(*) FROM pinterest_pins").fetchone()[0]
            outbound_clicks = conn.execute(
                "SELECT COUNT(*) FROM click_events WHERE event_type = 'outbound_product'"
            ).fetchone()[0]
            affiliate_clicks = conn.execute(
                "SELECT COUNT(*) FROM click_events WHERE is_affiliate = 1"
            ).fetchone()[0]
            top_articles = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT article_slug, COUNT(*) as clicks
                    FROM click_events
                    GROUP BY article_slug
                    ORDER BY clicks DESC
                    LIMIT 5
                    """
                ).fetchall()
            ]
        return {
            "total_products": total_products,
            "articles_generated": articles_total,
            "articles_published": articles_published,
            "articles_awaiting_approval": articles_awaiting,
            "target_keywords": total_keywords,
            "pinterest_pins": total_pins,
            "organic_traffic": "Connect GA4 / Google Search Console for verified sessions",
            "product_outbound_clicks": outbound_clicks,
            "affiliate_clicks": affiliate_clicks,
            "verified_sales_and_commissions": "Unconnected (verify via Zazzle Earnings dashboard)",
            "top_articles": top_articles,
        }
