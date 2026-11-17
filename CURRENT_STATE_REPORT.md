# DARKSHOD — Current State Audit & Prioritized Roadmap

**Date:** 2026-11-17  
**Repositories Inspected:**
- Main Engine: `https://github.com/Darkshod/zazzle-blog-autopilot` (`main` @ `d9e6517`)
- Live Website: `https://github.com/Darkshod/darkshod.github.io` (`main` @ `2eb1979`, live at `https://darkshod.github.io/`)

---

## 1. Completed Functionality
- **SQLite Core (`db.py`):** Persistent WAL-mode database (`products`, `keywords`, `articles`, `pinterest_pins`, `click_events`, `agent_logs`, `job_runs`) with deduplication and atomic `backup()`.
- **12 Existing Agents:** `ManagerAgent`, `ProductResearchAgent`, `MarketResearchAgent`, `KeywordResearchAgent`, `CompetitorAnalysisAgent`, `SEOContentAgent`, `EditorialQAAgent`, `ImageCreationAgent`, `ConversionOptimizationAgent`, `PinterestDistributionAgent`, `AnalyticsAgent`, `TechnicalSEODoctor`.
- **Static Site (`site_builder.py`):** `13` published SEO articles, `64` sitemap URLs, `robots.txt`, canonical tags, Open Graph, `Article` + `BreadcrumbList` JSON-LD, category/tag archives, client-side search, responsive `.rec-card` product CTAs with real lifestyle photography, and AdSense trust pages (`about.html`, `contact.html`, `privacy-policy.html`, `editorial-standards.html`).
- **Live Site Verification (`scripts/audit_live_site.py`):** `healthy: true`, `13` articles `HTTP 200`, `28` checked images `HTTP 200`, `0` issues.
- **Automation:** Daily (`daily_autopilot.yml`) and Weekly (`weekly_reports.yml`) GitHub Actions workflows + Windows 11 local scheduler script.

## 2. Incomplete Functionality, Disconnected Integrations & Technical Debt
- **Brand Identity Mismatch:** `config/settings.yaml` currently uses `GRIMORA11` instead of `DARKSHOD` for the master publishing brand.
- **Missing 5 Specialist Agents (12 of 17 built):** Missing dedicated `SEO Strategy`, `Monetization`, `Financial Reporting`, `Security & Compliance`, and `System Doctor` agents, plus a persistent executive `tasks` table with unique task IDs and `Emergency Stop` control.
- **Disconnected Integrations (Missing Credentials):**
  - `GSC_ACCESS_TOKEN` / `GSC_CREDENTIALS_PATH`: `NOT CONNECTED`
  - `GA4_MEASUREMENT_ID`: `NOT CONNECTED`
  - `PINTEREST_ACCESS_TOKEN` / `PINTEREST_BOARD_ID`: `NOT CONNECTED`
- **Financial Accounting Separation:** Missing dedicated ledger separating product sales, affiliate commissions, ad revenue, sponsorships, operating expenses, and net profit (currently all unverified).
- **Monthly Automation:** Daily and Weekly GitHub Actions exist, but Monthly full business review workflow is missing.

## 3. Top 10 Business Bottlenecks
1. **Unconnected Google Search Console (`GSC_ACCESS_TOKEN`):** Cannot measure actual Google impressions, clicks, CTR, or indexing status yet.
2. **Unconnected GA4 / Privacy Analytics Endpoint:** Outbound Zazzle clicks on the static site are not yet streaming to a live collector.
3. **Unconnected Pinterest API v5 (`PINTEREST_ACCESS_TOKEN`):** 20 prioritized pins (`reports/pinterest_top20_queue.json`) await human approval & token setup.
4. **Commercial Hosting Constraint for AdSense:** GitHub Pages restricts purely commercial/ad-monetized sites; migrating `dist/` to **Cloudflare Pages** (free) is needed before applying for AdSense.
5. **Morocco PayPal Withdrawal Friction:** Zazzle supports PayPal (`$50` min) and physical checks (`$100` min), NOT Payoneer/Wise/SWIFT; Moroccan PayPal USD withdrawal setup must be verified before scaling affiliate reliance.
6. **5 Content-Gap Drafts Awaiting Approval:** 5 non-cannibalizing drafts were generated in Phase 3 and sit in `awaiting_approval`.
7. **Missing Executive Task & Financial Ledger:** Need persistent task IDs, impact/feasibility/risk scoring, and separate revenue/expense accounting.
8. **Missing Security & Compliance Audit Agent:** Need automated pre-deploy scans for accidental secrets, unapproved claims, and missing disclosures.
9. **Incomplete Category Coverage:** Need US demand research across high-margin Zazzle categories (invitations, stickers, phone cases, personalized gifts) beyond current 14 products.
10. **Single-Channel Traffic Dependency:** Currently reliant on Pinterest and early Google indexing; needs systematic weekly/monthly refresh cycles.

## 4. Prioritized Implementation Roadmap
1. **P1:** Align master brand config to `DARKSHOD` (`config/settings.yaml`) & update `db.py` with `executive_tasks` and `financial_ledger` tables + Emergency Stop state.
2. **P2:** Implement the 5 missing specialist agents (`seo_strategy.py`, `monetization.py`, `financial_reporting.py`, `security_compliance.py`, `system_doctor.py`) to complete the **17-Agent Team**.
3. **P3:** Upgrade `dashboard.py` into the unified **DARKSHOD Executive Control Center** (`OVERVIEW`, `PRODUCTS`, `SEO`, `CONTENT`, `PINTEREST`, `MONETIZATION`, `FINANCIAL`, `AUTOMATION` + integration status badges + `Emergency Stop`).
4. **P4:** Run live US Google Autocomplete market research across invitations, stickers, phone cases, and personalized gifts (`enable_live_autocomplete=True`) and record verified signals vs estimates.
5. **P5:** Add `.github/workflows/monthly_review.yml` and expand `pytest` suite (`tests/test_phase4_master_os.py`).
6. **P6:** Push to `Darkshod/zazzle-blog-autopilot`, deploy updated brand & site to `Darkshod/darkshod.github.io`, re-audit live URLs, and deliver Executive Business Report.
