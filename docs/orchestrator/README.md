# GEO/SEO Pipeline Orchestrator

Not a content agent — this is the sequencing layer that runs the 6 technical skills below
in order within a single client run, carries findings between them, and prevents
duplicated or wasted work. `project-manager` sits one level above this: it decides *when*
a client run should happen at all and tracks everything across clients and time.

## Skills (install order matters for first understanding, not for install itself)
1. `technical-health`
2. `metadata-onpage-seo`
3. `geo-ai-visibility`
4. `analytics-tracking`
5. `content-expansion`
6. `client-reporting`
7. `project-manager` — the engagement layer above the other six; see its own SKILL.md
8. `progress-dashboard` — read-only, visualizes state from all agents; see its own SKILL.md
9. `skill-release-manager` — gates changes to skills 1–8 themselves; see its own SKILL.md. Not part of the per-client run sequence — it runs whenever a SKILL.md changes, against the staging client only.
10. `account-manager` — sits in front of everything else, but only for a client's very first kickoff. Handles payment confirmation, credential verification, and your explicit go-ahead. project-manager never starts a new engagement without a handoff from this agent. Not involved in day-to-day work on an existing engagement — see its own SKILL.md.

## Where a new client enters

`account-manager` → (your explicit approval) → `project-manager` → `orchestrator` →
the 6 technical agents. This is the only path a brand-new engagement can take. An
existing engagement's scheduled retainer runs skip account-manager entirely and go
straight from project-manager's schedule to the orchestrator.

## Where a run comes from

`project-manager` decides a client run should start (new engagement, a due retainer
check, or a client resolving a pending decision) and hands the orchestrator a "go"
signal for that client. The orchestrator doesn't decide *when* — it only decides *what
order* once triggered.

## Run sequence per client

1. **Technical Health** runs first. No point auditing metadata on pages that aren't even
   serving correctly.
2. **Metadata & On-Page SEO** runs next, fed Technical Health's findings — skip pages
   already confirmed broken/blocked until infra is fixed.
3. **GEO / AI-Visibility** runs after Metadata — schema and llms.txt work depends on
   metadata already being correct.
4. **Analytics & Tracking** runs in parallel with the above — independent of the content
   pipeline, but needs Technical Health's redirect/URL findings to interpret indexing
   data correctly.
5. **Content Expansion** output is held for explicit client approval before being marked
   "done" anywhere downstream — this is the one output type that must never auto-publish.
6. **Client Reporting** runs last, receiving everything tagged by audience
   (client / developer) and status bucket (completed / waiting on third party /
   needs your decision).

## State
Maintain a running per-client checklist state (e.g. a JSON or markdown file per client,
keyed by domain) so re-runs on the same client only re-check what's changed rather than
redoing everything from scratch.

## Install (Hermes)
Drop each numbered folder's SKILL.md into `~/.hermes/skills/<skill-name>/SKILL.md` on the
Hermes host, or publish via `hermes skills install` if using a skills.sh-hosted repo.
Skills are model-invoked — Hermes decides when to load `technical-health`,
`metadata-onpage-seo`, etc. based on their `description:` frontmatter, so the orchestrator's
job is really just: schedule the per-client run, and instruct Hermes (via the cron
task prompt) to follow the sequence above rather than run agents in arbitrary order.

## Why 6 + 1, not fewer or more
**Fewer** (one big "SEO agent") loses the audience-translation discipline — technical
findings kept needing two different write-ups in practice.

**More** (a separate agent per individual check) creates unnecessary handoff overhead for
tasks that are naturally sequential and share context — e.g. the caching check and the
redirect check are both "is the server actually doing what it claims" and belong together.

Six is the natural seam: each agent maps to a distinct *type of judgment* (infra
correctness, on-page optimization, AI-specific structuring, measurement, writing,
communication) rather than a specific tool or checklist item — reusable across different
client stacks even though the current checklist items were built against a
WordPress/Yoast/Object Cache Pro site.
