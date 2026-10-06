import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import render_progress as rp  # noqa: E402

CHANGELOG_ARGS = ("--client", "example.com", "--agent", "technical-health", "--task-id", "t-0",
                  "--action", "Flushed object cache", "--before", "stale page", "--after", "fresh page",
                  "--verified-by", "technical-health", "--verification-method", "incognito fetch after flush",
                  "--side-effects-checked", "no other pages changed")


class CliAndDashboardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.env = {**os.environ, "HERMES_STATE_DIR": self._tmp.name}

    def tearDown(self):
        self._tmp.cleanup()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "tasks_cli.py"), *args],
                              env=self.env, capture_output=True, text=True, timeout=60)

    def add(self, i="t-0", agent="technical-health"):
        r = self.cli("add", "--id", i, "--client", "example.com", "--agent", agent, "--title", agent)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_full_lifecycle_only_project_manager_closes(self):
        self.add()
        self.assertEqual(self.cli("status", "t-0", "in_progress", "--as", "technical-health").returncode, 0)
        self.assertEqual(self.cli("status", "t-0", "review", "--as", "technical-health").returncode, 0)
        # the owner cannot close its own task
        r = self.cli("status", "t-0", "done", "--as", "technical-health")
        self.assertEqual(r.returncode, 5, r.stderr)
        # project-manager cannot close it without a changelog entry (safety gate)
        r = self.cli("status", "t-0", "done", "--as", "project-manager")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(self.cli("changelog", *CHANGELOG_ARGS).returncode, 0)
        self.assertEqual(self.cli("status", "t-0", "done", "--as", "project-manager").returncode, 0)
        done = json.loads(self.cli("list", "--status", "done", "--json").stdout)
        self.assertEqual([t["id"] for t in done], ["t-0"])

    def test_agent_cannot_touch_another_agents_task(self):
        self.add()
        r = self.cli("status", "t-0", "in_progress", "--as", "metadata-onpage-seo")
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertEqual(self.cli("status", "t-0", "in_progress", "--as", "project-manager").returncode, 0)

    def test_changelog_rejects_placeholder_verification(self):
        args = list(CHANGELOG_ARGS)
        args[args.index("--verification-method") + 1] = "N/A"
        r = self.cli("changelog", *args)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse((Path(self._tmp.name) / "changelog" / "example.com.jsonl").exists())

    def test_invalid_input_exits_2_and_changes_nothing(self):
        self.add("x")
        self.assertEqual(self.cli("status", "x", "blocked", "--as", "technical-health").returncode, 2)
        self.assertEqual(self.cli("add", "--id", "x", "--client", "c", "--agent", "a").returncode, 2)
        self.assertEqual(json.loads(self.cli("list", "--json").stdout)[0]["status"], "todo")

    def test_dashboard_embeds_data_flags_unverified_and_is_script_safe(self):
        base = {"client": "example.com", "agent": "technical-health", "owner": "technical-health",
                "updated_at": "2026-10-01T09:00:00+03:00", "created_at": "2026-10-01T09:00:00+03:00"}
        tasks = [
            {**base, "id": "1", "status": "done", "title": "closed without a log"},
            {**base, "id": "2", "status": "blocked", "title": "</script><script>alert(1)</script>",
             "blocked_reason": "waiting on DNS"},
        ]
        page = rp.render(tasks, [{"timestamp": "2026-10-01T10:00", "client": "example.com", "task_id": "1",
                                  "action": "x", "verified_by": None, "verification_method": None}],
                         {"example.com": {"start_datetime": "2026-09-30T09:00:00+03:00"}},
                         has_changelog=lambda t: False)
        self.assertIn('"unverified": true', page)             # done, but no changelog entry
        self.assertIn('label: "Review"', page)                # the review column exists
        self.assertIn("2026-09-30T09:00:00+03:00", page)      # engagement start date embedded
        self.assertNotIn("</script><script>alert", page)      # embedded data cannot break out of the script
        self.assertIn("function esc(", page)                  # and cards escape task text when rendered
        self.assertNotIn("__TASKS__", page)                   # every placeholder was filled


if __name__ == "__main__":
    unittest.main()
