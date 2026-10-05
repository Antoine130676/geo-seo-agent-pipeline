# Changelog — progress-dashboard

## 1.0.0 — 2026-08-03
Initial version. Built from the a pilot client engagement checklist and the
9-agent architecture design (6 technical agents + project-manager +
progress-dashboard + skill-release-manager).

## 1.1.0 — 2026-08-03
Switched layout from queue-depth bars + list to a kanban board — one column
per status, cards per task, stale items flagged in place rather than in a
separate panel.

## 1.2.0 — 2026-08-03
Client filter chips and page header now show engagement start_datetime
beside the client name, sourced from project-manager's engagement record.

## 1.3.0 — 2026-08-03
Cards now show created date and owner explicitly (owner is a distinct field
from agent, since project-manager can reassign a task). Added a per-client
progress panel (percent done + bar) above the board, recomputed on every
render.
