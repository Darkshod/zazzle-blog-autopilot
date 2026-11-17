# Google Analytics 4 (GA4) Setup Guide — DARKSHOD

## 1. Where to Find Your Measurement ID
1. Sign in to [Google Analytics](https://analytics.google.com/) and create a free GA4 Property for **DARKSHOD**.
2. Go to **Admin -> Data Streams -> Add stream -> Web**.
3. Enter `https://darkshod.github.io` and stream name `DARKSHOD Blog`.
4. Copy the **Measurement ID** (format: `G-XXXXXXXXXX`, regex `^G-[A-Z0-9]{8,12}$`).

## 2. Configure Without Exposing Secrets
1. Add the Measurement ID to your local `.env` (never commit `.env`):
   ```env
   GA4_MEASUREMENT_ID=G-YOURREALID
   ```
2. Rebuild and deploy `dist/` (`python -m zazzle_blog_autopilot.cli build-site`).

## 3. Verify Real Events vs. Automated Tests
- **Automated Test (`G-TEST123456`):** `tests/test_phase5_cycle.py` only tests HTML/JS rendering locally using a dummy `G-TEST123456` string. That does **not** send real GA4 traffic.
- **Live Verification:** After deploying with your real `G-...` ID, open `https://darkshod.github.io/articles/pinkmas-christmas-card.html`, click **"Customize & View on Zazzle →"**, and confirm `page_view` and `zazzle_outbound_click` / `zazzle_affiliate_click` appear inside **GA4 -> Reports -> Realtime**.
