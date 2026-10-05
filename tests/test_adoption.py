from datetime import date

import pytest

from playbook.adoption import analyse, load, report

HEADER = "date,person,team,workflow,event,notes\n"


def write(tmp_path, body: str):
    path = tmp_path / "log.csv"
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def test_independent_use_needs_two_different_days(tmp_path):
    path = write(
        tmp_path,
        "2026-09-01,Ana,Ops,01,trained,\n"
        "2026-09-02,Ana,Ops,01,used_alone,\n"
        "2026-09-02,Ana,Ops,01,used_alone,same day again\n"
        "2026-09-01,Ben,Ops,01,trained,\n"
        "2026-09-03,Ben,Ops,01,used_alone,\n"
        "2026-09-09,Ben,Ops,01,used_alone,\n",
    )
    a = analyse(load(path), today=date(2026, 9, 10))
    assert a["trained"] == 2 and a["independent"] == 1  # only Ben, on two days


def test_follow_up_and_blockers(tmp_path):
    path = write(
        tmp_path,
        "2026-08-01,Cat,Sales,04,trained,\n"
        "2026-08-05,Cat,Sales,04,blocked,Access: no licence\n"
        "2026-09-20,Dan,Sales,04,trained,\n",
    )
    a = analyse(load(path), today=date(2026, 9, 25))
    assert [p for p, _t, _d in a["follow_up"]] == ["Cat"]  # Dan was trained only 5 days ago
    assert a["blockers"]["access"] == 1
    text = report(path, today=date(2026, 9, 25))
    assert "licence request, not training" in text


def test_unknown_event_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unknown event"):
        load(write(tmp_path, "2026-09-01,Eve,Ops,01,liked_it,\n"))


def test_example_log_reports():
    text = report("adoption/example-tracker.csv")
    assert "Use a workflow on their own" in text and "Follow up this week" in text
