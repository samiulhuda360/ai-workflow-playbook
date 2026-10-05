"""A workflow is a folder: instructions.md (what a person pastes into Claude, ChatGPT or Gemini),
workflow.yaml (checks and settings), optional knowledge/ files, and examples/ with answer keys."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / "workflows"


@dataclass
class Example:
    name: str
    input: str
    expect: list[dict] = field(default_factory=list)


@dataclass
class Workflow:
    id: str
    folder: Path
    title: str
    team: str
    output: str  # "json" or "text"
    instructions: str
    knowledge: dict[str, str]
    checks: list[dict]
    examples: list[Example]
    decline_phrase: str = ""

    def system_prompt(self) -> str:
        """Instructions plus reference files, the way a Claude Project or custom GPT holds them."""
        if not self.knowledge:
            return self.instructions
        files = "\n\n".join(f"## {name}\n\n{text}" for name, text in self.knowledge.items())
        return f"{self.instructions}\n\n# Reference files\n\n{files}"


def load(folder: Path) -> Workflow:
    meta = yaml.safe_load((folder / "workflow.yaml").read_text(encoding="utf-8")) or {}
    knowledge = {}
    for rel in meta.get("knowledge", []):
        path = folder / rel
        knowledge[path.name] = path.read_text(encoding="utf-8").strip()
    examples = []
    for path in sorted((folder / "examples").glob("*")):
        if path.suffix in (".yaml", ".yml") or path.name.startswith("."):
            continue
        key = path.with_name(path.stem + ".expected.yaml")
        expect = (yaml.safe_load(key.read_text(encoding="utf-8")) or {}).get("expect", []) if key.exists() else []
        examples.append(Example(path.stem, path.read_text(encoding="utf-8").strip(), expect))
    return Workflow(
        id=folder.name,
        folder=folder,
        title=meta.get("title", folder.name),
        team=meta.get("team", ""),
        output=meta.get("output", "text"),
        instructions=(folder / "instructions.md").read_text(encoding="utf-8").strip(),
        knowledge=knowledge,
        checks=meta.get("checks", []),
        examples=examples,
        decline_phrase=meta.get("decline_phrase", ""),
    )


def all_workflows() -> list[Workflow]:
    return [load(p) for p in sorted(WORKFLOWS.iterdir()) if (p / "workflow.yaml").exists()]


def find(name: str) -> Workflow:
    matches = [p for p in sorted(WORKFLOWS.iterdir()) if (p / "workflow.yaml").exists() and name in p.name]
    if len(matches) != 1:
        raise SystemExit(f"'{name}' matches {len(matches)} workflows; use a longer part of the folder name.")
    return load(matches[0])


# ------------------------------------------------------------------ output parsing

FENCE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.S)


def json_block(text: str):
    """The JSON part of a reply: a ```json fenced block, or else the outermost {...}."""
    m = FENCE.search(text)
    candidates = [m.group(1)] if m else []
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    return None


def values_at(data, path: str) -> list:
    """All values at a path like 'po_number', 'lines[].sku' or 'actions[].owner'."""
    current = [data]
    for part in path.split("."):
        nxt = []
        is_list = part.endswith("[]")
        key = part[:-2] if is_list else part
        for item in current:
            value = item.get(key) if isinstance(item, dict) else None
            if is_list:
                nxt.extend(value if isinstance(value, list) else [])
            else:
                nxt.append(value)
        current = nxt
    return current
