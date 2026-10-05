"""Command line wrapper around tasks_store, so agents never edit tasks.json by hand.

  python tools/tasks_cli.py add --id th-0042 --client example.com --agent technical-health --title "..."
  python tools/tasks_cli.py status th-0042 in_progress --as technical-health
  python tools/tasks_cli.py status th-0042 review --as technical-health     # finished: ask for verification
  python tools/tasks_cli.py changelog --client example.com --agent technical-health --task-id th-0042 ...
  python tools/tasks_cli.py status th-0042 done --as project-manager        # only project-manager may close
  python tools/tasks_cli.py list [--client example.com] [--status blocked] [--json]

Exit codes: 0 ok, 2 invalid, 3 lock timeout, 4 stale lock, 5 not authorized.
State directory: $HERMES_STATE_DIR, else ~/.hermes/state.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changelog  # noqa: E402
import tasks_store as ts  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(prog="tasks_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--id", required=True)
    a.add_argument("--client", required=True)
    a.add_argument("--agent", required=True)
    a.add_argument("--title", default="")
    a.add_argument("--status", default="todo", choices=ts.VALID_STATUSES)
    a.add_argument("--assigned-by", default="project-manager")

    s = sub.add_parser("status")
    s.add_argument("id")
    s.add_argument("status", choices=ts.VALID_STATUSES)
    s.add_argument("--blocked-reason")
    s.add_argument("--as", dest="actor", required=True, help="the agent making the change")

    c = sub.add_parser("changelog")
    for name in ("client", "agent", "task-id", "action", "before", "after", "verified-by",
                 "verification-method", "side-effects-checked"):
        c.add_argument(f"--{name}", required=True)
    c.add_argument("--backup-ref")
    c.add_argument("--rollback-available", choices=("true", "false"))
    c.add_argument("--notes")

    ls = sub.add_parser("list")
    ls.add_argument("--client")
    ls.add_argument("--status", choices=ts.VALID_STATUSES)
    ls.add_argument("--json", action="store_true")

    args = p.parse_args(argv)
    try:
        if args.cmd == "add":
            task = ts.add_task({"id": args.id, "client": args.client, "agent": args.agent,
                                "title": args.title, "status": args.status,
                                "assigned_by": args.assigned_by})
            print(json.dumps(task))
        elif args.cmd == "status":
            ts.set_status(args.id, args.status, args.actor, blocked_reason=args.blocked_reason)
            print(f"{args.id} -> {args.status}")
        elif args.cmd == "changelog":
            changelog.append_entry({
                "client": args.client, "agent": args.agent, "task_id": args.task_id,
                "action": args.action, "before": args.before, "after": args.after,
                "verified_by": args.verified_by, "verification_method": args.verification_method,
                "backup_ref": args.backup_ref,
                "rollback_available": None if args.rollback_available is None else args.rollback_available == "true",
                "side_effects_checked": args.side_effects_checked, "notes": args.notes})
            print(f"changelog entry added for {args.task_id}")
        else:
            tasks = [t for t in ts.read_tasks()
                     if (not args.client or t["client"] == args.client)
                     and (not args.status or t["status"] == args.status)]
            if args.json:
                print(json.dumps(tasks, indent=2))
            else:
                for t in tasks:
                    print(f"{t['id']:<12} {t['status']:<12} {t['client']:<22} {t['owner']:<26} {t.get('title', '')}")
    except (ts.InvalidTask, changelog.InvalidEntry) as e:
        print(f"invalid: {e}", file=sys.stderr)
        return 2
    except ts.NotAuthorized as e:
        print(f"not authorized: {e}", file=sys.stderr)
        return 5
    except ts.LockTimeout as e:
        print(f"lock timeout: {e}", file=sys.stderr)
        return 3
    except ts.StaleLockError as e:
        print(f"stale lock: {e}", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
