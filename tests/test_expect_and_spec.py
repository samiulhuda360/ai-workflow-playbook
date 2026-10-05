from playbook.expect import score
from playbook.spec import all_workflows, json_block, values_at


def out(json_text: str) -> str:
    return f"```json\n{json_text}\n```"


def test_rows_score_one_point_per_row_and_report_differences():
    expect = [
        {
            "type": "rows",
            "path": "lines",
            "key": "sku",
            "rows": [{"sku": "A", "qty": 10, "status": "delayed"}, {"sku": "B", "qty": 5}],
        }
    ]
    s = score(expect, out('{"lines": [{"sku": "A", "qty": 10, "status": "Delayed"}, {"sku": "B", "qty": 6}]}'))
    assert (s["points"], s["total"]) == (1, 2)
    assert "qty expected 5 got 6" in s["misses"][0]


def test_equals_handles_null_and_booleans():
    expect = [
        {"type": "equals", "path": "po_number", "value": None},
        {"type": "equals", "path": "needs_person", "value": False},
    ]
    assert score(expect, out('{"po_number": null, "needs_person": false}'))["points"] == 2
    assert score(expect, out('{"po_number": "PO-1", "needs_person": true}'))["points"] == 0


def test_ids_recall_and_no_extra_precision():
    expect = [
        {"type": "ids", "path": "needs_person[].id", "values": ["R07", "R11"]},
        {"type": "no_extra_ids", "path": "needs_person[].id", "values": ["R07", "R11"]},
    ]
    s = score(expect, out('{"needs_person": [{"id": "R07"}, {"id": "R02"}]}'))
    assert (s["points"], s["total"]) == (1, 3)


def test_mentions_excludes_count_declines():
    text = "Online revenue rose. Return rate: reason not given. This isn't covered in our documents."
    expect = [{"type": "mentions", "values": ["reason not given", "freight"]}, {"type": "declines"}]
    s = score(expect, text, decline_phrase="isn't covered in our documents")
    assert (s["points"], s["total"]) == (2, 3)
    s = score(
        [
            {"type": "excludes", "path": "decisions[].text", "values": ["20% off"]},
            {"type": "count", "path": "actions[]", "min": 1, "max": 2},
        ],
        out('{"decisions": [{"text": "Run the 20% off sale"}], "actions": [{}, {}, {}]}'),
    )
    assert s["points"] == 0


def test_values_at_walks_nested_lists():
    data = {"themes": [{"review_ids": ["R1", "R2"]}, {"review_ids": ["R3"]}]}
    assert values_at(data, "themes[].review_ids[]") == ["R1", "R2", "R3"]
    assert json_block('text {"a": [1, 2]} more') == {"a": [1, 2]}


def test_every_workflow_loads_with_examples_and_valid_answer_keys():
    workflows = all_workflows()
    assert len(workflows) >= 6
    for wf in workflows:
        assert wf.instructions and wf.checks and wf.examples, wf.id
        for ex in wf.examples:
            # an answer key scored against an empty reply must not crash
            score(ex.expect, "", decline_phrase=wf.decline_phrase)
