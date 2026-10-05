"""Automatic checks on a workflow's output: the things a careful person would verify before trusting it.

Each check returns (passed, detail). They are deliberately simple and deterministic, so a failure
always points at something specific in the output.
"""

from __future__ import annotations

import re

from .spec import json_block, values_at

NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")


def norm(text) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def numbers_in(text: str) -> set[float]:
    out = set()
    for m in NUMBER.finditer(str(text)):
        try:
            out.add(round(float(m.group().replace(",", "")), 4))
        except ValueError:
            pass
    return out


MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def date_variants(iso: str) -> list[str]:
    """How people write 2026-10-24 in an email: 24 October, Oct 24, 24/10/2026, 24th Oct..."""
    m = ISO_DATE.match(iso)
    if not m:
        return []
    y, mo, d = int(m[1]), int(m[2]), int(m[3])
    if not 1 <= mo <= 12:
        return []
    full, short = MONTHS[mo - 1], MONTHS[mo - 1][:3]
    out = [iso, f"{d}/{mo}/{y}", f"{d:02d}/{mo:02d}/{y}", f"{d}/{mo}", f"{d:02d}/{mo:02d}", f"{d}.{mo}.{y}"]
    for day in (str(d), f"{d}st", f"{d}nd", f"{d}rd", f"{d}th"):
        out += [f"{day} {full}", f"{day} {short}", f"{full} {day}", f"{short} {day}"]
    return out


def appears_in(value, source: str) -> bool:
    """A value 'appears' in the source if its text does, or, for a number, the same number does,
    or, for an ISO date, the same date written any common way."""
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return round(float(value), 4) in numbers_in(source)
    v = norm(value)
    if v == "":
        return True
    src = norm(source)
    if ISO_DATE.match(v):
        return any(re.search(r"(?<![\w/])" + re.escape(x) + r"(?![\w/])", src) for x in date_variants(v))
    if v in src:
        return True
    # "1,200" in the source and 1200 (as text) in the output are the same quantity
    return bool(re.fullmatch(r"-?\d[\d,]*(\.\d+)?", v)) and round(float(v.replace(",", "")), 4) in numbers_in(source)


def selected_text(spec: dict, output: str, data) -> str:
    """The text a check reads: the whole reply, or only the JSON fields it names (`field` or `fields`)."""
    paths = spec.get("fields") or ([spec["field"]] if "field" in spec else None)
    if not paths:
        return output
    return " ".join(str(v) for p in paths for v in values_at(data or {}, p) if v is not None)


def check(
    spec: dict, output: str, source: str, *, input_text: str | None = None, decline_phrase: str = ""
) -> tuple[bool, str]:
    """`source` is the input plus any reference files; a check with `scope: input` (the default for
    banned phrases) compares against the input alone, so a reference file that lists forbidden
    words, or a warranty the product doesn't have, can't make a bad output pass."""
    kind = spec["type"]
    data = json_block(output)
    default_scope = "input" if kind == "banned_phrases" else "all"
    if spec.get("scope", default_scope) == "input" and input_text is not None:
        source = input_text

    if kind == "json_block":
        return (data is not None, "" if data is not None else "no parseable JSON block")

    if kind == "required":
        if data is None:
            return False, "no JSON to check"
        missing = [f for f in spec["fields"] if not any(v not in (None, "", []) for v in values_at(data, f))]
        return (not missing, f"missing or empty: {', '.join(missing)}" if missing else "")

    if kind == "in_source":
        # Every extracted value must be traceable to the input: nothing invented.
        if data is None:
            return False, "no JSON to check"
        bad = [
            f"{f}={v!r}"
            for f in spec["fields"]
            for v in values_at(data, f)
            if not (v is None and spec.get("allow_null", True)) and not appears_in(v, source)
        ]
        return (not bad, "not in the input: " + "; ".join(bad[:5]) if bad else "")

    if kind == "quotes_verbatim":
        if data is None:
            return False, "no JSON to check"
        bad = [
            f"{v!r}"
            for f in spec["fields"]
            for v in values_at(data, f)
            if isinstance(v, str) and norm(v.strip('"“”')) not in norm(source)
        ]
        return (not bad, "quote not found word for word: " + "; ".join(bad[:3]) if bad else "")

    if kind == "numbers_grounded":
        # Every number in the chosen text must exist in the input. Small counting numbers and the
        # numbers in an allow-list are fine. Signs are compared loosely: "fell 6.0%" correctly
        # reports a "-6.0%" in the table.
        text = selected_text(spec, output, data)
        known = {abs(n) for n in numbers_in(source)} | {abs(float(n)) for n in spec.get("allow", [])}
        extra = sorted(
            n for n in {abs(n) for n in numbers_in(text)} if n not in known and not n <= spec.get("small", 10)
        )
        return (not extra, "numbers not in the input: " + ", ".join(f"{n:g}" for n in extra[:6]) if extra else "")

    if kind == "max_chars":
        if data is None:
            return False, "no JSON to check"
        long = [
            f"{f} ({len(str(v))} > {limit})"
            for f, limit in spec["limits"].items()
            for v in values_at(data, f)
            if v is not None and len(str(v)) > limit
        ]
        return (not long, "too long: " + "; ".join(long) if long else "")

    if kind == "max_items":
        if data is None:
            return False, "no JSON to check"
        over = [
            f"{f} has {len(v)} > {limit}"
            for f, limit in spec["limits"].items()
            for v in values_at(data, f)
            if isinstance(v, list) and len(v) > limit
        ]
        return (not over, "; ".join(over))

    if kind == "banned_phrases":
        # Claims the business must never make, unless the input itself makes them.
        text = selected_text(spec, output, data)
        hits = [p for p in spec["phrases"] if re.search(p, text, re.I) and not re.search(p, source, re.I)]
        return (not hits, "banned wording: " + ", ".join(hits) if hits else "")

    if kind == "cites":
        # Answers must point at the section they came from, e.g. "[Returns policy, 2.1]".
        pattern = spec.get("pattern", r"\[[^\]]+\]")
        ok = bool(re.search(pattern, output)) or decline_phrase and norm(decline_phrase) in norm(output)
        return (bool(ok), "" if ok else "no citation")

    raise ValueError(f"unknown check type: {kind}")


def run_checks(
    checks: list[dict], output: str, source: str, *, input_text: str | None = None, decline_phrase: str = ""
) -> list[dict]:
    results = []
    for spec in checks:
        try:
            passed, detail = check(spec, output, source, input_text=input_text, decline_phrase=decline_phrase)
        except Exception as e:  # a broken check must show up, not crash the run
            passed, detail = False, f"check error: {e}"
        results.append({"id": spec.get("id", spec["type"]), "passed": passed, "detail": detail})
    return results
