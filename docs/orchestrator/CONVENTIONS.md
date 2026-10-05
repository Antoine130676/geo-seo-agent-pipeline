# Shared conventions — state file, locking, and changelog

Every agent (the 6 technical agents, project-manager, progress-dashboard) follows this
protocol. It exists so concurrent writes never corrupt state and so every change is
traceable after the fact.

## Files

```
~/.hermes/state/tasks.json          current status of every task (progress-dashboard reads this)
~/.hermes/state/.tasks.lock         lock directory, present only while a write is in progress
~/.hermes/state/changelog/          one append-only JSONL file per client
  example.com.jsonl
  another-client.com.jsonl
  ...
~/.hermes/state/staging-expected.json   golden file: known issues on the staging site
~/.hermes/state/skill-releases.jsonl    append-only log of every skill promotion/rollback
~/.hermes/skills/                   live skills — never edited directly
~/.hermes/skills-staging/           where skill edits happen before testing
~/.hermes/skills-archive/<name>/<version>/   last 3 promoted versions of each skill, for rollback
```

## Notification channel

All human-facing alerts go through Hermes's Telegram gateway (configured once at
`~/.hermes/gateways/telegram`). See project-manager's Notifications section for the
severity tiers and message format — only project-manager decides what gets sent and
when; other agents raise events, they don't message you directly.

## Credentials

Any agent that needs client access (CMS, GA4, Search Console) follows `CREDENTIALS.md`
in this same directory — never stores a raw secret in `tasks.json`, the changelog, or
its own memory beyond the single task that needed it.

## Write protocol for tasks.json (prevents corruption from concurrent agents)

1. Acquire the lock: `mkdir ~/.hermes/state/.tasks.lock` — this is atomic on POSIX, so if
   it fails because the directory exists, another agent is writing. Wait and retry
   (short backoff, cap retries — don't spin forever; if a lock is stale after N minutes,
   that's a bug to surface, not silently break through).
2. Read the current `tasks.json`.
3. Apply your change in memory.
4. Write the full result to `tasks.json.tmp`.
5. Atomically rename `tasks.json.tmp` → `tasks.json` (rename is atomic — readers never
   see a half-written file).
6. Remove the lock directory.

No agent ever edits `tasks.json` in place or holds the lock across a slow operation
(a web fetch, an LLM call). Do the slow work first, then lock only for the quick
read-modify-write-rename.

## Changelog entry (append one line per change, ever)

Changelogs are append-only. Never edit or delete a past entry — if something was wrong,
add a new entry that corrects it, so the history stays honest.

```json
{
  "timestamp": "2026-08-03T14:40:00+03:00",
  "client": "example.com",
  "agent": "metadata-onpage-seo",
  "task_id": "md-0018",
  "action": "Updated meta description on /services from empty to drafted copy",
  "before": "meta description: (empty)",
  "after": "meta description: \"...\" (147px, within limit)",
  "verified_by": "metadata-onpage-seo",
  "verification_method": "out-of-band view-source fetch after publish",
  "backup_ref": "example-services-pre-2026-08-03.html",
  "rollback_available": true,
  "side_effects_checked": "confirmed no other page referenced the old description; slug unchanged",
  "notes": null
}
```

Every field above is required except `notes`. If a field genuinely doesn't apply
(e.g. no backup possible for a config toggle), write `null` explicitly rather than
omitting the key — an omitted key is indistinguishable from an oversight.

## Tooling

`tools/tasks_store.py` implements the write protocol above; agents call it through `tools/tasks_cli.py`
and never edit `tasks.json` by hand. Valid statuses: `todo`, `in_progress`, `waiting`, `blocked`,
`review`, `done`.

## Verification gate (see project-manager SKILL.md for the full policy)

Task-owning agents never mark a task `done`. They append a changelog entry with
`verified_by`, `verification_method`, and `side_effects_checked` filled in, then move the task to
`review`. Only `project-manager` sets `done`, and `tools/tasks_store.py` refuses it unless the
client's changelog has an entry for the task. `progress-dashboard` treats a `done` task with a missing changelog entry as
a data-integrity error, not a normal state, and surfaces it.
