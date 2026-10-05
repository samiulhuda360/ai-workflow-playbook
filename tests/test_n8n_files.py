"""The n8n files are what people import, so check them like code: wiring, no secrets, the safety rules present."""

import json
import re
import runpy
from pathlib import Path

import pytest

N8N = Path(__file__).resolve().parent.parent / "n8n"
FILES = ["inbox-triage.json", "price-watch.json"]


@pytest.fixture(params=FILES)
def workflow(request):
    return json.loads((N8N / request.param).read_text(encoding="utf-8"))


def test_every_connection_points_at_a_real_node(workflow):
    names = {n["name"] for n in workflow["nodes"]}
    for source, outputs in workflow["connections"].items():
        assert source in names
        for branch in outputs["main"]:
            for link in branch:
                assert link["node"] in names


def test_no_credentials_or_keys_inside(workflow):
    text = json.dumps(workflow)
    assert all("credentials" not in n for n in workflow["nodes"])
    assert not re.search(r"AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,}", text), "an API key is in the file"


def test_inbox_triage_reads_the_key_from_the_environment_and_keeps_its_rules():
    wf = json.loads((N8N / "inbox-triage.json").read_text(encoding="utf-8"))
    nodes = {n["name"]: n for n in wf["nodes"]}
    auth = nodes["Classify and draft (AI)"]["parameters"]["headerParameters"]["parameters"][0]["value"]
    assert "$env.AI_API_KEY" in auth
    rules = nodes["Apply the rules"]["parameters"]["jsCode"]
    for must in ("burn", "allerg", "tribunal", "ignore (all |your |the )?(previous |above )?instructions", "refund"):
        assert must in rules
    # both branches end before anything is sent
    assert "Nothing is sent" in nodes["To the review queue"]["parameters"]["jsCode"]


def test_price_watch_uses_no_ai():
    text = (N8N / "price-watch.json").read_text(encoding="utf-8")
    assert "chat/completions" not in text and "AI_API_KEY" not in text


def test_files_match_the_builder():
    """The committed JSON must be what build_workflows.py produces, so the readable code is the real code."""
    builder = runpy.run_path(str(N8N / "build_workflows.py"))  # not run as __main__, so it writes nothing
    for f in FILES:
        assert (N8N / f).read_text(encoding="utf-8") == builder["render"](builder["WORKFLOWS"][f]), (
            f"{f} is out of date: run python n8n/build_workflows.py"
        )


def test_sample_emails_have_expected_answers():
    samples = json.loads((N8N / "samples" / "inbox.json").read_text(encoding="utf-8"))
    assert len(samples) == 10
    for s in samples:
        assert s["expected"]["category"] and isinstance(s["expected"]["needs_person"], bool)
