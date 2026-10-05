"""Render the read-only progress dashboard (kanban) from tasks.json.

  python tools/render_progress.py [output.html]

Follows skills/progress-dashboard: one column per status with counts, progress per
client as done/total recomputed on every render, stale waiting/blocked cards flagged,
and nothing ever written back to tasks.json.
"""

import html
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changelog  # noqa: E402
import tasks_store as ts  # noqa: E402

STALE_AFTER = timedelta(days=3)
COLUMNS = (("todo", "Todo"), ("in_progress", "In progress"), ("waiting", "Waiting"),
           ("blocked", "Blocked"), ("review", "Review"), ("done", "Done"))


def _age(task, now):
    try:
        return now - datetime.fromisoformat(task["updated_at"])
    except (KeyError, ValueError):
        return timedelta(0)


def render(tasks, now=None, has_changelog=None):
    now = now or datetime.now(timezone.utc)
    esc = lambda v: html.escape(str(v if v is not None else ""))  # noqa: E731
    clients = sorted({t["client"] for t in tasks})

    progress = ""
    for c in clients:
        mine = [t for t in tasks if t["client"] == c]
        pct = round(100 * sum(t["status"] == "done" for t in mine) / len(mine))
        progress += (f'<div class="client"><b>{esc(c)}</b> {pct}% '
                     f'<span class="bar"><i style="width:{pct}%"></i></span></div>')

    cols = ""
    for status, label in COLUMNS:
        cards = ""
        for t in (t for t in tasks if t["status"] == status):
            stale = status in ("waiting", "blocked") and _age(t, now) > STALE_AFTER
            unverified = status == "done" and has_changelog is not None and not has_changelog(t)
            reason = f'<div class="why">{esc(t.get("blocked_reason"))}</div>' if t.get("blocked_reason") else ""
            cards += (f'<div class="card{" stale" if stale else ""}"><b>{esc(t["id"])}</b> {esc(t.get("title"))}'
                      f'<div class="meta">{esc(t["client"])} | {esc(t.get("owner"))}'
                      f'{" | STALE" if stale else ""}{" | UNVERIFIED (no changelog entry)" if unverified else ""}</div>{reason}</div>')
        count = sum(t["status"] == status for t in tasks)
        cols += f'<section><h2>{label} ({count})</h2>{cards}</section>'

    return f"""<!doctype html><meta charset="utf-8"><title>Progress dashboard</title>
<style>body{{font:14px system-ui;margin:20px}}.board{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}
.card{{border:1px solid #bbb;border-radius:6px;padding:8px;margin:6px 0}}.stale{{border-color:#c33;background:#fdeeee}}
.meta,.why{{color:#555;font-size:12px}}.bar{{display:inline-block;width:120px;height:8px;background:#ddd;vertical-align:middle}}
.bar i{{display:block;height:8px;background:#2a9d8f}}.client{{margin:4px 0}}</style>
<h1>Progress dashboard</h1><div>{progress}</div><div class="board">{cols}</div>
<p class="meta">Generated {esc(now.isoformat(timespec="seconds"))} from tasks.json (read-only view)</p>"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0]) if argv else ts.default_state_dir().parent / "dashboard" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(ts.read_tasks(), has_changelog=lambda t: changelog.has_entry(t["client"], t["id"])),
        encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
