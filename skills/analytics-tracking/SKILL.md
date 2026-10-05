---
name: analytics-tracking
description: Confirm a client can actually measure GEO/SEO impact, and build the AI-referral attribution layer that GA4 doesn't provide by default. Use in parallel with the content pipeline (independent of Metadata/GEO agents), whenever a client asks "how do I know this is working," or when setting up AI-visibility ROI reporting for the first time.
version: 1.0.0
---

# Analytics & Tracking Agent

## Job
Confirm the client can actually measure the impact of the SEO/GEO work, and build the AI-attribution layer that's missing from GA4 by default.

## Checklist

- [ ] Verify the GA4 tag is actually installed in page source — not just configured in the dashboard. These can be out of sync.
- [ ] Verify via the Realtime report with real traffic, not just GA4's own setup checklist — the setup checklist can lag behind reality.
- [ ] Verify Search Console access and submit the sitemap if not already submitted.
- [ ] Check sitemap fetch status and page discovery count after submission.
- [ ] Build (or confirm existing) AI-referral traffic segmentation: a Free Form exploration using Session source dimension, with a regex filter for major AI platforms — `chatgpt|openai|perplexity|claude|gemini|copilot`.
- [ ] Flag when data is pending processing vs. genuinely broken. GA4 has a real lag between Realtime and aggregated reports — don't mistake one for the other.

## Output format

Access confirmation, sitemap status, and a working AI-referral tracking view. This view is the concrete "proof of GEO ROI" deliverable for the client.

## Handoff
Uses Technical Health's redirect/URL findings to correctly interpret indexing data. Runs independently of the Metadata/GEO/Content pipeline — no need to wait on those agents.
