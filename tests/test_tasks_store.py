import json
import multiprocessing as mp
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import tasks_store as ts  # noqa: E402

WRITERS, PER_WRITER = 8, 25


def _writer(state_dir, worker):
    for i in range(PER_WRITER):
        ts.add_task({"id": f"w{worker}-{i}", "client": "example.com",
                     "agent": "technical-health", "status": "todo"},
                    state_dir=state_dir, max_wait=60)


class TasksStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_concurrent_writers_lose_nothing(self):
        procs = [mp.Process(target=_writer, args=(self.dir, w)) for w in range(WRITERS)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(120)
            self.assertEqual(p.exitcode, 0)
        ids = [t["id"] for t in ts.read_tasks(self.dir)]
        self.assertEqual(len(ids), WRITERS * PER_WRITER)
        self.assertEqual(len(set(ids)), WRITERS * PER_WRITER)
        self.assertFalse((Path(self.dir) / ".tasks.lock").exists())

    def test_readers_never_see_a_partial_file(self):
        stop, bad, reads = threading.Event(), [], []

        def reader():
            while not stop.is_set():
                try:
                    ts.read_tasks(self.dir)  # raises JSONDecodeError on a partial file
                except Exception as e:
                    bad.append(e)
                reads.append(1)

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        try:
            for i in range(150):
                ts.add_task({"id": f"r-{i}", "client": "example.com",
                             "agent": "metadata-onpage-seo", "status": "todo"}, state_dir=self.dir)
        finally:
            stop.set()
            t.join(10)
        self.assertEqual(bad, [])
        self.assertGreater(len(reads), 10)  # the reader really ran during the writes

    def test_lock_released_after_error(self):
        def boom(tasks):
            raise RuntimeError("fail inside the critical section")

        with self.assertRaises(RuntimeError):
            ts.update_tasks(boom, state_dir=self.dir)
        self.assertFalse((Path(self.dir) / ".tasks.lock").exists())
        ts.add_task({"id": "a", "client": "c", "agent": "x", "status": "todo"}, state_dir=self.dir)

    def test_second_writer_times_out_while_lock_is_held(self):
        with ts.tasks_lock(self.dir):
            with self.assertRaises(ts.LockTimeout):
                ts.update_tasks(lambda t: t, state_dir=self.dir, max_wait=0.2)

    def test_stale_lock_is_surfaced_not_broken(self):
        lock = Path(self.dir) / ".tasks.lock"
        lock.mkdir(parents=True)
        old = time.time() - 3600
        os.utime(lock, (old, old))
        with self.assertRaises(ts.StaleLockError):
            ts.update_tasks(lambda t: t, state_dir=self.dir, stale_after=300)
        self.assertTrue(lock.exists())  # left in place for a human to inspect

    def test_invalid_tasks_are_rejected_and_nothing_is_written(self):
        ts.add_task({"id": "ok", "client": "c", "agent": "x", "status": "todo"}, state_dir=self.dir)
        with self.assertRaises(ts.InvalidTask):
            ts.set_status("ok", "blocked", "x", state_dir=self.dir)  # blocked needs a reason
        with self.assertRaises(ts.InvalidTask):
            ts.set_status("ok", "finished", "x", state_dir=self.dir)  # not a valid status
        self.assertEqual(ts.read_tasks(self.dir)[0]["status"], "todo")

    def test_status_transition_updates_timestamp_only(self):
        t = ts.add_task({"id": "s", "client": "c", "agent": "x", "status": "todo"}, state_dir=self.dir)
        ts.set_status("s", "blocked", "x", blocked_reason="waiting on DNS", state_dir=self.dir)
        got = ts.read_tasks(self.dir)[0]
        self.assertEqual(got["created_at"], t["created_at"])
        self.assertEqual(got["blocked_reason"], "waiting on DNS")

    def test_duplicate_ids_rejected(self):
        ts.add_task({"id": "d", "client": "c", "agent": "x", "status": "todo"}, state_dir=self.dir)
        with self.assertRaises(ts.InvalidTask):
            ts.add_task({"id": "d", "client": "c", "agent": "x", "status": "todo"}, state_dir=self.dir)


if __name__ == "__main__":
    unittest.main()
