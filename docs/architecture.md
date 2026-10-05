# Architecture

## Layers

| Layer | Agents | Responsibility |
|---|---|---|
| Intake | Account Manager | Payment, credentials, human approval. Runs once per client. |
| Engagement | Project Manager, Skill Release Manager | Multi-client priorities, safety gate, notifications; testing the agents themselves |
| Orchestration | geo-client-workflow | Execution gate, parallel runs, cost log, project folder structure |
| Execution | 7 technical agents | The actual audit/fix/report work per client |
| Visibility | Progress Dashboard, Performance Dashboard | Internal task state; client-facing outcome view |

## Run order within one client run

1. **Technical Health** first. Everything else depends on infra being confirmed working.
2. **Metadata & On-Page SEO** after it, skipping pages Technical Health found broken.
3. **GEO / AI-Visibility** after Metadata. Schema and llms.txt need correct metadata underneath.
4. **Analytics & Tracking** and **Backlink & Authority** in parallel with the above. They are independent of the on-page chain.
5. **Content Expansion** where pages are thin; output waits for client approval.
6. **Client Reporting** last, once findings are tagged by audience and status bucket.

Status buckets on every item: **Completed**, **Waiting on a third party**, **Needs your decision**.

## Shared state contract (as specified)

All agents write to one task file so the dashboards have a single source of truth. A task carries:

```json
{
  "id": "th-0042",
  "client": "example.com",
  "agent": "technical-health",
  "owner": "technical-health",
  "title": "Verify redirect fires as a real HTTP redirect, not just a saved field",
  "status": "in_progress",
  "created_at": "2026-08-01T09:12:00+03:00",
  "updated_at": "2026-08-03T14:40:00+03:00",
  "blocked_reason": null,
  "assigned_by": "project-manager"
}
```

- `status` is one of `todo | in_progress | waiting | blocked | review | done`. Agents finish at `review`; only project-manager sets `done`.
- `agent` is the capability that created the task; `owner` can differ after reassignment.
- `blocked_reason` is required when `status` is `blocked`.
- `revision_count` and `client_note` support the client-approval loop (two rejections escalate to the human).
- Each client has an append-only changelog. Corrections are new entries, never edits.

## Safety gate (before any task is `done`)

0. Only project-manager marks a task `done` (enforced in code), moving it from `review`.
1. Changelog entry with `verified_by`, `verification_method`, `side_effects_checked`.
2. Backup or pre-change snapshot referenced for any live-site change.
3. Out-of-band verification, not the tool's own cached fetch.
4. Rollback recorded, or explicitly acknowledged as unavailable beforehand.
5. Anything irreversible or out of scope becomes a "needs your decision" item instead of auto-closing.

## Notification tiers

- **Critical, immediate:** rollbacks, `done` task with no changelog entry, blocked with no rollback plan, "new engagement ready", "onboarding stuck".
- **Needs your decision, immediate:** scope creep, brand collision, disavow candidates, outreach drafts.
- **Routine, daily digest:** stale waits, weekly priorities, engagement summary.

## Releasing changes to the agents

Edit in staging, run the whole pipeline against a disposable staging site with seeded issues, compare to a golden file, promote only on a full pass, archive the last three versions, and log every promotion or rollback.

## Roadmap notes

Shared conventions and credential handling are documented in [docs/orchestrator](orchestrator/). The staging site and its golden file are the next pieces to stand up.
