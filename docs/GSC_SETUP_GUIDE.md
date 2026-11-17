# Google Search Console (GSC) Setup Guide — DARKSHOD

## 1. Google Cloud OAuth & API Permissions
1. Open [Google Cloud Console](https://console.cloud.google.com/) -> create a free project.
2. Enable **Google Search Console API** (`searchconsole.googleapis.com`).
3. Create an **OAuth 2.0 Client ID** (Desktop App) or **Service Account** with scope `https://www.googleapis.com/auth/webmasters` (read + sitemap submission) or `https://www.googleapis.com/auth/webmasters.readonly`.

## 2. Secure Token Storage
- Save downloaded JSON credentials inside `./credentials/` (ignored by `.gitignore`) and set in `.env`:
  ```env
  GSC_CREDENTIALS_PATH=./credentials/gsc.json
  GSC_ACCESS_TOKEN=ya29....
  GSC_VERIFICATION_TOKEN=<meta-tag-content-token>
  ```
- Never commit `.env` or `credentials/*.json` to GitHub.

## 3. Verify Ownership, Submit Sitemap & Pull Real Data
1. Add your site `https://darkshod.github.io/` in [Google Search Console](https://search.google.com/search-console) and choose **HTML tag** verification.
2. Put the `content="..."` token into `GSC_VERIFICATION_TOKEN`, rebuild, deploy to `darkshod.github.io`, and click **Verify** in GSC.
3. Run:
   ```bash
   python scripts/setup_gsc.py
   ```
   This submits `https://darkshod.github.io/sitemap.xml` and retrieves real Search Analytics (impressions, clicks, CTR, average position). Without `GSC_ACCESS_TOKEN`, the system reports `NOT CONNECTED`.
