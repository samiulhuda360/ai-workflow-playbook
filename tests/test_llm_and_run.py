import json

import pytest

from playbook import llm, run
from playbook.spec import find


class FakeResponse:
    def __init__(self, status: int, content: str = ""):
        self.status_code = status
        self.ok = status == 200
        self._content = content

    def json(self):
        return {
            "choices": [{"message": {"content": self._content}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 9},
        }


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # cache goes to a temp folder
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    monkeypatch.setattr(run, "RESULTS", tmp_path / "results")


def test_client_retries_rate_limits_then_caches(monkeypatch):
    calls = []

    def post(url, json, timeout, headers):
        calls.append(url)
        return FakeResponse(429) if len(calls) == 1 else FakeResponse(200, "hello")

    monkeypatch.setattr(llm.requests, "post", post)
    client = llm.Client(model="m", base_url="https://ai.test/v1", api_key="k")
    first = client.chat("s", "u")
    second = client.chat("s", "u")
    assert first.text == second.text == "hello"
    assert len(calls) == 2 and calls[0] == "https://ai.test/v1/chat/completions"
    assert second.cached and not first.cached and first.input_tokens == 50


def test_client_gives_up_on_a_bad_request(monkeypatch):
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: FakeResponse(400))
    with pytest.raises(llm.ModelError):
        llm.Client(model="m", api_key="k", use_cache=False).chat("s", "u")


def test_client_needs_a_key():
    with pytest.raises(llm.ModelError):
        llm.Client(model="m", api_key="", use_cache=False).chat("s", "u")


def test_run_workflow_scores_and_writes_results(monkeypatch):
    wf = find("01-supplier")
    good = {
        "supplier": "Supplier A Manufacturing Co.",
        "po_number": "PO-20417",
        "lines": [
            {"sku": "TW-BTL-750", "qty": 1200, "status": "delayed", "new_date": "2026-10-24"},
            {"sku": "TW-BTL-500", "qty": 800, "status": "confirmed", "new_date": "2026-10-10"},
        ],
        "needs_person": True,
        "needs_person_reason": "new date",
        "reply_draft": "Thanks, we will check and come back to you.",
    }

    class FakeClient:
        model = "fake-model"

        def chat(self, system, user, **kw):
            assert "Supplier email" in system
            text = "Summary\n```json\n" + json.dumps(good) + "\n```" if "PO-20417" in user else "{}"
            return llm.Reply(text, "fake-model", 0.1, 10, 5, cached=False)

    result = run.run_workflow(wf, FakeClient())
    delay = next(r for r in result["examples"] if r["example"] == "01-delay")
    assert delay["score"]["points"] == delay["score"]["total"]
    assert all(c["passed"] for c in delay["checks"])
    s = run.summarise(result)
    assert s["examples"] == len(wf.examples)
    assert (run.RESULTS / "fake-model" / f"{wf.id}.json").exists()
    assert "Supplier email" in run.report()
