"""Demo: the pipeline's task rules, live, in about a second. Uses fake data in a temp folder.

    python examples/demo.py                      # run the walkthrough
    python examples/demo.py --out dashboard.html # also keep the rendered dashboard
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
tmp = tempfile.TemporaryDirectory()
os.environ["HERMES_STATE_DIR"] = tmp.name

import changelog  # noqa: E402
import render_progress  # noqa: E402
import tasks_store as ts  # noqa: E402

PM = "project-manager"


def step(text):
    print(f"\n== {text}")


def refused(label, fn, expect):
    try:
        fn()
    except expect as e:
        print(f"   REFUSED  {label}\n            -> {e}")
    else:
        raise SystemExit(f"demo failed: '{label}' should have been refused")


def new(task_id, agent, title):
    ts.add_task({"id": task_id, "client": "example.com", "agent": agent, "title": title,
                 "status": "todo", "assigned_by": PM})


step("Project manager assigns three tasks")
new("th-1", "technical-health", "Verify the redirect is a real HTTP redirect")
new("md-1", "metadata-onpage-seo", "Draft missing meta descriptions")
new("geo-1", "geo-ai-visibility", "Check llms.txt against the spec")
ts.set_status("th-1", "in_progress", "technical-health")
ts.set_status("md-1", "in_progress", "metadata-onpage-seo")
ts.set_status("geo-1", "blocked", "geo-ai-visibility", blocked_reason="waiting on CMS access")
print("   th-1 and md-1 in progress; geo-1 blocked with a reason")

step("Rule 1: an agent cannot close its own task")
refused("technical-health marks th-1 done", lambda: ts.set_status("th-1", "done", "technical-health"),
        ts.NotAuthorized)

step("Rule 2: an agent cannot touch another agent's task")
refused("metadata-onpage-seo edits th-1", lambda: ts.set_status("th-1", "review", "metadata-onpage-seo"),
        ts.NotAuthorized)

step("Rule 3: a blocked task must say why")
refused("md-1 set to blocked with no reason", lambda: ts.set_status("md-1", "blocked", "metadata-onpage-seo"),
        ts.InvalidTask)

step("Technical-health finishes th-1 and asks for review")
ts.set_status("th-1", "review", "technical-health")
print("   th-1 -> review")

step("Rule 4: even the project manager cannot close without a changelog entry")
refused("project-manager marks th-1 done", lambda: ts.set_status("th-1", "done", PM), ts.InvalidTask)

step("The agent logs what it did and how it was verified (placeholders are rejected)")
entry = {"client": "example.com", "agent": "technical-health", "task_id": "th-1",
         "action": "Fixed redirect rule for /old-services", "before": "301 missing, page 404s",
         "after": "301 to /services", "verified_by": "technical-health",
         "verification_method": "incognito fetch showing the 301 header", "backup_ref": "redirects-2026-10-06.json",
         "rollback_available": True, "side_effects_checked": "no other redirects changed", "notes": None}
refused("changelog entry with verification_method 'N/A'",
        lambda: changelog.append_entry({**entry, "verification_method": "N/A"}), changelog.InvalidEntry)
changelog.append_entry(entry)
print("   changelog entry written")

step("Now the project manager can close it")
ts.set_status("th-1", "done", PM)
print("   th-1 -> done")

step("Progress dashboard (read-only view of the same file)")
page = render_progress.render(ts.read_tasks(), has_changelog=lambda t: changelog.has_entry(t["client"], t["id"]))
out = None
if "--out" in sys.argv:
    out = Path(sys.argv[sys.argv.index("--out") + 1])
    out.write_text(page, encoding="utf-8")
    print(f"   written to {out}")
counts = {}
for t in ts.read_tasks():
    counts[t["status"]] = counts.get(t["status"], 0) + 1
print("   status counts:", counts)
print("\nAll four rules held.")
tmp.cleanup()
