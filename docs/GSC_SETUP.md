# Google Search Console OAuth Setup Guide ($0)

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a free project.
2. Enable **Google Search Console API** (`searchconsole.googleapis.com`).
3. Create **OAuth 2.0 Client ID** (Desktop App) or a **Service Account**:
   - If using a **Service Account**, copy its email (`...@...iam.gserviceaccount.com`) and add it as a **Full/Restricted User** in [Google Search Console -> Settings -> Users and permissions](https://search.google.com/search-console) for `https://darkshod.github.io/`.
4. Export a short-lived OAuth access token or point `.env` to your credentials:
   ```env
   GSC_CREDENTIALS_PATH=./credentials/gsc_service_account.json
   GSC_ACCESS_TOKEN=ya29....
   ```
5. Never commit `credentials/*.json` or `.env` (both are ignored in `.gitignore`).
6. Once configured, `GoogleSearchConsoleClient.fetch_search_analytics()` and `inspect_url()` pull real impressions, clicks, CTR, average position, and index status. Without credentials, the system honestly reports `Unconnected`.
