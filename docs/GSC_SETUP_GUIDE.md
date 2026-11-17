# Google Search Console (GSC) Setup Guide — DARKSHOD

## 1. Verify Ownership via URL-Prefix HTML Meta Tag
1. Open [https://search.google.com/search-console/](https://search.google.com/search-console/) and sign in.
2. Click **Add property** and choose **URL prefix** (do NOT choose Domain, since GitHub owns `github.io` DNS).
3. Enter: **`https://darkshod.github.io/`**
4. Under **Verify ownership**, select **HTML tag**.
5. Copy the `<meta name="google-site-verification" content="..." />` tag (or just the `content` token).
6. Paste the `content` token into `.env` as `GSC_VERIFICATION_TOKEN=<token>` (or share the tag with Antigravity), rebuild & deploy `darkshod.github.io`, then return to Google Search Console and click **Verify**.

## 2. Submit Your Sitemap
Once verified in Search Console -> **Sitemaps**, submit:
- `https://darkshod.github.io/sitemap.xml`

## 3. Optional Google Cloud OAuth API Access (Minimum Permissions)
1. In [Google Cloud Console](https://console.cloud.google.com/), enable **Google Search Console API** (`searchconsole.googleapis.com`).
2. Create an OAuth 2.0 Client ID (Desktop App) or Service Account with minimum scope `https://www.googleapis.com/auth/webmasters` (or `.readonly`).
3. Store credentials inside `./credentials/` (gitignored) and set `GSC_ACCESS_TOKEN` in `.env`. Never commit `.env` or `credentials/*.json`.
4. Run `python scripts/setup_gsc.py` to submit the sitemap and pull impressions, clicks, CTR, and average position.
