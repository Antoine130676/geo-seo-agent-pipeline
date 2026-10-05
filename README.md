# GEO/SEO Agent Pipeline

A multi-agent design for delivering GEO (Generative Engine Optimization) and technical SEO work to clients, built as a set of Claude/Hermes agent skills. Each agent is a `SKILL.md` with a defined job, checklist, output format and handoff.

> **Status: working design, not a product.** The `skills/` folder holds the agent specifications as they exist today. Outcome numbers (traffic, citations, hours saved) are not claimed here. See [Status](#status) for what is and isn't proven.

## What it does

Takes a new client from confirmed payment to a verified, measurable GEO/SEO engagement, with a human approval point where money, access or irreversible changes are involved.

```
Client pays
   |
Account Manager ---- verifies credentials, asks the human for go-ahead (the one universal human gate)
   |
Project Manager ---- creates the engagement, owns the safety gate, notifications, retainer schedule
   |                          \
   |                           Skill Release Manager ---- tests and gates changes to the agents themselves
   |
Orchestration (geo-client-workflow) ---- runs the technical agents, logs cost per project
   |
   +-- Technical Health ------ is the site really serving what the CMS claims?     (runs first)
   +-- Metadata & On-Page SEO - titles, descriptions, keyphrases                     (after Technical Health)
   +-- GEO / AI-Visibility --- llms.txt, schema, brand-collision risk               (after Metadata)
   +-- Analytics & Tracking -- GA4/GSC verified, AI-referral segment                (parallel)
   +-- Backlink & Authority -- off-page profile, toxic links, outreach drafts       (parallel)
   +-- Content Expansion ----- additive drafts, never auto-published
   +-- Client Reporting ------ teaser / client / developer registers                (runs last)
   |
Dashboards: Progress (internal, read-only task board) | Performance (client-facing SEO/GEO gauges + GSC/GA4)
```

## Design principles

1. **Verify, don't trust the tool.** Agents are told to confirm results out-of-band (view-source, incognito fetch, the site's own aggregation endpoint) because CMS dashboards and tool fetches can be stale.
2. **Finishing is not verifying.** A task is `done` only with a changelog entry containing the verification method, side effects checked and a backup/rollback reference.
3. **Humans approve what is irreversible or outward-facing.** Credentials, kickoff, backlink-outreach emails, disavow files, published content and out-of-scope changes all wait for explicit approval.
4. **The agents get tested too.** A change to a `SKILL.md` runs against a staging site with seeded issues and a golden file of expected findings before it can go live, with archived versions for rollback.
5. **Different audiences, different documents.** The same findings become a shallow pre-sale teaser, a plain-English client update, or a precise developer handoff.
6. **Honest scoring.** Scores show which run they came from; a score drop is labelled regression vs. scope growth; stale data is labelled, never passed off as current.

## Agents

| Agent | Job | Key guardrail |
|---|---|---|
| [Account Manager](skills/account-manager/SKILL.md) | Payment webhook to verified credentials to human go-ahead | Nothing is created before the human says go; 3 failed credential checks escalates instead of retrying |
| [Project Manager](skills/project-manager/SKILL.md) | Engagements, priorities, safety gate, notifications, closure | No `done` without changelog + backup + out-of-band verification; credentials revoked on closure |
| [Skill Release Manager](skills/skill-release-manager/SKILL.md) | Version, test and promote agent changes | Staging client + golden file; no promoting "mostly passing" |
| [Technical Health](skills/technical-health/SKILL.md) | Infra: caching, redirects, PageSpeed, accessibility | Runs first; flags tool-side caching vs. server issues |
| [Metadata & On-Page SEO](skills/metadata-onpage-seo/SKILL.md) | Titles, descriptions, keyphrases | Verifies slug before editing; pixel width, not just characters |
| [GEO / AI-Visibility](skills/geo-ai-visibility/SKILL.md) | llms.txt, schema, brand collision | Validates llms.txt against spec; strategic items go to the client as decisions |
| [Analytics & Tracking](skills/analytics-tracking/SKILL.md) | GA4/GSC verification, AI-referral segment | Real-traffic check, not the setup checklist |
| [Content Expansion](skills/content-expansion/SKILL.md) | Additive content drafts | Never auto-publishes; claims flagged as estimates; 2-rejection escalation |
| [Client Reporting](skills/client-reporting/SKILL.md) | Teaser / client / developer documents | Teaser never includes the fix; runs last |
| [Backlink & Authority](skills/backlink-authority/SKILL.md) | Off-page audit, competitor gap | Outreach never auto-sends; disavow only with approval |
| [geo-client-workflow](skills/geo-client-workflow/SKILL.md) | Execution gate, parallel audit orchestration, per-project token/cost log | Asks before running a skill; cost from real session data, not guesses |
| [Progress Dashboard](skills/progress-dashboard/SKILL.md) | Internal kanban of every task across clients | Read-only; flags `done` tasks with no changelog as unverified |
| [Performance Dashboard](skills/performance-dashboard/SKILL.md) | Client-facing SEO/GEO gauges + live GSC/GA4 | Labels processing lag vs. real zero; never shows stale data as current |

See [docs/architecture.md](docs/architecture.md) for the shared state contract and run order.

## Status

**In use today**
- 13 versioned agent specifications with defined run order, handoffs and guardrails (`skills/`, per-skill changelogs in `docs/changelogs/`).
- Orchestration and shared conventions: run order and client entry path ([orchestrator](docs/orchestrator/README.md)), the task-file write protocol and append-only changelog format ([conventions](docs/orchestrator/CONVENTIONS.md)), and credential handling with scoped tokens, a secrets manager, just-in-time fetch and an access log ([credentials](docs/orchestrator/CREDENTIALS.md)).
- Run on 8+ live sites between Aug and Oct 2026 (property agency, restaurants, manufacturer, retail, e-commerce; Estonia). Each produced a written audit in HTML/PDF/Markdown. Client names withheld.
- Audit types: comprehensive GEO/SEO, technical, analytics tracking, competitor intelligence.
- Every finding carries a severity, who fixes it (self-serve or developer), step-by-step remediation and a way to verify the fix.
- Per-project token and cost logging.

**Roadmap**
- Outcome tracking: before/after measurement per site (citations, traffic, fixes applied).
- Stand up the staging site and its golden file, so changes to the agents are regression-tested before release (the process is specified in `skill-release-manager`).
- Run the shared state layer (task file and per-client changelogs) live behind the dashboards (protocol documented in `docs/orchestrator/CONVENTIONS.md`).

## Built with

Claude Code, Hermes Agent (self-hosted, persistent memory), OmniRoute model routing.

## Author

Anthony D'Souza. Technical delivery leader building production AI agents.
