# DARKSHOD — Phase 7 Conversion & Funnel Audit

## Conversion Funnel Architecture
`Article / Homepage page_view` -> `zazzle_affiliate_click` (`?rf=238181835450951105`, `rel="sponsored noopener noreferrer"`) OR `zazzle_outbound_click` (non-affiliate Zazzle links) -> `Zazzle Product Page`

> **Reporting Rule:** Clicks are outbound intent signals only. They are never treated as sales or revenue; verified commission data is recorded only when reported by Zazzle.

## Audit Findings & Improvements Implemented
1. **CTA Placement & Clarity:**
   - Every article places a styled `.rec-card` with product photo (`720x900`, `aspect-ratio: 4/5`), `Affiliate Partner Link` badge, target audience/style summary, bulleted highlights, and high-contrast `#22382c` pill CTA (`Customize & View on Zazzle →`).
   - Added explicit `width="720" height="900"` attributes to all `.rec-card-media img` elements in `conversion.py` and all `16` published articles to prevent layout shift (CLS) on mobile.
2. **Affiliate Disclosure & Compliance:**
   - Visible disclosure banner (`Editorial & Affiliate Disclosure`) appears near the top of every article, paired with `Affiliate Partner Link` badges on each card and `/editorial-standards.html` in the footer.
3. **Outbound Click Tracking Coverage:**
   - Updated `site_builder.py` and `site/index.html` so **all** `a[href*="zazzle.com"]` links are tracked via `window.__darkshodClickInit` (zero duplicate listeners):
     - `data-affiliate="true"` or `rf=` -> `zazzle_affiliate_click` (`event_type: affiliate_click`)
     - Non-affiliate Zazzle links -> `zazzle_outbound_click` (`event_type: outbound_product`)
   - Internal navigation (`/articles/*`, `/blog.html`, `/`) is excluded from outbound tracking.
4. **Homepage Conversion Path Repair:**
   - Fixed the broken `/articles/pinkmas-christmas-card.html` (`404`) link on `https://darkshod.github.io/` to point to `/articles/pinkmas-coquette-christmas-mug.html` (`HTTP 200`).
5. **Verified Current Funnel Metrics:**
   - **GA4 Live Tracking:** Verified (`G-JT1HMMV6S5`, `page_view`, `zazzle_affiliate_click`, and `zazzle_outbound_click` all confirmed transmitting HTTP `204`).
   - **Historical Verified Traffic / Clicks / Revenue:** `0` historical sessions/sales imported (owner will monitor live counts in GA4 & Zazzle Affiliate dashboard; Search Console remains unverified).
