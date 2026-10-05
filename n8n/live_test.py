"""Run both n8n workflows for real, in a throwaway n8n, and score them.

    AI_API_KEY=... python n8n/live_test.py [path to the n8n CLI]

1. Serves the invented competitor pages in n8n/mock-shop on http://127.0.0.1:8765.
2. Imports both workflows into a temporary n8n data folder (your own n8n is untouched).
3. Runs the inbox workflow from its "Try with sample emails" trigger: the ten invented emails go through the same
   AI call and rules as webhook traffic. Each decision is compared with the expected category and with whether a
   person should see it.
4. Runs the price check once.
5. Writes n8n/RESULTS.md.

The API key is passed to n8n as an environment variable only; it is never written to a file.
"""

from __future__ import annotations

import functools
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
N8N = sys.argv[1] if len(sys.argv) > 1 else shutil.which("n8n") or "n8n"


def n8n(args: list[str], env: dict, timeout: int = 600) -> str:
    cmd = ["node", N8N, *args] if Path(N8N).is_file() and not N8N.endswith((".cmd", ".exe")) else [N8N, *args]
    run = subprocess.run(
        cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
    )
    if run.returncode != 0:
        raise RuntimeError(f"n8n {' '.join(args)} failed:\n{run.stdout[-2000:]}\n{run.stderr[-2000:]}")
    return run.stdout


def run_data(stdout: str) -> dict:
    """`n8n execute --rawOutput` prints a few log lines, then the execution as JSON."""
    data = json.loads(stdout[stdout.find("{") :])
    result = data["data"]["resultData"]
    if result.get("error"):
        raise RuntimeError(f"execution failed: {result['error']}")
    return result["runData"]


def items(runs: dict, node: str) -> list[dict]:
    return [i["json"] for i in runs[node][0]["data"]["main"][0]]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


def serve_mock_shop() -> socketserver.TCPServer:
    handler = functools.partial(QuietHandler, directory=str(HERE / "mock-shop"))
    server = socketserver.TCPServer(("127.0.0.1", 8765), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.environ.get("AI_API_KEY"):
        print("Set AI_API_KEY first.")
        return 1
    triage = json.loads((HERE / "inbox-triage.json").read_text(encoding="utf-8"))
    price = json.loads((HERE / "price-watch.json").read_text(encoding="utf-8"))
    samples = {s["id"]: s for s in json.loads((HERE / "samples" / "inbox.json").read_text(encoding="utf-8"))}

    home = tempfile.mkdtemp(prefix="n8n-live-test-")
    env = {
        **os.environ,
        "N8N_USER_FOLDER": home,
        "N8N_DIAGNOSTICS_ENABLED": "false",
        "N8N_BLOCK_ENV_ACCESS_IN_NODE": "false",  # the workflows read AI_API_KEY and AI_MODEL from the environment
        "PRICE_WATCH_BASE_URL": "http://127.0.0.1:8765",
    }
    shop = serve_mock_shop()
    try:
        for path in ("inbox-triage.json", "price-watch.json"):
            n8n(["import:workflow", f"--input={HERE / path}"], env)
        decisions = items(run_data(n8n(["execute", f"--id={triage['id']}", "--rawOutput"], env)), "Apply the rules")
        price_runs = run_data(n8n(["execute", f"--id={price['id']}", "--rawOutput"], env))
        summary = items(price_runs, "Weekly summary")[0]
    finally:
        shop.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    rows = []
    for d in decisions:
        expected = samples[d["id"]]["expected"]
        rows.append(
            {
                "id": d["id"],
                "subject": samples[d["id"]]["subject"],
                "expected": expected,
                "got": d,
                "category_ok": d["category"] in expected["category"],
                "person_ok": d["needs_person"] is expected["needs_person"],
            }
        )
    write_results(rows, summary)
    print((HERE / "RESULTS.md").read_text(encoding="utf-8"))
    return 0


def write_results(rows: list[dict], price: dict) -> None:
    cat = sum(r["category_ok"] for r in rows)
    person = sum(r["person_ok"] for r in rows)
    by_rule = sum("wording found" in r["got"]["reason"] or "instructions to the AI" in r["got"]["reason"] for r in rows)
    lines = [
        "# n8n workflows: live test results",
        "",
        f"Run on {date.today().isoformat()} with `{os.environ.get('AI_MODEL', 'gemini-flash-lite-latest')}` by "
        "`python n8n/live_test.py`: both workflows imported into a fresh n8n, the inbox workflow run on the ten "
        "invented emails, the price check run once against the invented competitor pages in `mock-shop/`.",
        "",
        "## Inbox triage",
        "",
        f"- Category right: **{cat}/{len(rows)}**",
        f"- Sent to a person when it should be, and only then: **{person}/{len(rows)}**",
        f"- Decisions where the fixed rules added a reason on top of the AI: {by_rule}",
        "",
        "| Email | Expected | Got | A person? (expected → got) | Reason given |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        g = r["got"]
        mark = "" if r["category_ok"] and r["person_ok"] else " ✗"
        why = (g.get("reason") or "").replace("|", "/")
        why = why if len(why) <= 140 else why[:137] + "..."
        lines.append(
            f"| {r['id']} {r['subject']}{mark} | {' or '.join(r['expected']['category'])} | {g.get('category')} | "
            f"{r['expected']['needs_person']} → {g.get('needs_person')} | {why} |"
        )
    lines += ["", "## Weekly price check", "", "```", price.get("summary", "(no output)"), "```", ""]
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
