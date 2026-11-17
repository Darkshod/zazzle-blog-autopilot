# Google AdSense & GitHub Pages Official Policy Audit

## 1. Official Policy References
- **AdSense Site Eligibility & Subdomains:** `https://support.google.com/adsense/answer/9724` (AdSense Program Policies & Site Eligibility)
- **AdSense `ads.txt` Guide:** `https://support.google.com/adsense/answer/7532444`
- **GitHub Pages Custom Domain Docs:** `https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site`

## 2. Technical Capabilities vs. Policy Eligibility
- **HTML Verification Meta Tag (`<meta>`):** **Supported** on GitHub Pages (verified with Pinterest `p:domain_verify`).
- **Root `ads.txt` Support:** **Supported** on GitHub Pages by placing `ads.txt` at the repo root (`https://<custom-domain>/ads.txt`).
- **JavaScript (`gtag.js` / AdSense script):** **Supported** over HTTPS.
- **`*.github.io` Subdomain Eligibility:** **NOT ELIGIBLE.** Google AdSense rejects free shared public-suffix subdomains (`darkshod.github.io`) because the publisher does not own the root `github.io` domain or `github.io/ads.txt`.
- **Custom Domain Requirement:** **REQUIRED** before applying for AdSense (configure via a root `CNAME` file + 4 GitHub Pages `A` records). No hosting migration is technically required once a custom domain is attached.

## 3. Content & Publisher Readiness
- Trust pages (`about.html`, `contact.html`, `privacy-policy.html`, `editorial-standards.html`) are live.
- `13` original articles are live; recommend reaching `20+` high-craft articles and attaching a custom domain before submitting an AdSense review (approval is never guaranteed).
