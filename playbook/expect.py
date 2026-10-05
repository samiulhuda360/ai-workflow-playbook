"""Score an output against an example's answer key (examples/<name>.expected.yaml).

Answer-key items:
  {type: equals,   path: po_number, value: "PO-20417"}
  {type: rows,     path: lines, key: sku, rows: [{sku: ..., qty: ...}, ...]}   one point per row
  {type: ids,      path: "urgent[].id", values: [7, 19]}                    one point per id (recall)
  {type: no_extra_ids, path: "urgent[].id", values: [7, 19]}               nothing flagged that shouldn't be
  {type: count,    path: "actions[]", value: 4}   or  {min: 3, max: 5}     how many items were found
  {type: mentions, values: ["returns", "wholesale"]}                       one point per value
  {type: excludes, path: "decisions[].text", values: ["20% off"]}          must NOT appear there
  {type: declines}                                                         says it isn't in the documents
  {type: cites,    values: ["2.1"]}                                        cites the right section
"""

from __future__ import annotations

from .checks import norm
from .spec import json_block, values_at


def same(a, b) -> bool:
    if isinstance(b, bool) or isinstance(a, bool):
        return a is b or (isinstance(a, str) and norm(a) == str(b).lower())
    if isinstance(b, (int, float)):
        try:
            return abs(float(a) - float(b)) < 1e-6
        except (TypeError, ValueError):
            return False
    if b is None:
        return a in (None, "", "null")
    return norm(a) == norm(b)


def score(expect: list[dict], output: str, *, decline_phrase: str = "") -> dict:
    data = json_block(output) or {}
    points, total, misses = 0, 0, []

    for item in expect:
        kind = item["type"]
        if kind == "equals":
            total += 1
            got = values_at(data, item["path"])
            if got and same(got[0], item["value"]):
                points += 1
            else:
                misses.append(f"{item['path']}: expected {item['value']!r}, got {got[0] if got else None!r}")

        elif kind == "rows":
            got_rows = [r for r in values_at(data, item["path"] + "[]") if isinstance(r, dict)]
            by_key = {norm(r.get(item["key"])): r for r in got_rows}
            for row in item["rows"]:
                total += 1
                found = by_key.get(norm(row[item["key"]]))
                bad = [k for k, v in row.items() if found is None or not same(found.get(k), v)]
                if not bad:
                    points += 1
                else:
                    misses.append(
                        f"{item['path']} {row[item['key']]}: "
                        + (
                            "missing"
                            if found is None
                            else ", ".join(f"{k} expected {row[k]!r} got {found.get(k)!r}" for k in bad)
                        )
                    )

        elif kind == "ids":
            got = {norm(v) for v in values_at(data, item["path"])}
            for want in item["values"]:
                total += 1
                if norm(want) in got:
                    points += 1
                else:
                    misses.append(f"{item['path']}: {want!r} not flagged")

        elif kind == "no_extra_ids":
            total += 1
            allowed = {norm(v) for v in item["values"]}
            extra = sorted({norm(v) for v in values_at(data, item["path"])} - allowed)
            if not extra:
                points += 1
            else:
                misses.append(f"{item['path']}: also flagged {', '.join(extra)}")

        elif kind == "count":
            total += 1
            got = len(values_at(data, item["path"]))
            low, high = item.get("min", item.get("value")), item.get("max", item.get("value"))
            if low <= got <= high:
                points += 1
            else:
                misses.append(f"{item['path']}: expected {item.get('value', f'{low}-{high}')} items, got {got}")

        elif kind == "mentions":
            text = norm(output)
            for value in item["values"]:
                total += 1
                if norm(value) in text:
                    points += 1
                else:
                    misses.append(f"does not mention {value!r}")

        elif kind == "excludes":
            # a point only if none of the values appear at the path (e.g. a decision reversed later)
            total += 1
            text = norm(" ".join(str(v) for v in values_at(data, item["path"])))
            found = [v for v in item["values"] if norm(v) in text]
            if not found:
                points += 1
            else:
                misses.append(f"{item['path']} should not contain {', '.join(map(repr, found))}")

        elif kind == "declines":
            total += 1
            if decline_phrase and norm(decline_phrase) in norm(output):
                points += 1
            else:
                misses.append("should have said the documents don't cover this")

        elif kind == "cites":
            for value in item["values"]:
                total += 1
                if norm(value) in norm(output):
                    points += 1
                else:
                    misses.append(f"does not cite {value!r}")

        else:
            raise ValueError(f"unknown answer-key type: {kind}")

    return {"points": points, "total": total, "misses": misses}
