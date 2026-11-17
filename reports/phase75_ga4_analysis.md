# DARKSHOD — Phase 7.5 GA4 Analysis & Funnel Readiness

- **GA4 Measurement ID:** `G-JT1HMMV6S5` (verified live across homepage, `blog.html`, and all `16 / 16` published articles)
- **Active Events Verified Live:**
  - `page_view` (HTTP `204` confirmed)
  - `zazzle_affiliate_click` (`?rf=238181835450951105`, `rel="sponsored noopener noreferrer"`, HTTP `204` confirmed)
  - `zazzle_outbound_click` (non-affiliate Zazzle links, HTTP `204` confirmed)
- **GA4 Data API Status Locally:** **NOT CONNECTED** *(GA4 property reporting requires owner login in `https://analytics.google.com/` or a Google Analytics Data API service account)*.
- **Verified Historical Totals Imported Locally:** `0` users, `0` sessions, `0` page views, `0` US visitors, `0` Zazzle clicks, `0` sales *(no metrics fabricated)*.

## How to Compare Traffic Sources & Zazzle Clicks in GA4 UI
1. Open **Reports → Acquisition → Traffic acquisition** in GA4 (`G-JT1HMMV6S5`) and filter by **Country = United States**.
2. Compare **Organic Search (`google / organic`)** vs **Organic Social (`pinterest.com / referral`)**.
3. Open **Reports → Engagement → Events** to compare `page_view` against `zazzle_affiliate_click` and `zazzle_outbound_click` per `article_slug` (`ep.article_slug`).
4. Never treat `zazzle_affiliate_click` as a sale; verify actual commissions inside the Zazzle Associate dashboard.
