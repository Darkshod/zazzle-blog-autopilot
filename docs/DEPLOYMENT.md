# Deployment & Scheduling Guide ($0 Hosting)

## 1. Recommended Static Hosting: Cloudflare Pages (Free Tier)

Why **Cloudflare Pages** over GitHub Pages for a commercial blog:
- Commercial monetization and **Google AdSense** are permitted on Cloudflare Pages (whereas GitHub Pages terms restrict purely commercial/ad-driven sites).
- Free global CDN, automatic HTTPS, custom domain support, and unlimited bandwidth.

### Deploy Steps
1. Push this repository to GitHub.
2. Log into **Cloudflare Dashboard -> Workers & Pages -> Create -> Pages -> Connect to Git**.
3. Select `zazzle-blog-autopilot`.
4. Set **Build command**:
   ```bash
   pip install -r requirements.txt && python -m zazzle_blog_autopilot.cli run-all && python -m zazzle_blog_autopilot.cli build-site
   ```
5. Set **Build output directory**: `dist`.
6. Update `config/settings.yaml` -> `brand.base_url` to your live `*.pages.dev` or custom domain.

## 2. Google Search Console Setup
1. Open [Google Search Console](https://search.google.com/search-console) and verify your domain via DNS TXT record.
2. Submit `https://<your-domain>/sitemap.xml` once.
3. Never use automated mass-indexing scripts; Google indexes healthy sitemaps organically.

## 3. Cloud vs. Local Automation
- **Cloud Automation (Recommended)**: `.github/workflows/daily_autopilot.yml` runs daily at `14:00 UTC` (`09:00 EST`) on GitHub-hosted runners—your Windows laptop can stay completely off.
- **Local Windows 11 Automation**: Run `scripts/register_windows_schedule.ps1` in PowerShell if you want local execution at `09:00 AM` (requires PC to be awake).
