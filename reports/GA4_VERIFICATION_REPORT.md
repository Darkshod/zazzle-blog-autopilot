# GA4 Verification Report — DARKSHOD

- **Measurement ID Configured:** `NOT CONFIGURED` (`GA4_MEASUREMENT_ID` is not yet set in `.env`)
- **Articles Covered by Outbound Click Listener:** `13 / 13` live articles on `https://darkshod.github.io/`
- **Events Implemented:** `page_view` (via `gtag.js`), `zazzle_outbound_click` (non-affiliate Zazzle links), `zazzle_affiliate_click` (`data-affiliate="true"` links)
- **Duplicate Event Prevention:** `window.__darkshodClickInit` guard verified (`1` listener per page, `0` duplicate scripts on all 13 live articles)
- **Internal Link Exclusion:** Listener checks `a.zazzle-cta-card` and `a.href.indexOf('zazzle.com') !== -1`
- **Privacy Settings:** `anonymize_ip: true` enabled when `GA4_MEASUREMENT_ID` is configured; zero PII transmitted
- **Local Test Status:** `tests/test_phase5_cycle.py::test_ga4_and_gsc_meta_rendering_in_site_builder` passed using dummy ID `G-TEST123456`
- **Realtime Verification Status:** `NOT VERIFIED` (requires your real `G-XXXXXXXXXX` Measurement ID in `.env` and redeployment)
- **Remaining Blockers:** Owner must create the GA4 property & Web Stream (`https://darkshod.github.io/`) per `docs/GA4_SETUP_GUIDE.md` and supply `G-XXXXXXXXXX`.
