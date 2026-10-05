# Changelog — project-manager

## 1.0.0 — 2026-08-03
Initial version. Built from the a pilot client engagement checklist and the
9-agent architecture design (6 technical agents + project-manager +
progress-dashboard + skill-release-manager).

## 1.1.0 — 2026-08-03
Added Notifications section: Telegram as the delivery channel, three severity
tiers (critical / needs your decision / routine digest), and a 4-hour
unacknowledged-critical escalation.

## 1.2.0 — 2026-08-03
Engagement record now requires start_datetime (set by account-manager's
handoff, not payment or credential-verification time). project-manager no
longer self-initiates new engagements — only reacts to account-manager
handoffs or scheduled retainer triggers. Added account-manager's
"new engagement ready" approval request as a critical-tier notification.

## 1.3.0 — 2026-08-03
Added "onboarding stuck" as its own critical notification category,
distinct from "new engagement ready," fired by account-manager after
3 failed credential-verification attempts on the same credential.

## 1.6.0 - 2026-10-06
Project-manager is the only agent that marks tasks `done`, from `review`, after the safety gate; enforced by the task store.
