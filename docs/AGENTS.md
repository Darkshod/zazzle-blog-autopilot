# Agent Architecture Documentation

All 12 agents inherit from `BaseAgent` (`src/zazzle_blog_autopilot/agents/__init__.py`) and log every execution as a structured `TaskResult` into the `agent_logs` table in SQLite.

1. **Manager Agent (`manager.py`)**: Orchestrates the end-to-end daily pipeline, tracks step state in `job_runs`, and supports resume-after-interruption and retry.
2. **Product Research Agent (`product_research.py`)**: Imports products from CSV or manual URLs, validates `https://www.zazzle.*` domains, and organizes metadata without scraping restricted pages.
3. **Market Research Agent (`market_research.py`)**: Identifies US seasonal and category opportunities and optionally queries the free public Google Suggest endpoint.
4. **Keyword Research Agent (`keyword_research.py`)**: Scores opportunities using the weighted formula (`25%` demand, `25%` buyer intent, `20%` competition difficulty, `15%` product relevance, `10%` seasonal opportunity, `5%` ranking feasibility) and marks unavailable volumes as estimates/unknown.
5. **Competitor Analysis Agent (`competitor_analysis.py`)**: Maps keywords to 8 structured content formats and differentiation angles without copying competitor text.
6. **SEO Content Agent (`seo_content.py`)**: Writes >=750-word US-English articles with H1/H2/H3 hierarchy, FAQs, sources, internal links, reusable product cards, and disclosures.
7. **Editorial QA Agent (`editorial_qa.py`)**: Enforces minimum word count, meta description length, keyword density limits, duplicate title checks, and blocks fabricated reviews/ratings/discounts.
8. **Image Creation Agent (`image_creation.py`)**: Renders `1200x630` Open Graph blog covers and `1000x1500` 2:3 Pinterest graphics via Pillow, writing `image_manifest.json` with alt text and license info.
9. **Conversion Optimization Agent (`conversion.py`)**: Generates CTA cards and gates affiliate query parameters strictly behind `zazzle_affiliate_approved=true`.
10. **Pinterest Distribution Agent (`pinterest_distribution.py`)**: Creates 3 Pin concepts per article in `pending_approval` status.
11. **Analytics Agent (`analytics.py`)**: Reports DB metrics, outbound/affiliate click counts, and content refresh candidates.
12. **Technical SEO Doctor (`technical_seo.py`)**: Audits `dist/` for broken internal links, duplicate titles, missing canonicals, invalid `sitemap.xml`, missing `robots.txt`, and malformed JSON-LD.
