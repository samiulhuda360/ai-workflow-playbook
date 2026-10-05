"""Adoption report from a simple event log (adoption/tracker-template.csv).

Counting attendance is easy and says little. This report answers the questions an AI adoption lead is asked:
who now uses a workflow without help, which teams changed how they work, what is blocking the rest, and who to
follow up with this week.

Events (one row each): trained, used_with_help, used_alone, workflow_changed, blocked, stopped.
For `blocked`, put the kind of blocker in `notes`: learning, time, access or technical.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

EVENTS = {"trained", "used_with_help", "used_alone", "workflow_changed", "blocked", "stopped"}
BLOCKERS = ("learning", "time", "access", "technical")
INDEPENDENT_DAYS = 2  # used alone on at least two different days
FOLLOW_UP_AFTER = 14  # days after training with no independent use


def load(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle), start=2):
            event = (row.get("event") or "").strip()
            if event not in EVENTS:
                raise ValueError(f"line {i}: unknown event {event!r} (allowed: {', '.join(sorted(EVENTS))})")
            rows.append(
                {
                    "date": date.fromisoformat(row["date"].strip()),
                    "person": row["person"].strip(),
                    "team": row["team"].strip(),
                    "workflow": row["workflow"].strip(),
                    "event": event,
                    "notes": (row.get("notes") or "").strip(),
                }
            )
    return rows


def analyse(rows: list[dict], today: date | None = None) -> dict:
    today = today or max(r["date"] for r in rows)
    people = {r["person"]: r["team"] for r in rows}
    trained = {}
    alone_days = defaultdict(set)
    for r in rows:
        if r["event"] == "trained":
            trained.setdefault(r["person"], r["date"])
        if r["event"] == "used_alone":
            alone_days[(r["person"], r["workflow"])].add(r["date"])

    independent = {p for (p, _w), days in alone_days.items() if len(days) >= INDEPENDENT_DAYS}
    follow_up = sorted(
        p for p, when in trained.items() if p not in independent and today - when >= timedelta(days=FOLLOW_UP_AFTER)
    )
    by_workflow = defaultdict(lambda: {"trained": set(), "independent": set(), "changed_teams": set()})
    for r in rows:
        w = by_workflow[r["workflow"]]
        if r["event"] == "trained":
            w["trained"].add(r["person"])
        if r["event"] == "workflow_changed":
            w["changed_teams"].add(r["team"])
    for (p, wf), days in alone_days.items():
        if len(days) >= INDEPENDENT_DAYS:
            by_workflow[wf]["independent"].add(p)

    blockers = Counter()
    for r in rows:
        if r["event"] == "blocked":
            kind = next((b for b in BLOCKERS if b in r["notes"].lower()), "unspecified")
            blockers[kind] += 1

    stopped = [(r["person"], r["workflow"], r["notes"]) for r in rows if r["event"] == "stopped"]
    return {
        "today": today,
        "people": len(people),
        "trained": len(trained),
        "independent": len(independent & set(trained)),
        "changed": sorted({(r["team"], r["workflow"]) for r in rows if r["event"] == "workflow_changed"}),
        "by_workflow": by_workflow,
        "blockers": blockers,
        "follow_up": [(p, people[p], trained[p]) for p in follow_up],
        "stopped": stopped,
    }


def pct(n: int, d: int) -> str:
    return f"{round(100 * n / d)}%" if d else "n/a"


def report(path: str | Path, today: date | None = None) -> str:
    a = analyse(load(path), today)
    lines = [
        f"# AI adoption report ({a['today'].isoformat()})",
        "",
        f"- **Trained:** {a['trained']} of {a['people']} people in the log",
        f"- **Use a workflow on their own** (on {INDEPENDENT_DAYS}+ different days): {a['independent']} of "
        f"{a['trained']} trained ({pct(a['independent'], a['trained'])})",
        f"- **Teams that changed how they work:** {len(a['changed'])}",
        "",
        "| Workflow | Trained | Using it alone | Teams that changed their process |",
        "|---|---|---|---|",
    ]
    for wf, w in sorted(a["by_workflow"].items()):
        lines.append(
            f"| {wf} | {len(w['trained'])} | {len(w['independent'])} | {', '.join(sorted(w['changed_teams'])) or '-'} |"
        )
    lines += ["", "## What is blocking people", ""]
    if a["blockers"]:
        advice = {
            "learning": "a learning gap: a short follow-up session or a better tutorial",
            "time": "no time to try it: book 20 minutes with them on a real task",
            "access": "no access to the tool: an IT or licence request, not training",
            "technical": "something broken: escalate to the systems owner",
            "unspecified": "ask what got in the way",
        }
        for kind, n in a["blockers"].most_common():
            lines.append(f"- {kind}: {n} ({advice[kind]})")
    else:
        lines.append("Nothing recorded.")
    lines += ["", f"## Follow up this week (trained {FOLLOW_UP_AFTER}+ days ago, not yet using it alone)", ""]
    lines += [f"- {p} ({team}), trained {when.isoformat()}" for p, team, when in a["follow_up"]] or ["Nobody."]
    if a["stopped"]:
        lines += ["", "## Stopped using a workflow", ""]
        lines += [f"- {p}: {wf}. {why}" for p, wf, why in a["stopped"]]
    return "\n".join(lines) + "\n"
