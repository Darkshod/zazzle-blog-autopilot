# GA4 Verification Report — DARKSHOD

- **Measurement ID Configured:** `G-JT1HMMV6S5` (stored in local gitignored `.env` as `GA4_MEASUREMENT_ID`; never committed to GitHub)
- **Live Deployment:** `https://darkshod.github.io/` (website repo commit `94f43b6`, main repo commit `52bb26d` + report update)
- **Articles Covered:** `13 / 13` live articles on `https://darkshod.github.io/` (`sitemap_total: 64`, `sitemap_all_200: true`, `articles_all_200: true`, `duplicate_trackers_found: false`), plus `blog.html` and homepage `index.html` (`G-JT1HMMV6S5` verified present in live homepage HTML)
- **Events Implemented:**
  - `page_view` (via `gtag.js` with `anonymize_ip: true`)
  - `zazzle_outbound_click` (non-affiliate Zazzle links)
  - `zazzle_affiliate_click` (affiliate Zazzle links with `data-affiliate="true"`)
- **Live Browser Network Verification (`https://darkshod.github.io/articles/old-money-christmas-card.html`):**
  - `GET https://www.googletagmanager.com/gtag/js?id=G-JT1HMMV6S5` -> HTTP `200` (`1` request, `0` duplicate scripts)
  - `POST https://www.google-analytics.com/g/collect?v=2&tid=G-JT1HMMV6S5...&en=page_view` -> HTTP `204`
  - Single click on `"Customize & View on Zazzle →"` (`a.zazzle-cta-card`, `rf=238181835450951105`) -> `1` `POST https://www.google-analytics.com/g/collect?v=2&tid=G-JT1HMMV6S5...&en=zazzle_affiliate_click&ep.event_type=affiliate_click&ep.article_slug=old-money-christmas-card&ep.product_id=5` -> HTTP `204` (`0` duplicate events)
  - Note: `zazzle_outbound_click` was not triggered during this click test because the article CTA uses an affiliate `rf=` link (`data-affiliate="true"`), which routes to `zazzle_affiliate_click` as designed.
  - Note: An initial browser visit to `https://darkshod.github.io/` observed `0` GA requests (before CDN cache refresh), though fetching `https://darkshod.github.io/` directly confirms `G-JT1HMMV6S5` is present in the live HTML.
- **Automated Test Suite:** `python -m pytest -v` -> `16 passed` (`0` failed, `0` skipped)
- **GA4 Realtime Dashboard Status:** **Pending Owner Confirmation** — live `g/collect` HTTP `204` beacons to `G-JT1HMMV6S5` are confirmed leaving the browser, but confirming they appear inside Google Analytics (`https://analytics.google.com/` -> **Reports -> Realtime**) requires your personal Google account login.
