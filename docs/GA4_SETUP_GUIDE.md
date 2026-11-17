# Google Analytics 4 (GA4) Setup Guide — DARKSHOD

## 1. Create Your Free GA4 Property & Web Stream
1. Open [https://analytics.google.com/](https://analytics.google.com/) and sign in.
2. Create an Account named **`DARKSHOD`** (if not already created).
3. Create a Property named **`DARKSHOD Website`**:
   - Reporting currency: **USD**
   - Reporting time zone: **United States (Eastern Time)** or **Morocco (Africa/Casablanca)**
4. Under **Data Streams**, choose **Web**.
5. Enter Website URL: **`https://darkshod.github.io/`** and Stream Name: **`DARKSHOD Blog`**.
6. Copy your **Measurement ID** (strict format: **`G-XXXXXXXXXX`**).

## 2. Configure Locally Without Exposing Secrets
1. Add the Measurement ID to your local `.env` (never commit `.env`):
   ```env
   GA4_MEASUREMENT_ID=G-XXXXXXXXXX
   ```
2. Rebuild and deploy:
   ```bash
   python -m zazzle_blog_autopilot.cli build-site
   ```
   *(Push `dist/` to `Darkshod/darkshod.github.io`.)*

## 3. Distinguish Test Events vs. Real Visitor Events
- **Local Automated Test:** `tests/test_phase5_cycle.py` validates HTML/JS rendering using a dummy `G-TEST123456` ID; it does **not** send real GA4 traffic.
- **Real Visitor Verification:** After deploying with your real `G-` ID, visit `https://darkshod.github.io/articles/pinkmas-christmas-card.html`, click **"Customize & View on Zazzle →"**, and confirm `page_view` and `zazzle_outbound_click` / `zazzle_affiliate_click` appear in **GA4 -> Reports -> Realtime**.
