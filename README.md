# Zazzle Blog Autopilot

**Autonomous SEO blogging and organic sales engine for Zazzle products.**

Built for **$0/month** using Python 3.11+, SQLite, FastAPI, static HTML/Markdown generation, and GitHub Actions cloud scheduling.

## Features

- **12 Specialized Agents**: Product Intelligence, Market Research, 6-Factor Keyword Scoring, Competitor Gap Analysis, SEO Content Writer, Editorial QA, Image & Pinterest Graphic Generator, Conversion Funnel Builder, Pinterest Distribution, Analytics, Technical SEO Doctor, and Manager Orchestrator.
- **Zero-Cost Static Blog**: Generates portable Markdown (`content/articles/*.md`) and fast, mobile-first HTML (`dist/`) with `sitemap.xml`, `robots.txt`, Open Graph tags, canonical URLs, `Article` + `BreadcrumbList` JSON-LD, client-side search, category/tag archives, and AdSense-ready legal pages.
- **Functional Control Dashboard**: FastAPI web UI (`127.0.0.1:8080`) where every action button executes real agent pipelines, approval queues, SEO audits, and report exports.
- **Human-in-the-Loop & Policy Safe**: Never fabricates search volumes, product prices, reviews, ratings, or discounts; requires approval before publishing articles or Pinterest pins; separates ordinary product links from affiliate links.

## Quick Start (Windows 11 / Linux / macOS)

```bash
git clone https://github.com/Darkshod/zazzle-blog-autopilot.git
cd zazzle-blog-autopilot
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### 1. Run Tests
```bash
python -m pytest -v
```

### 2. Run the Full 12-Agent Pipeline
```bash
python -m zazzle_blog_autopilot.cli run-all --csv data/sample_products.csv --max-articles 3
python -m zazzle_blog_autopilot.cli approve-all
```

### 3. Launch the Dashboard
```bash
python -m zazzle_blog_autopilot.cli dashboard
```
Open `http://127.0.0.1:8080` in your browser.

## Repository Structure

- `config/settings.yaml` — Brand identity, market focus (`US` primary; `GB`, `CA`, `AU` secondary), scoring weights, and daily schedule.
- `data/sample_products.csv` — Sample Zazzle product catalog import template.
- `src/zazzle_blog_autopilot/agents/` — All 12 specialized agents.
- `src/zazzle_blog_autopilot/site_builder.py` — Portable Markdown + static HTML generator.
- `src/zazzle_blog_autopilot/dashboard.py` — FastAPI dashboard and REST action endpoints.
- `.github/workflows/daily_autopilot.yml` — Cloud-hosted daily schedule (laptop does not need to stay on).
- `scripts/register_windows_schedule.ps1` — Optional Windows 11 local Task Scheduler setup.

## License

MIT License — see [LICENSE](LICENSE).
