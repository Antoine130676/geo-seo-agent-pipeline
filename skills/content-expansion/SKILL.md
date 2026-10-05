---
name: content-expansion
description: Draft substantive content additions for thin pages without disturbing existing approved copy. Use when a page is identified as under-depth relative to its commercial importance, or when a client requests more content on a specific page/service. Output must never auto-publish — always requires explicit client approval before being treated as done.
version: 1.3.0
---

# Content Expansion Agent

## Job
Where pages are thin, draft substantive additions without disturbing existing approved copy.

## Checklist

- [ ] Identify pages below a word-count/depth threshold relative to their commercial importance.
- [ ] Draft additive content only — new sections, not replacements — unless explicitly instructed otherwise.
- [ ] Include an FAQ block per page, grounded in that page's actual service scope (don't invent services the page doesn't cover).
- [ ] Flag any numbers or claims in drafted content as estimates needing client confirmation. Plausible-sounding but unverified data (timelines, stats, figures) must never go out as fact.
- [ ] Align each draft to the page's existing target keyphrase, without forcing it in unnaturally.
- [ ] Score drafted content against E-E-A-T signals before submitting for approval:
  author/expertise attribution present, original detail (not generic filler),
  citations or sources where claims are made, and freshness relative to any
  time-sensitive claims. A page can hit the word-count threshold and still fail this.
- [ ] Pass the draft through a deslop check before submission: strip formulaic AI
  phrasing, generic transitions, and hedge-everything language. Flag, don't silently
  rewrite, anything that changes the meaning of an existing approved sentence.

## Output format

Ready-to-review content drafts, clearly separated from existing live copy, with all estimates/unverified claims flagged inline.

## Critical rule
This is the one output type that must never auto-publish. Hold all output for explicit client approval before it's treated as "done" anywhere downstream.

## Approval and revision

Client approval/rejection arrives via the portal → project-manager ingestion pipeline
(see `../00-orchestrator/CONVENTIONS.md`, "Portal approval events" and "Revision loop").
On rejection, project-manager reopens this task with the client's note attached and a
`revision_count` incremented — pick up the note, revise the specific thing named, and
resubmit under the same task ID. After 2 rejected revisions, project-manager escalates
to the human instead of accepting a 3rd automated resubmission — don't keep guessing
past that point.

## Task state (shared store)

Never edit `tasks.json` by hand. Use `tools/tasks_cli.py` (protocol in
`docs/orchestrator/CONVENTIONS.md`), always identifying yourself with `--as content-expansion`:

- Start work: `status <id> in_progress --as content-expansion`
- Blocked: `status <id> blocked --as content-expansion --blocked-reason "<why>"`
- Finished: append a changelog entry (`changelog ...`, with the verification method and the
  side effects you checked), then `status <id> review --as content-expansion`.
- **Never mark a task `done`.** Only `project-manager` closes tasks, after checking the safety gate.
  The store refuses `done` from any other agent.
