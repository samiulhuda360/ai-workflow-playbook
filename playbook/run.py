"""Run workflows on their examples with one or more models, then summarise the results."""

from __future__ import annotations

import json
import re
import statistics
import time
from datetime import date

from .checks import run_checks
from .expect import score
from .llm import Client
from .spec import ROOT, Workflow

RESULTS = ROOT / "results"


def slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", model.lower()).strip("-")


def run_workflow(wf: Workflow, client: Client, *, pause: float = 0.0) -> dict:
    rows = []
    for ex in wf.examples:
        reply = client.chat(wf.system_prompt(), ex.input)
        checks = run_checks(
            wf.checks,
            reply.text,
            ex.input + "\n\n" + "\n\n".join(wf.knowledge.values()),
            input_text=ex.input,
            decline_phrase=wf.decline_phrase,
        )
        rows.append(
            {
                "example": ex.name,
                "output": reply.text,
                "checks": checks,
                "score": score(ex.expect, reply.text, decline_phrase=wf.decline_phrase),
                "seconds": reply.seconds,
                "tokens": [reply.input_tokens, reply.output_tokens],
                "cached": reply.cached,
            }
        )
        if pause and not reply.cached:
            time.sleep(pause)
    result = {
        "workflow": wf.id,
        "title": wf.title,
        "model": client.model,
        "date": date.today().isoformat(),
        "examples": rows,
    }
    out = RESULTS / slug(client.model) / f"{wf.id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def summarise(result: dict) -> dict:
    rows = result["examples"]
    points = sum(r["score"]["points"] for r in rows)
    total = sum(r["score"]["total"] for r in rows)
    checks = [c for r in rows for c in r["checks"]]
    fresh = [r["seconds"] for r in rows if not r["cached"]] or [r["seconds"] for r in rows]
    tokens_in = [r["tokens"][0] for r in rows if r["tokens"][0]]
    tokens_out = [r["tokens"][1] for r in rows if r["tokens"][1]]
    return {
        "workflow": result["workflow"],
        "title": result["title"],
        "model": result["model"],
        "examples": len(rows),
        "answer_key": f"{points}/{total}" if total else "n/a",
        "answer_key_pct": round(100 * points / total) if total else None,
        "checks": f"{sum(c['passed'] for c in checks)}/{len(checks)}",
        "checks_pct": round(100 * sum(c["passed"] for c in checks) / len(checks)) if checks else None,
        "median_seconds": round(statistics.median(fresh), 1) if fresh else None,
        "avg_tokens": (
            round(statistics.mean(tokens_in)) if tokens_in else None,
            round(statistics.mean(tokens_out)) if tokens_out else None,
        ),
    }


def report(models: list[str] | None = None) -> str:
    """results/REPORT.md: one row per workflow and model, then every miss and failed check."""
    found = sorted(RESULTS.glob("*/*.json"))
    results = [json.loads(p.read_text(encoding="utf-8")) for p in found]
    if models:
        results = [r for r in results if r["model"] in models]
    if not results:
        return "No results yet. Run: python -m playbook run all"

    lines = [
        "# Evaluation results",
        "",
        "Each workflow's instructions run on its examples (synthetic data). *Answer key*: facts that must "
        "be right (an order's quantities, the reviews that need a person, the section an answer comes from). "
        "*Checks*: guardrails on every output (nothing invented, no banned claims, length limits, citations).",
        "",
        "| Workflow | Model | Examples | Answer key | Checks passed | Median time | Tokens in / out |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda r: (r["workflow"], r["model"])):
        s = summarise(r)
        tok = f"{s['avg_tokens'][0] or '?'} / {s['avg_tokens'][1] or '?'}"
        ak = f"{s['answer_key']} ({s['answer_key_pct']}%)" if s["answer_key_pct"] is not None else "n/a"
        ck = f"{s['checks']} ({s['checks_pct']}%)" if s["checks_pct"] is not None else "n/a"
        lines.append(
            f"| {s['title']} | `{s['model']}` | {s['examples']} | {ak} | {ck} | {s['median_seconds']} s | {tok} |"
        )

    lines += ["", "## What went wrong", ""]
    any_miss = False
    for r in sorted(results, key=lambda r: (r["workflow"], r["model"])):
        for ex in r["examples"]:
            issues = ex["score"]["misses"] + [
                f"check {c['id']}: {c['detail']}" for c in ex["checks"] if not c["passed"]
            ]
            if issues:
                any_miss = True
                lines.append(f"- **{r['title']}** · `{r['model']}` · {ex['example']}: " + "; ".join(issues))
    if not any_miss:
        lines.append("Nothing: every answer-key fact and every check passed.")
    text = "\n".join(lines) + "\n"
    (RESULTS / "REPORT.md").write_text(text, encoding="utf-8")
    return text
