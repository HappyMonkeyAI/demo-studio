from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

def _schema_path() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "beat.schema.json",
        here.parents[1] / "schema" / "beat.schema.json",
        Path.cwd() / "schema" / "beat.schema.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("beat.schema.json not found (package or repo schema/)")


def load_schema() -> dict[str, Any]:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def load_beats(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be an object")
    return data


def validate_beats(data: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty means valid."""
    validator = Draft202012Validator(load_schema())
    return sorted(
        f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
        for err in validator.iter_errors(data)
    )


def summarize(data: dict[str, Any]) -> str:
    beats = data.get("beats") or []
    lines = [
        f"product={data.get('product')}",
        f"title={data.get('title') or '(none)'}",
        f"beats={len(beats)}",
        f"base_url_env={data.get('base_url_env') or 'DEMO_BASE_URL'}",
    ]
    for beat in beats:
        n_actions = len(beat.get("actions") or [])
        n_assert = len(beat.get("assert") or [])
        narr = (beat.get("narration") or "").replace("\n", " ")
        if len(narr) > 72:
            narr = narr[:69] + "..."
        lines.append(f"  - {beat.get('id')}: actions={n_actions} assert={n_assert} | {narr}")
    return "\n".join(lines)
