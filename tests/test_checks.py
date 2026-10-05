"""The checks must catch the failures they exist for, not just pass good output."""

from playbook.checks import appears_in, check, date_variants, numbers_in, run_checks

EMAIL = "PO-20417: the 1,200 pcs of TW-BTL-750 will now be ready on 24 October instead of 10 October."


def reply(json_text: str, summary: str = "Summary.") -> str:
    return f"{summary}\n\n```json\n{json_text}\n```"


def test_json_block_found_in_fence_or_bare():
    assert check({"type": "json_block"}, reply('{"a": 1}'), "")[0]
    assert check({"type": "json_block"}, 'Here: {"a": 1} done', "")[0]
    assert not check({"type": "json_block"}, "no json here", "")[0]


def test_in_source_accepts_numbers_with_commas_and_dates_in_words():
    out = reply('{"po_number": "PO-20417", "lines": [{"sku": "TW-BTL-750", "qty": 1200, "new_date": "2026-10-24"}]}')
    ok, detail = check(
        {"type": "in_source", "fields": ["po_number", "lines[].sku", "lines[].qty", "lines[].new_date"]}, out, EMAIL
    )
    assert ok, detail


def test_in_source_catches_an_invented_quantity_and_date():
    out = reply('{"lines": [{"sku": "TW-BTL-750", "qty": 1500, "new_date": "2026-10-31"}]}')
    ok, detail = check({"type": "in_source", "fields": ["lines[].qty", "lines[].new_date"]}, out, EMAIL)
    assert not ok
    assert "1500" in detail and "2026-10-31" in detail


def test_date_variants_cover_common_ways_of_writing_a_date():
    variants = date_variants("2026-10-24")
    for written in ("24 october", "oct 24", "24/10/2026", "24th october"):
        assert written in variants
    assert appears_in("2026-10-24", "Ready on Saturday 24 October.")
    assert not appears_in("2026-10-24", "Ready on 4 October.")  # 24 must not match inside a different day


def test_quotes_must_be_word_for_word():
    notes = "Great. Leo, can you send the shot list to the team before the shoot? Like, by Monday?"
    good = reply('{"actions": [{"source": "Leo, can you send the shot list to the team before the shoot?"}]}')
    swapped = reply('{"actions": [{"source": "Jess, can you send the shot list to the team before the shoot?"}]}')
    spec = {"type": "quotes_verbatim", "fields": ["actions[].source"]}
    assert check(spec, good, notes)[0]
    assert not check(spec, swapped, notes)[0]


def test_numbers_grounded_catches_invented_numbers_but_allows_sign_in_words():
    table = "| Online store revenue | $161,900 | $172,300 | -6.0% |"
    assert check({"type": "numbers_grounded", "small": 5}, "Online revenue fell 6.0% to $161,900.", table)[0]
    ok, detail = check({"type": "numbers_grounded", "small": 5}, "Online revenue fell 7.5%.", table)
    assert not ok and "7.5" in detail


def test_numbers_grounded_with_input_scope_ignores_reference_files():
    spec_sheet = "Capacity: 750 ml"
    brand_guide = "We offer a 2-year warranty."
    copy = reply('{"website": {"description": "750 ml bottle with a 2-year warranty"}}')
    spec = {"type": "numbers_grounded", "scope": "input", "fields": ["website.description"], "small": 1}
    ok, _ = check(spec, copy, spec_sheet + "\n" + brand_guide, input_text=spec_sheet)
    assert not ok  # the warranty is only in the brand guide, not in this product's spec


def test_banned_phrases_only_in_the_copy_and_unless_the_input_says_it():
    brand_guide = "Never write non-toxic or eco-friendly."
    spec_sheet = "Moso bamboo board."
    bad = reply('{"website": {"title": "Eco-friendly bamboo board"}}')
    spec = {"type": "banned_phrases", "fields": ["website.title"], "phrases": ["eco-?friendly"]}
    assert not check(spec, bad, spec_sheet + brand_guide, input_text=spec_sheet)[0]
    # the same word in the summary (outside the checked fields) is fine
    discussed = reply('{"website": {"title": "Bamboo board"}}', summary="I avoided 'eco-friendly'.")
    assert check(spec, discussed, spec_sheet, input_text=spec_sheet)[0]


def test_length_and_item_limits():
    out = reply('{"website": {"title": "' + "x" * 71 + '", "bullets": ["a", "b", "c", "d", "e", "f"]}}')
    assert not check({"type": "max_chars", "limits": {"website.title": 70}}, out, "")[0]
    assert not check({"type": "max_items", "limits": {"website.bullets": 5}}, out, "")[0]


def test_citation_or_decline():
    spec = {"type": "cites", "pattern": r"\[(Returns policy) §\d+\]"}
    assert check(spec, "30 days [Returns policy §1].", "")[0]
    assert check(spec, "This isn't covered in our documents.", "", decline_phrase="isn't covered in our documents")[0]
    assert not check(spec, "30 days, I think.", "", decline_phrase="isn't covered in our documents")[0]


def test_a_broken_check_is_reported_not_raised():
    results = run_checks([{"type": "no_such_check"}], "x", "y")
    assert results[0]["passed"] is False and "check error" in results[0]["detail"]


def test_numbers_in_reads_money_and_percentages():
    assert numbers_in("$182,400 and +12.7% and 4.9%") >= {182400.0, 12.7, 4.9}
