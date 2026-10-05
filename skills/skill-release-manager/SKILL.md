---
name: skill-release-manager
description: Version, test, and gate any change to a SKILL.md before it's allowed to run against a real client. Use whenever a skill file is edited, before promoting a staged skill change to the live skills directory, or when asked to review/rollback a recent skill change. This is the only agent allowed to move a file from staging into ~/.hermes/skills/.
version: 1.1.0
---

# Skill Release Manager

## Job
Catch regressions in the agents themselves before they run against a real client. A bug
in a SKILL.md is worse than a bug in a single task — it repeats across every client the
agent touches until caught.

## Why this exists
Every other agent in this system is gated on verifying *its own output*. Nothing was
gating changes to the *instructions* those agents follow. An edited SKILL.md goes live
immediately and silently changes behavior for every client on the next run — that's the
regression path this agent closes.

## Versioning

- [ ] Every SKILL.md carries a `version:` field in its frontmatter (semver: MAJOR.MINOR.PATCH).
- [ ] Every skill has a sibling `CHANGELOG.md` — one entry per version, with date, what changed, and why.
- [ ] No skill file is edited directly in `~/.hermes/skills/`. Edits happen in `~/.hermes/skills-staging/<skill-name>/`, mirroring the live structure.
- [ ] A version bump is required for any change to the Checklist or Handoff sections. Wording/typo fixes to prose don't require a bump; behavior changes always do.

## The staging client

- [ ] Maintain one designated staging site — a real, disposable site you control (not a live client) with known, deliberately seeded issues: a broken redirect, an empty meta description, a missing WebSite schema description, an unlabeled interactive element, etc.
- [ ] Keep a golden file at `~/.hermes/state/staging-expected.json` listing every issue the staging site is known to have and which agent should catch it.
- [ ] When the staging site's known issues change (new one seeded, an old one intentionally fixed), update the golden file in the same change — an out-of-date golden file makes every future test meaningless.

## Test-and-promote checklist

Run for every staged skill change before it can go live:

- [ ] Run the staged skill against the staging client only — never against a real client.
- [ ] Compare findings written to `tasks.json` against the golden file: every previously-caught issue must still be caught (no silent regression), and no new finding should appear that isn't real (no new false positive introduced by the change).
- [ ] If the change was meant to add new detection capability, confirm it actually catches the new case the golden file was updated for — a version bump with no corresponding new-catch is suspicious, flag it.
- [ ] Run the full 6-agent + orchestrator sequence against staging, not just the one changed skill — a change to one agent's output format can silently break a downstream agent's parsing.
- [ ] Confirm the changed skill still writes valid entries to `tasks.json` and the changelog per `../00-orchestrator/CONVENTIONS.md` — a schema drift here breaks `progress-dashboard` invisibly.

## Promotion

- [ ] Only on a full pass: copy the staged skill from `~/.hermes/skills-staging/<name>/` to `~/.hermes/skills/<name>/`, bump the version, append the changelog entry with a timestamp, and record the promotion itself as an entry in `~/.hermes/state/skill-releases.jsonl` (fields: `timestamp`, `skill`, `from_version`, `to_version`, `tested_against`, `result`).
- [ ] On any failure, the change stays in staging. Report exactly which expected finding was missed or which unexpected finding appeared — never promote "mostly passing."
- [ ] Keep the previous 3 promoted versions of every skill archived at `~/.hermes/skills-archive/<name>/<version>/` so a bad promotion can be rolled back by copying the prior version back into `~/.hermes/skills/`.

## Rollback

- [ ] If a promoted skill causes a real problem on an actual client (caught via the safety gate, a client complaint, or a `progress-dashboard` integrity flag), roll back immediately: restore the prior version from the archive, log the rollback in `skill-releases.jsonl` with `result: "rolled_back"` and why, and only re-attempt promotion after the staging test is updated to cover whatever was missed.
- [ ] A rollback is never silent — it always produces a "needs your decision" item for Project Manager, since it means a bug reached a real client despite the gate. This is a critical-tier event: it goes out on Telegram immediately, not in a daily digest (see project-manager's Notifications section).

## What this agent explicitly does not do
It doesn't write or improve the other skills' logic — that's still you (or another Claude
session) editing the SKILL.md. This agent only tests, versions, and gates the promotion.
It never edits checklist content itself.
