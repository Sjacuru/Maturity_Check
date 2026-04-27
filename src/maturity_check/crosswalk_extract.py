from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def iter_json_fence_contents(md: str) -> list[str]:
    """Return raw string contents of every ```json ... ``` fence in order."""
    out: list[str] = []
    for m in re.finditer(r"^```json\s*\n(.*?)^```\s*$", md, flags=re.DOTALL | re.MULTILINE):
        out.append(m.group(1).strip())
    return out


def load_crosswalk_dicts_from_markdown(path: Path) -> list[dict[str, Any]]:
    """Parse all JSON objects embedded in Markdown fences (usually one per template)."""
    text = path.read_text(encoding="utf-8")
    blocks = iter_json_fence_contents(text)
    if not blocks:
        raise ValueError(f"No ```json fence found in {path}")
    result: list[dict[str, Any]] = []
    for i, raw in enumerate(blocks):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in fence #{i + 1} of {path}: {e}") from e
        if not isinstance(data, dict):
            raise TypeError(f"Fence #{i + 1} in {path} must be a JSON object, got {type(data)}")
        result.append(data)
    return result


def default_json_out_name(template_path: Path) -> str:
    """Map action_1_subtask_1_1.template.md -> action_1_subtask_1_1.json"""
    stem = template_path.stem
    if stem.endswith(".template"):
        stem = stem[: -len(".template")]
    return f"{stem}.json"


def extract_templates_to_dir(
    *,
    template_paths: list[Path],
    out_dir: Path,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for p in template_paths:
        p = p.resolve()
        dicts = load_crosswalk_dicts_from_markdown(p)
        if len(dicts) != 1:
            raise ValueError(
                f"Expected exactly one JSON object in {p}, found {len(dicts)} fences "
                "(split templates or extend extract_templates_to_dir)."
            )
        out_path = out_dir / default_json_out_name(p)
        out_path.write_text(json.dumps(dicts[0], ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(out_path)
    return written
