# Sample audit: Technical and GEO/SEO audit

> Anonymized from a real audit delivered in August 2026. The domain, brand and company names are replaced with placeholders. Findings, severities, fixes and verification steps are unchanged. This is the kind of document the **Client Reporting** agent produces from the technical agents' findings.

**Site:** `www.example-startup.com` (a startup finance-planning product)
**Platform:** Vite + React single-page app, built with an AI app builder, hosted on Netlify behind Cloudflare
**Date:** 24 Aug 2026

## Score: 50 / 100, needs work (3 pass, 1 warn, 4 fail)

| Category | Result | Score |
|---|---|---|
| Crawlability | Fail | 6 / 15 |
| Indexability | Fail | 5 / 12 |
| Security | Warn | 5 / 10 |
| URL structure | Pass | 7 / 8 |
| Mobile optimization (est.) | Pass | 10 / 10 |
| Core Web Vitals (est.) | Fail | 5 / 15 |
| Server-side rendering | Fail | 0 / 15 |
| Page speed and server | Pass | 12 / 15 |

## AI crawler access

`robots.txt` disallows 9 named bots, and Cloudflare's managed "block AI bots" rule is active on the zone. Because the site has no server-side rendering, the few crawlers that are allowed still see an empty page.

| Crawler | Platform | Access | What it actually gets |
|---|---|---|---|
| GPTBot | ChatGPT | Blocked | Nothing, disallowed |
| ClaudeBot | Claude | Blocked | Nothing, disallowed |
| Google-Extended | Gemini training/grounding | Blocked | Nothing, disallowed |
| Amazonbot | Alexa | Blocked | Nothing, disallowed |
| Applebot-Extended | Apple Intelligence | Blocked | Nothing, disallowed |
| Bytespider, CCBot, meta-externalagent | TikTok, Common Crawl, Meta AI | Blocked | Nothing, disallowed |
| CloudflareBrowserRenderingCrawler | Cloudflare AI Crawl Control | Blocked | Nothing, disallowed |
| PerplexityBot | Perplexity | Allowed | An empty `<div id="root"></div>`, no SSR |
| bingbot | Bing / Copilot | Allowed | Renders JS during indexing, likely sees content eventually |
| Googlebot | Search / AI Overviews | Allowed | Renders JS, but on a delayed queue |

---

## Critical: fix immediately

### 01. Server-side rendering (0/15): the whole site is one empty div
**Who fixes it:** developer (first step is self-serve)

Fetching the homepage without running JavaScript returns only `<body><div id="root"></div></body>`. Every headline, price, testimonial and FAQ exists only after about 650 KB of JavaScript runs. No crawler that doesn't execute JavaScript can see any of it. This is the root cause of most other findings.

**How to fix**, in order of effort:
1. **Netlify prerendering (about 10 minutes, do this first).** Site configuration, then Build and deploy, then Prerendering, and switch it on. Netlify serves a fully rendered snapshot to bots while people still get the normal app. No code changes.
2. **Statically generate the marketing pages** (home, pricing, about) with a framework that supports islands (such as Astro), and keep the authenticated app as a client-rendered SPA.
3. **Full framework migration** (Next.js or Remix) if a rebuild is planned anyway.

**Verify:** `curl -s https://www.example-startup.com/ | grep -o "<headline text>"` should return a match.

### 02. Crawlability: most AI crawlers are disallowed
**Who fixes it:** site owner (a dashboard setting)

The whole `robots.txt` is Cloudflare's default managed AI-crawler block, and nothing in it was written by the site. Combined with finding 01, ChatGPT, Claude, Gemini and Apple Intelligence cannot cite the site even in principle. This is an explicit refusal, not a rendering problem.

**How to fix**
1. In Cloudflare, open the zone, then Security, then AI Crawl Control (or Bots, depending on plan), and review the per-bot toggles. It is likely one "Block AI bots" switch.
2. Decide intent. If the goal is to be cited, set GPTBot, ClaudeBot, Google-Extended and Applebot-Extended to Allow. Pure scraper bots with no citation value (Bytespider, CCBot, meta-externalagent) can stay blocked as a deliberate licensing choice.

**Verify:** `curl -s https://www.example-startup.com/robots.txt` and confirm the named blocks are gone for the bots you want to allow.

### 03. Crawlability: no sitemap
**Who fixes it:** developer

`/sitemap.xml` returns HTTP 200, but the body is the app shell, not XML. There is no sitemap and no `Sitemap:` line in `robots.txt`.

**How to fix:** add a static `sitemap.xml` to the project's `/public` folder (Vite serves it as-is, bypassing the SPA catch-all) listing the home, pricing, about and contact pages, then add `Sitemap: https://www.example-startup.com/sitemap.xml` to `robots.txt`.

### 04. URL structure: the bare domain returns a hard 404
**Who fixes it:** site owner or developer

`example-startup.com` (no `www`) returns 404 over both HTTP and HTTPS, with no redirect. Anyone typing the bare domain, or following a backlink or deck link without `www`, hits a dead page.

**How to fix**
1. In Cloudflare, point the apex domain at the same target as `www` (proxied).
2. Add a Bulk Redirect or Page Rule: `example-startup.com/*` to a 301 at `https://www.example-startup.com/$1`.

**Verify:** `curl -IL https://example-startup.com/` should show one 301 to `www`, then a 200.

### 05. Indexability: no meta description, canonical, Open Graph tags or schema
**Who fixes it:** developer

Neither the raw HTML nor the rendered page has a meta description, canonical link, Open Graph tags or any JSON-LD. The only signal is a generic `<title>`. Shared links have no preview, and search engines have no canonical URL signal.

**How to fix:** add `react-helmet-async` (or the framework's equivalent) and set per-route tags: a descriptive title, a meta description, a canonical link and Open Graph title, description, image and URL.

Note: this only helps crawlers that run JavaScript until fix 01 is in place.

---

## Warnings: fix this month

### 06. Indexability: soft 404s
**Who fixes it:** developer

Every URL, including pages that don't exist, returns HTTP 200 with the same app shell. Search engines cannot tell a real route from a typo, which risks index bloat.

**How to fix:** replace the blanket `/* /index.html 200` rule in Netlify's `_redirects` with an explicit list of real routes, and end it with `/* /index.html 404`. Real users keep client-side routing, and crawlers get a true 404 for unknown paths.

### 07. Crawlability: malformed `robots.txt`
**Who fixes it:** developer

`robots.txt` is served as `text/html` and runs from Cloudflare's block straight into the app's HTML, because there is no real file at the origin.

**How to fix:** add a real `robots.txt` to `/public` (`User-agent: *`, `Allow: /`, and the `Sitemap:` line). Cloudflare's managed rules will still merge in ahead of it, which is normal.

### 08. Security: incomplete HSTS and four missing headers
**Who fixes it:** developer

HSTS is present without `includeSubDomains`. `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Content-Security-Policy` are missing.

**How to fix:** add a `_headers` file to `/public` with the standard set (HSTS with `includeSubDomains; preload`, `nosniff`, `SAMEORIGIN`, a strict referrer policy and a restrictive permissions policy). Roll out the CSP in **report-only mode first**, because the payments library, tag manager and the app builder's badge script all need allow-listing before it can be enforced.

### 09. Page speed: a payments library loads on the marketing homepage
**Who fixes it:** developer

The homepage loads a 259 KB main bundle plus a 248 KB payments library, a 57 KB charts bundle, and router and UI bundles, all before the page is interactive. The load event fires at about 4.5 seconds. The payments library is only needed at checkout.

**How to fix:** load it with a dynamic `import()` only when the user reaches checkout, which should remove about 250 KB from the initial load. Also confirm the charts bundle is only imported by dashboard routes, and split by route with `React.lazy` if it is not.

---

## Recommendations: this quarter

### 10. Page speed: hashed assets cached for only 4 hours
**Who fixes it:** developer

Content-hashed JavaScript files are served with `max-age=14400, must-revalidate`. The hash changes on every deploy, so there is no reason to cache them for only 4 hours.

**How to fix:** in `_headers`, set `/assets/*` to `Cache-Control: public, max-age=31536000, immutable`.

### 11. Housekeeping: the app builder's dev badge is live in production
**Who fixes it:** developer

A development and attribution badge script from the tool the app was scaffolded with loads on every page. It is harmless functionally, but it is the first impression for a paying customer of a financial-planning product.

**How to fix:** remove the script tag from `index.html`. Once finding 05 is done, add `SoftwareApplication` and `Organization` JSON-LD describing the product and its publisher.

---

## What this sample shows
- **Severity-ranked findings** grouped as critical, warnings and recommendations.
- **A named fixer** for every finding, so a non-technical owner knows what to do themselves and what to hand to a developer.
- **Step-by-step fixes** in the platform's own settings and file names.
- **A way to verify each fix**, so the owner can confirm it worked.
- **Root-cause ordering:** finding 01 drives findings 02 and 05, and the report says so.
