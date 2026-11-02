from __future__ import annotations

"""Cursor / click timeline for studio polish (MIT path — not Recordly).

Normalized coordinates are fractions of the capture viewport (0–1).
Inspired by OpenScreen `.cursor.json` / aidemo timelines, but owned here.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

EventType = Literal["move", "click", "fill", "scroll", "beat"]


@dataclass
class CursorEvent:
    t_ms: int
    type: EventType
    x: float  # 0–1
    y: float  # 0–1
    beat_id: str = ""
    label: str = ""
    cursor: str = "default"  # default | text | pointer


@dataclass
class CursorTimeline:
    version: int = 1
    width: int = 1280
    height: int = 900
    events: list[CursorEvent] = field(default_factory=list)

    def add(self, event: CursorEvent) -> None:
        self.events.append(event)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "events": [asdict(e) for e in self.events],
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> CursorTimeline:
        data = json.loads(path.read_text(encoding="utf-8"))
        events = [
            CursorEvent(
                t_ms=int(e.get("t_ms") or 0),
                type=e.get("type") or "move",  # type: ignore[arg-type]
                x=float(e.get("x") or 0.5),
                y=float(e.get("y") or 0.5),
                beat_id=str(e.get("beat_id") or ""),
                label=str(e.get("label") or ""),
                cursor=str(e.get("cursor") or "default"),
            )
            for e in data.get("events") or []
        ]
        return cls(
            version=int(data.get("version") or 1),
            width=int(data.get("width") or 1280),
            height=int(data.get("height") or 900),
            events=events,
        )

    def focus_per_beat(self) -> dict[str, tuple[float, float]]:
        """Last click/fill position per beat_id (fallback: last move)."""
        foci: dict[str, tuple[float, float]] = {}
        for ev in self.events:
            if not ev.beat_id:
                continue
            if ev.type in {"click", "fill", "move"}:
                foci[ev.beat_id] = (ev.x, ev.y)
        return foci

    def to_openscreen_cursor_samples(self) -> dict[str, Any]:
        """Best-effort OpenScreen-shaped sidecar for optional external export."""
        samples = []
        for ev in self.events:
            samples.append(
                {
                    "t": ev.t_ms,
                    "x": ev.x,
                    "y": ev.y,
                    "type": "click" if ev.type == "click" else "move",
                    "cursor": ev.cursor,
                }
            )
        return {"version": 2, "samples": samples}


def write_openscreen_sidecar(timeline: CursorTimeline, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timeline.to_openscreen_cursor_samples(), indent=2) + "\n", encoding="utf-8")
    return path
