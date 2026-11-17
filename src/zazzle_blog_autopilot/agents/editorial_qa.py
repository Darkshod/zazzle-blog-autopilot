"""Editorial QA Agent — enforces SEO structure, anti-stuffing, anti-fabrication, and deduplication."""

from __future__ import annotations

import re
from typing import Any

from ..models import Article, TaskResult
from . import BaseAgent

BANNED_FABRICATED_PHRASES = (
    "5 out of 5 stars",
    "verified customer review",
    "guaranteed overnight shipping",
    "limited time 50% off",
    "act now before stock runs out",
)


def evaluate_article_quality(
    article: Article,
    all_titles: list[str],
    min_words: int = 750,
    max_density_pct: float = 2.8,
) -> tuple[int, bool, list[str]]:
    notes: list[str] = []
    score = 100
    body_lower = article.markdown_body.lower()

    if article.word_count < min_words:
        notes.append(f"Thin content: {article.word_count} words < {min_words} minimum.")
        score -= 30

    if not (110 <= len(article.meta_description) <= 165):
        notes.append(f"Meta description length ({len(article.meta_description)}) should be 110-165 chars.")
        score -= 10

    if "# " not in article.markdown_body or "## " not in article.markdown_body:
        notes.append("Missing H1/H2 heading hierarchy.")
        score -= 20

    # Keyword density check
    words = re.findall(r"\b\w+\b", body_lower)
    kw_tokens = article.primary_keyword.lower().strip()
    occurrences = body_lower.count(kw_tokens) if kw_tokens else 0
    kw_word_len = max(1, len(kw_tokens.split()))
    density = (occurrences * kw_word_len / max(1, len(words))) * 100.0
    if density > max_density_pct:
        notes.append(f"Keyword stuffing detected ({density:.2f}% > {max_density_pct}%).")
        score -= 20

    # Fabricated claims check
    for banned in BANNED_FABRICATED_PHRASES:
        if banned in body_lower:
            notes.append(f"Banned unverified claim phrase found: '{banned}'.")
            score -= 35

    if "disclosure:" not in body_lower:
        notes.append("Missing affiliate/editorial disclosure.")
        score -= 15

    # Duplicate title check
    title_count = sum(1 for t in all_titles if t.lower().strip() == article.title.lower().strip())
    if title_count > 1:
        notes.append("Duplicate article title detected.")
        score -= 25

    score = max(0, score)
    passed = score >= 80 and not any("Thin content" in n or "Banned" in n or "Duplicate" in n for n in notes)
    return score, passed, notes


class EditorialQAAgent(BaseAgent):
    name = "editorial_qa"

    def execute(self, **kwargs: Any) -> TaskResult:
        articles = self.db.list_articles()
        all_titles = [a.title for a in articles]
        passed_count = 0
        failed_slugs: list[str] = []

        for article in articles:
            score, passed, notes = evaluate_article_quality(
                article,
                all_titles=all_titles,
                min_words=self.settings.publishing.min_word_count,
                max_density_pct=self.settings.publishing.max_keyword_density_pct,
            )
            article.qa_score = score
            article.qa_passed = passed
            article.qa_notes = notes
            if article.status == "draft" and passed:
                article.status = "awaiting_approval"
            elif article.status == "draft" and not passed:
                article.status = "rejected"
                failed_slugs.append(article.slug)
            if passed:
                passed_count += 1
            self.db.upsert_article(article)

        return TaskResult(
            agent_name=self.name,
            task="run_editorial_and_seo_qa",
            status="warning" if failed_slugs else "success",
            input_summary={"articles_checked": len(articles)},
            output_summary={"passed": passed_count, "rejected": failed_slugs},
            recommendations=["Review articles in 'awaiting_approval' before publishing."],
        )
