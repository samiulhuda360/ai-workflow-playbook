"""Command line.

python -m playbook list
python -m playbook run all [--model gemini-flash-lite-latest] [--model ...] [--no-cache] [--pause 4]
python -m playbook run 01 03                # by folder-name fragment
python -m playbook show 01 02-partial       # print one stored output and its checks
python -m playbook report
python -m playbook adoption adoption/example-tracker.csv
"""

from __future__ import annotations

import argparse
import json
import sys

from . import run as runner
from .llm import Client, ModelError
from .spec import all_workflows, find


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="playbook")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("names", nargs="+")
    r.add_argument("--model", action="append")
    r.add_argument("--no-cache", action="store_true")
    r.add_argument("--pause", type=float, default=0.0, help="seconds between model calls (free-tier limits)")
    s = sub.add_parser("show")
    s.add_argument("workflow")
    s.add_argument("example")
    s.add_argument("--model")
    sub.add_parser("report")
    a = sub.add_parser("adoption")
    a.add_argument("csv")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for wf in all_workflows():
            print(f"{wf.id:42} {wf.team:18} {len(wf.examples)} examples  {wf.title}")
        return 0

    if args.cmd == "run":
        workflows = all_workflows() if args.names == ["all"] else [find(n) for n in args.names]
        for model in args.model or [None]:
            client = Client(model=model, use_cache=not args.no_cache)
            for wf in workflows:
                try:
                    result = runner.run_workflow(wf, client, pause=args.pause)
                except ModelError as e:
                    print(f"{wf.id}: {e}")
                    return 1
                s = runner.summarise(result)
                print(
                    f"{client.model:28} {wf.id:42} answer key {s['answer_key']:>7}  checks {s['checks']:>7}  "
                    f"median {s['median_seconds']} s"
                )
        print("\n" + runner.report().split("\n## What went wrong")[0])
        return 0

    if args.cmd == "show":
        wf = find(args.workflow)
        model = args.model or Client().model
        path = runner.RESULTS / runner.slug(model) / f"{wf.id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        ex = next(e for e in data["examples"] if args.example in e["example"])
        print(ex["output"], "\n")
        for c in ex["checks"]:
            print(("PASS " if c["passed"] else "FAIL ") + c["id"], c["detail"])
        print("answer key:", ex["score"])
        return 0

    if args.cmd == "report":
        print(runner.report())
        return 0

    if args.cmd == "adoption":
        from .adoption import report as adoption_report

        print(adoption_report(args.csv))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
