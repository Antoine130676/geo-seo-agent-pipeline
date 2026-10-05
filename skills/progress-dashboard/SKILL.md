---
name: progress-dashboard
description: Maintain a backend progress dashboard showing the status of every task the Project Manager has assigned across all client agents (Technical Health, Metadata, GEO, Analytics, Content Expansion, Client Reporting). Use whenever a new task is created or updated by any agent, on a schedule to regenerate the dashboard view, or when asked "what's the status of everything right now."
version: 1.5.0
---

# Progress Dashboard Agent

## Job
Give a single, always-current view of every task in flight — across every client and every agent — without anyone having to ask each agent individually.

## Data contract (read this first)

All agents write task updates to one shared state file so the dashboard has a single
source of truth: `~/.hermes/state/tasks.json`, following the locking and write protocol
in `../00-orchestrator/CONVENTIONS.md`. Never write to this file without that protocol —
concurrent unprotected writes will corrupt it.

Each task is an object:

```json
{
  "id": "th-0042",
  "client": "example.com",
  "agent": "technical-health",
  "owner": "technical-health",
  "title": "Verify redirect fires as real HTTP redirect, not just saved field",
  "status": "in_progress",
  "created_at": "2026-08-01T09:12:00+03:00",
  "updated_at": "2026-08-03T14:40:00+03:00",
  "blocked_reason": null,
  "assigned_by": "project-manager"
}
```

`status` is always one of: `todo`, `in_progress`, `waiting`, `blocked`, `review`, `done`. `review` means the owning agent finished and is waiting for project-manager to verify; only project-manager sets `done`.
`agent` is always one of the 6 technical agent skill names — the capability that created
the task. `owner` starts equal to `agent` but is a separate field because
project-manager can reassign an in-flight task to a different agent; the dashboard
always displays `owner`, never assumes it matches `agent`.
`created_at` is set once, when the task is first written, and never changes.
`updated_at` changes on every status transition.
`blocked_reason` is required (non-null) whenever `status` is `blocked`.
`revision_count` (default 0) and `client_note` (default null) apply to tasks that can be
client-approved — see `../00-orchestrator/CONVENTIONS.md`, "Revision loop." A task with
`revision_count >= 2` that's awaiting a further decision should render distinctly (it's
escalated to the human, not a normal in-flight task).

## Checklist

- [ ] On every task creation or status change by any agent, append/update the entry in `tasks.json` rather than each agent keeping its own private log.
- [ ] Validate: every task has a `client`, an `agent` from the known set, and a valid `status` — reject/flag malformed entries rather than silently dropping them.
- [ ] Regenerate the dashboard HTML/view whenever `tasks.json` changes, or on a schedule (e.g. every 15 minutes) — whichever is more frequent for active engagements.
- [ ] Compute per-agent queue depth (count of tasks in each status) and per-client rollups.
- [ ] Compute per-client progress as `done tasks / total tasks` for that client, rounded to the nearest whole percent — recompute on every regeneration rather than storing a cached percentage that can drift from the underlying task counts.
- [ ] Surface staleness: any task in `waiting` or `blocked` with `updated_at` older than an agreed threshold (default 3 days) gets flagged the same way Project Manager flags stale items — the dashboard should visually distinguish "normal wait" from "stale, needs a nudge."
- [ ] Never let the dashboard silently drop a task — a task disappearing from view because of a malformed write is worse than a visibly broken entry.
- [ ] For every task marked `done`, confirm a matching entry exists in that client's changelog file. A `done` task with no changelog entry is a data-integrity error — render it with a distinct "unverified" marker rather than treating it as a normal completed task.
- [ ] Surface a rolling "recent changes" feed pulled directly from the changelog files, not from `tasks.json` — the changelog has the detail (before/after, verification method) that the status file doesn't.
- [ ] Keep the dashboard read-only. It visualizes state; it never writes task changes back. Status changes only come from the agent that owns that task, or from Project Manager reassigning it.
- [ ] Exclude closed engagements (per `engagements.json`, `closed_datetime` set) from the default kanban view, but keep them accessible via a separate filter — closed history stays queryable, just not mixed into the active board.

## Output format
A static HTML file (or locally served page) at `~/.hermes/dashboard/index.html`, regenerated on every state change, laid out as a kanban board:
- One column per status (Todo, In progress, Waiting, Blocked, Review, Done), each headed by a count
- One card per task, filterable by client — card shows task ID, owner, title, created date, last-updated age, client, and blocked reason where relevant
- A progress-by-client panel above the board: percentage of that client's tasks marked `done`, as both a number and a filled bar, next to the client's engagement start date/time — recalculated on every render, never cached from a prior view
- Each client filter shows that client's engagement `start_datetime` (from project-manager's engagement record, set by account-manager's handoff) directly beside the client name — never inferred from the first task's timestamp, since that can predate or postdate actual kickoff
- Stale cards (waiting/blocked past the threshold) visually distinguished within their column, not moved to a separate panel — status is what the column already encodes
- A "recent changes" feed below the board, pulled from the changelog files

## Handoff
Reads from every technical agent and from Project Manager (who is the one that assigns tasks and moves them between agents). Writes nothing back except the rendered dashboard file itself.

Rendered by `tools/render_progress.py`, which is read-only. A card in `done` with no changelog entry is marked UNVERIFIED.
