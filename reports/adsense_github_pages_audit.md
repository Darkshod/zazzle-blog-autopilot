# Google AdSense & GitHub Pages Compatibility Audit

## Technical Capabilities (Verified)
- **HTML `<meta>` Verification:** Supported cleanly in `<head>` (already verified with Pinterest `p:domain_verify` and wired for `GSC_VERIFICATION_TOKEN`).
- **Root `ads.txt` Support:** Supported on GitHub Pages by placing `ads.txt` at the repository root (no Jekyll conflict when `_config.yml` is absent or configured).
- **Client-Side JavaScript (`gtag.js` & AdSense):** Supported cleanly over HTTPS.
- **Migration Needed Now?** **No** — no technical limitation prevents serving static HTML, JS, meta tags, or `ads.txt` on GitHub Pages.

## Official Policy Limitation (Critical)
- **Google AdSense does NOT approve free `*.github.io` subdomains** (`https://darkshod.github.io/`) because `github.io` is a shared public suffix.
- **Required Fix Before Applying:** Attach a custom apex domain (e.g., `darkshod.com`) via a root `CNAME` file + 4 GitHub Pages `A` records, then place `ads.txt` at `https://darkshod.com/ads.txt`.
- **Approval Guarantee:** None. Approval depends on Google's manual/automated publisher review of original content and policy compliance.
