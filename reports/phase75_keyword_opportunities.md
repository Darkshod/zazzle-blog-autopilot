# DARKSHOD — Phase 7.5 Search Opportunity & Indexing Prioritization

> **Data Integrity Notice:** Because `GSC_ACCESS_TOKEN` / `GSC_CREDENTIALS_PATH` is not yet connected locally, real Search Console query impressions, CTR, and positions (5–30) are **not yet available**. No search volumes or rankings are fabricated.

## Prioritized Manual URL Inspection List (Top 6 URLs)
Do **not** manually submit all 81 URLs. Google will discover all 81 URLs through the submitted `sitemap.xml`; use Search Console **URL Inspection -> Request Indexing** only for these highest-commercial-intent pages first:

1. `https://darkshod.github.io/articles/tartan-rocking-horse-ceramic-ornament.html` *(new Q4 heirloom ornament guide)*
2. `https://darkshod.github.io/articles/pinkmas-coquette-christmas-mug.html` *(homepage featured Q4 coquette mug guide)*
3. `https://darkshod.github.io/articles/old-money-christmas-card.html` *(homepage featured Q4 heritage stationery guide)*
4. `https://darkshod.github.io/articles/tartan-rocking-horse-holiday-card.html` *(flagship holiday card guide)*
5. `https://darkshod.github.io/articles/night-shift-nurse-mug.html` *(new evergreen US healthcare gift guide)*
6. `https://darkshod.github.io/articles/retro-italian-espresso-poster.html` *(new evergreen coffee bar wall art guide)*

## Search Opportunity Framework (Ready Once GSC API Connects)
When `python scripts/setup_gsc.py` pulls live 7d/28d/90d data, prioritize:
- **High-Impression / Low-CTR Pages:** Rewrite `<title>` and `<meta name="description">` to sharpen US buyer benefit.
- **Positions 5–30 Queries:** Expand H2 FAQ & customization walkthroughs and add internal links from the homepage and related guides.
- **US Country Slice (`country=usa`):** Focus new Zazzle product articles on US seasonal and evergreen queries confirmed in `phase7_keyword_opportunities.csv`.
