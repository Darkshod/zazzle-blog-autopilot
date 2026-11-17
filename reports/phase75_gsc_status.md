# DARKSHOD — Phase 7.5 Google Search Console Status

- **Property:** `https://darkshod.github.io/`
- **Ownership Verification (Google Search Console UI):** **VERIFIED** *(confirmed by owner)*
- **Sitemap Submitted (Google Search Console UI):** **SUBMITTED** (`https://darkshod.github.io/sitemap.xml` — `81 / 81` URLs live `HTTP 200`)
- **GSC REST API Authorization (`GSC_ACCESS_TOKEN` / `GSC_CREDENTIALS_PATH`):** **NOT CONNECTED**
  - Local `.env` contains `GA4_MEASUREMENT_ID` only (`GSC_ACCESS_TOKEN` and `GSC_CREDENTIALS_PATH` are absent; `./credentials/` does not yet contain a JSON key).
  - As a result, Google's sitemap read/error count, URL Inspection verdicts, and 7d / 28d / 90d Search Analytics (`clicks`, `impressions`, `ctr`, `position`, `country`, `device`) are **not yet retrievable via API**.

## Minimum-Permission Google Cloud Setup (to Activate Automated Reporting)
1. Open [Google Cloud Console](https://console.cloud.google.com/) (free tier, \$0) -> enable **Google Search Console API** (`searchconsole.googleapis.com`).
2. Create either:
   - A **Service Account** -> download JSON key to `./credentials/gsc_service_account.json` (gitignored), then add that Service Account email as a **Restricted User** in Google Search Console -> **Settings -> Users and permissions** for `https://darkshod.github.io/`, OR
   - An **OAuth 2.0 Client ID (Desktop App)** with minimum scope `https://www.googleapis.com/auth/webmasters.readonly` and store the token JSON in `./credentials/gsc_oauth.json` (gitignored).
3. Add `GSC_CREDENTIALS_PATH=./credentials/gsc_service_account.json` (or `GSC_ACCESS_TOKEN=...`) to your local gitignored `.env`.
4. Run `python scripts/setup_gsc.py` to pull `7d`, `28d`, and `90d` Search Analytics (`query`, `page`, `country`, `device`) and sitemap diagnostics automatically.
