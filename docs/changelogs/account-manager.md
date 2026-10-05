# Changelog — account-manager

## 1.0.0 — 2026-08-03
Initial version. Payment confirmation, credential verification, and
explicit human go-ahead before project-manager creates a new engagement.

## 1.1.0 — 2026-08-03
Added a 3-attempt cap per credential before escalating to a critical
"onboarding stuck" Telegram alert, tracked per-credential rather than
per-client so one bad credential doesn't reset others' clean passes.
