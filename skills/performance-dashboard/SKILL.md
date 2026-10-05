---
name: performance-dashboard
description: Render a client-facing performance view — SEO and GEO health as gauge scores, plus live Google Search Console and GA4 data including the AI-referral segment. Use whenever a client asks "how are we doing," on a recurring schedule (weekly/monthly per retainer), or after a full orchestrator run completes for a client. This is the outcome/ROI view, distinct from progress-dashboard which tracks internal task status.
version: 1.0.0
---

# Performance Dashboard Agent

## Job
Answer "is this actually working" in one glance — a client shouldn't have to read a task list to know whether their SEO/GEO health is improving. This is the deliverable that justifies the retainer, not an internal ops tool.

## Distinct from progress-dashboard
`progress-dashboard` shows work in flight (tasks, statuses, who owns what) and is read
by you. This agent shows outcomes (scores, real search/analytics data) and is meant to
be shown to the client. Different audience, different question being answered — don't
merge them into one view even though both are "a dashboard."

## Score computation

- [ ] **SEO score** = weighted pass rate across `technical-health` and `metadata-onpage-seo` findings for this client: (clean/passing checklist items) ÷ (total applicable checklist items), most recent full run. A `blocked` item counts as neither pass nor fail — exclude it from the denominator and note it separately, since it's not yet known whether it would pass.
- [ ] **GEO score** = same pass-rate calculation across `geo-ai-visibility` and `backlink-authority` findings.
- [ ] Recompute both scores after every full (non-diffed) orchestrator run — never after a partial/diffed run, since a diffed run didn't re-check everything the score depends on.
- [ ] Store the computed score with its `computed_at` timestamp and which run it was derived from, so a client asking "why did my score change" has a concrete answer, not just a new number.
- [ ] A score dropping between two runs is not itself an error — it can mean a regression (something that was fixed broke again) or scope expansion (new pages/checks added this run lowered the denominator's pass rate). Note which one it was; don't let the client infer regression when it was actually scope growth.

## Live GSC / GA4 data

- [ ] Pull directly from Search Console and GA4 via the credentials already verified by `account-manager` and `analytics-tracking` — never re-prompt the client for access this agent doesn't need to ask for again.
- [ ] Search Console: clicks, impressions, CTR, average position, over a defined trailing window (default last 28 days, matching GSC's own default reporting window so numbers are comparable to what the client sees if they check GSC themselves).
- [ ] GA4: total sessions, AI-referral sessions (using the segment `analytics-tracking` already built — `chatgpt|openai|perplexity|claude|gemini|copilot`), and AI-referral as a percentage of total sessions, same trailing window.
- [ ] Flag clearly when GSC/GA4 data is still processing vs. genuinely flat — a real zero and a reporting lag look identical to a client unless labeled.
- [ ] Never silently substitute stale cached data if a live pull fails — show the last successful pull's timestamp explicitly rather than presenting old numbers as current.

## Output format

A single HTML view (or embeddable widget for the client portal) per client, showing:
- Two gauge/speedometer displays: SEO score and GEO score, 0–100, colored by band (red under ~50, amber 50–79, teal 80+)
- A GSC panel: clicks, impressions, CTR, average position, trailing-window trend
- A GA4 panel: total sessions, AI-referral sessions, AI-referral % of total, trailing-window trend
- Last-updated timestamp, and which run the scores were computed from

## Handoff
Reads from `technical-health`, `metadata-onpage-seo`, `geo-ai-visibility`, and `backlink-authority` for score inputs, and from `analytics-tracking`'s verified GSC/GA4 access for live data. Writes nothing back except the rendered view — same read-only discipline as `progress-dashboard`.
