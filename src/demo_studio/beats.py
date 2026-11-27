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


CLIP_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

def visual_kind(beat: dict[str, Any]) -> str:
    return str(((beat.get("visual") or {}).get("kind") or "capture"))

def resolve_clip_path(beat: dict[str, Any], pack_dir: Path) -> Path | None:
    f = (beat.get("visual") or {}).get("file")
    if not f:
        return None
    # ``~/Videos/...`` is the natural way to reference a local recording in a
    # beat file; expand it against the home directory before the absolute check.
    p = Path(f).expanduser()
    return p if p.is_absolute() else Path(pack_dir) / p

def validate_visuals(data: dict[str, Any], pack_dir: Path) -> list[str]:
    """Clip-source checks beyond JSON schema. Empty list = valid."""
    errors: list[str] = []
    for i, beat in enumerate(data.get("beats") or []):
        bid = str(beat.get("id") or f"beat{i}")
        if visual_kind(beat) != "clip":
            continue
        v = beat.get("visual") or {}
        if not v.get("file"):
            errors.append(f"{bid}: visual.kind=clip requires visual.file")
            continue
        p = resolve_clip_path(beat, pack_dir)
        if p is None:
            errors.append(f"{bid}: could not resolve clip path")
            continue
        if not p.is_file():
            errors.append(f"{bid}: clip file not found: {p}")
        if p.suffix.lower() not in CLIP_EXTENSIONS:
            errors.append(f"{bid}: unsupported clip extension {p.suffix or '(none)'}")
        if beat.get("actions"):
            errors.append(f"{bid}: clip beats must not carry browser actions")
        in_sec = float(v.get("in_sec") or 0.0)
        out_sec = v.get("out_sec")
        if out_sec is not None and float(out_sec) <= in_sec:
            errors.append(f"{bid}: visual.out_sec must be greater than in_sec")
    return errors
