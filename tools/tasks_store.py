"""Shared task store for the agent pipeline.

Implements the write protocol from docs/orchestrator/CONVENTIONS.md:

1. acquire the lock with an atomic mkdir (.tasks.lock)
2. read the current tasks.json
3. apply the change in memory
4. write the full result to tasks.json.tmp
5. atomically rename tasks.json.tmp -> tasks.json
6. remove the lock directory

Do slow work (web fetches, LLM calls) before calling update_tasks(); the lock
is only held for the quick read-modify-write-rename.

State directory: $HERMES_STATE_DIR, else ~/.hermes/state.
"""

import json
import os
import random
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUSES = ("todo", "in_progress", "waiting", "blocked", "review", "done")
CLOSER = "project-manager"  # the only agent allowed to mark a task done


class LockTimeout(Exception):
    """Could not acquire the lock within max_wait seconds."""


class StaleLockError(Exception):
    """The lock is older than stale_after seconds. Surfaced, never broken silently."""


class NotAuthorized(Exception):
    """The actor is not allowed to make this change."""


class InvalidTask(ValueError):
    """A task failed validation and was rejected rather than silently dropped."""


def default_state_dir():
    return Path(os.environ.get("HERMES_STATE_DIR", Path.home() / ".hermes" / "state"))


def _now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@contextmanager
def tasks_lock(state_dir=None, max_wait=10.0, stale_after=300.0):
    """Hold the tasks lock. mkdir is atomic: it fails if the directory exists."""
    state_dir = Path(state_dir or default_state_dir())
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = state_dir / ".tasks.lock"
    deadline = time.monotonic() + max_wait
    delay = 0.005
    while True:
        try:
            os.mkdir(lock)
            break
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except FileNotFoundError:
                continue  # released between our mkdir and stat; try again at once
            if age > stale_after:
                raise StaleLockError(
                    f"{lock} is {age:.0f}s old (limit {stale_after:.0f}s). "
                    "A writer likely crashed. Investigate, then remove it by hand."
                )
            if time.monotonic() >= deadline:
                raise LockTimeout(f"could not acquire {lock} within {max_wait}s")
            time.sleep(delay + random.uniform(0, delay))  # short backoff with jitter
            delay = min(delay * 2, 0.25)
    try:
        yield
    finally:
        os.rmdir(lock)


def read_tasks(state_dir=None):
    """Read without locking. Safe because writers only ever rename a complete file."""
    path = Path(state_dir or default_state_dir()) / "tasks.json"
    for attempt in range(100):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except PermissionError:  # Windows: briefly unreadable while a writer swaps the file
            if attempt == 99:
                raise
            time.sleep(0.01)


def validate_task(task):
    for field in ("id", "client", "agent", "status"):
        if not task.get(field):
            raise InvalidTask(f"task is missing '{field}': {task!r}")
    if task["status"] not in VALID_STATUSES:
        raise InvalidTask(f"invalid status {task['status']!r} on {task['id']}")
    if task["status"] == "blocked" and not task.get("blocked_reason"):
        raise InvalidTask(f"{task['id']} is blocked but has no blocked_reason")


def _replace_with_retry(src, dst, attempts=100):
    """Atomic rename. On Windows it fails briefly while a reader has dst open, so retry."""
    for attempt in range(attempts):
        try:
            os.replace(src, dst)  # atomic: readers never see a partial file
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.01)


def update_tasks(change, state_dir=None, max_wait=10.0, stale_after=300.0):
    """Run change(tasks) -> tasks under the lock, then atomically replace tasks.json.

    `change` receives the current list and may mutate it or return a new list.
    Every task is validated before anything is written.
    """
    state_dir = Path(state_dir or default_state_dir())
    with tasks_lock(state_dir, max_wait, stale_after):
        tasks = read_tasks(state_dir)
        result = change(tasks)
        if result is None:
            result = tasks
        for task in result:
            validate_task(task)
        tmp = state_dir / "tasks.json.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        _replace_with_retry(tmp, state_dir / "tasks.json")
        return result


def add_task(task, state_dir=None, **lock_args):
    """Append a task. created_at is set once; updated_at changes on every transition."""
    task = {"owner": task.get("agent"), "blocked_reason": None, "revision_count": 0,
            "client_note": None, **task, "created_at": _now(), "updated_at": _now()}

    def change(tasks):
        if any(t["id"] == task["id"] for t in tasks):
            raise InvalidTask(f"duplicate task id {task['id']}")
        tasks.append(task)

    update_tasks(change, state_dir, **lock_args)
    return task


def set_status(task_id, status, actor, blocked_reason=None, state_dir=None, **lock_args):
    """Change a task's status as `actor`.

    - An agent may only change tasks it owns; project-manager may change any task.
    - Only project-manager may set `done`, and only if the client's changelog has an
      entry for the task. Other agents finish work by moving the task to `review`.
    """
    import changelog  # local import: changelog depends on this module

    def change(tasks):
        for t in tasks:
            if t["id"] != task_id:
                continue
            if actor != CLOSER and t.get("owner") != actor:
                raise NotAuthorized(f"{actor} does not own {task_id} (owner: {t.get('owner')})")
            if status == "done":
                if actor != CLOSER:
                    raise NotAuthorized(f"only {CLOSER} may mark a task done; move it to 'review' instead")
                if not changelog.has_entry(t["client"], task_id, state_dir):
                    raise InvalidTask(f"{task_id} has no changelog entry; it cannot be marked done")
            t["status"] = status
            t["blocked_reason"] = blocked_reason
            t["updated_at"] = _now()
            return
        raise InvalidTask(f"no such task {task_id}")

    update_tasks(change, state_dir, **lock_args)
