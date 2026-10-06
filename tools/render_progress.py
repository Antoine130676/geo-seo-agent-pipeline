"""Render the read-only progress dashboard (kanban) from the shared state.

  python tools/render_progress.py [output.html]

Uses tools/dashboard_template.html. Reads tasks.json, the per-client changelogs and
engagements.json from the state directory and embeds them in the page. Nothing is
ever written back to the state files (see skills/progress-dashboard).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changelog  # noqa: E402
import tasks_store as ts  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "dashboard_template.html"


def _embed(value):
    """JSON safe to place inside a <script> block."""
    return (json.dumps(value).replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def recent_changelog(state_dir=None, limit=30):
    entries = []
    folder = Path(state_dir or ts.default_state_dir()) / "changelog"
    for path in folder.glob("*.jsonl") if folder.exists() else []:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a bad line is skipped here; it never blocks the dashboard
    return sorted(entries, key=lambda e: e.get("timestamp", ""), reverse=True)[:limit]


def read_engagements(state_dir=None):
    path = Path(state_dir or ts.default_state_dir()) / "engagements.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def render(tasks, changelog_entries=None, engagements=None, has_changelog=None):
    """Return the dashboard HTML. Done tasks with no changelog entry are flagged unverified."""
    tasks = [dict(t) for t in tasks]
    if has_changelog is not None:
        for t in tasks:
            t["unverified"] = t["status"] == "done" and not has_changelog(t)
    page = TEMPLATE.read_text(encoding="utf-8")
    for token, empty, value in (("/*__TASKS__*/[]", "[]", tasks),
                                ("/*__CHANGELOG__*/[]", "[]", changelog_entries or []),
                                ("/*__ENGAGEMENTS__*/{}", "{}", engagements or {})):
        assert token in page, f"template is missing {token}"
        page = page.replace(token, _embed(value))
    return page


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    state = ts.default_state_dir()
    out = Path(argv[0]) if argv else state.parent / "dashboard" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(ts.read_tasks(state), recent_changelog(state), read_engagements(state),
                          has_changelog=lambda t: changelog.has_entry(t["client"], t["id"], state)),
                   encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
