# Monetization & Compliance Guide

## 1. Zazzle Organic Product Sales
- Every article includes contextual product recommendation cards linking directly to your Zazzle product pages.
- Ordinary product links remain clean and unlabeled as affiliate links when `zazzle_affiliate_approved: false`.

## 2. Zazzle Affiliate / Associate Program
- **Never assume automatic eligibility**: Before enabling `zazzle_affiliate_approved: true` in `config/settings.yaml`, verify current Zazzle Ambassador/Associate country eligibility for **Morocco (`MA`)** and confirm supported payout methods (such as Payoneer or USD wire) inside Zazzle's official program terms.
- Once approved, set `ZAZZLE_AFFILIATE_APPROVED=true` and `ZAZZLE_AFFILIATE_ID=<your-id>` in `.env`. All product cards will automatically append your tracking parameter and mark links `rel="sponsored noopener noreferrer"`.

## 3. Google AdSense Preparation
This site pre-builds the foundational trust pages required before applying for Google AdSense:
- `/about.html`
- `/contact.html`
- `/privacy-policy.html`
- `/editorial-standards.html`

Before applying for AdSense:
- Replace `Your Brand Name` and `hello@example.com` in `config/settings.yaml` with your real brand identity and monitored email.
- Publish at least 15–25 original, helpful articles (`>= 750` words each) and connect a custom domain on Cloudflare Pages.
