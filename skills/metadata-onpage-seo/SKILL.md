---
name: metadata-onpage-seo
description: Audit and draft on-page SEO fundamentals (titles, meta descriptions, keyphrases) across every indexable page of a client site. Use after the Technical Health agent has confirmed which pages are actually serving correctly. Also use when a client asks for metadata review, title/description drafts, or reports a page ranking poorly.
version: 1.0.0
---

# Metadata & On-Page SEO Agent

## Job
Audit and draft on-page SEO fundamentals across every indexable page.

## Prerequisite
Only run on pages the Technical Health agent has confirmed are serving correctly. Skip pages flagged as broken/blocked until infra is fixed.

## Checklist

- [ ] Enumerate all indexable pages — don't rely on an obvious sitemap list alone. Check for placeholder/test pages that are still live and indexed.
- [ ] For each page, check: focus keyphrase, SEO title, meta description. Flag any that are empty or still on a template default.
- [ ] Verify pixel-width limits on titles/descriptions, not just character counts — the practical limit runs shorter than most platforms' stated character limit.
- [ ] Draft missing/weak metadata, keeping the keyphrase naturally embedded rather than stuffed.
- [ ] Before editing anything, verify the slug matches the intended page. Editing the wrong page's keyphrase because the slug wasn't checked first is an easy, real mistake.
- [ ] Confirm changes are live via out-of-band verification (view-source or an incognito fetch), not just a tool re-fetch.

## Output format

Page-by-page metadata status, plus ready-to-paste drafts for anything missing or weak.

## Handoff
Pass completed/corrected metadata state to the GEO Agent — schema and llms.txt work depends on metadata already being correct.
