"""Append-only per-client changelog (see docs/orchestrator/CONVENTIONS.md).

One JSONL file per client at <state_dir>/changelog/<client>.jsonl. Entries are only
ever appended. A correction is a new entry, never an edit.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import tasks_store as ts

KEYS = ("client", "agent", "task_id", "action", "before", "after", "verified_by",
        "verification_method", "backup_ref", "rollback_available",
        "side_effects_checked", "notes")
MUST_BE_REAL_TEXT = ("verified_by", "verification_method", "side_effects_checked")
PLACEHOLDERS = {"", "n/a", "na", "none", "null", "-", "tbd"}


class InvalidEntry(ValueError):
    """A changelog entry that skips the safety gate's required fields."""


def _path(client, state_dir):
    if not client or "/" in client or "\\" in client or client.startswith(".."):
        raise InvalidEntry(f"unsafe client name {client!r}")
    return Path(state_dir or ts.default_state_dir()) / "changelog" / f"{client}.jsonl"


def append_entry(entry, state_dir=None):
    missing = [k for k in KEYS if k not in entry]
    if missing:
        raise InvalidEntry(f"missing keys (write null explicitly if not applicable): {missing}")
    for k in MUST_BE_REAL_TEXT:
        if str(entry[k] or "").strip().lower() in PLACEHOLDERS:
            raise InvalidEntry(f"'{k}' must describe real work, not a placeholder: {entry[k]!r}")
    path = _path(entry["client"], state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    line = json.dumps({"timestamp": stamp, **entry}) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    try:
        os.write(fd, line.encode("utf-8"))  # one write, appended: lines never interleave
        os.fsync(fd)
    finally:
        os.close(fd)


def has_entry(client, task_id, state_dir=None):
    try:
        text = _path(client, state_dir).read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    for line in text.splitlines():
        try:
            if json.loads(line).get("task_id") == task_id:
                return True
        except json.JSONDecodeError:
            continue
    return False
