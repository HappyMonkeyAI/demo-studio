from __future__ import annotations

import json
from pathlib import Path

from demo_studio.cursor_timeline import CursorEvent, CursorTimeline, write_openscreen_sidecar


def test_timeline_roundtrip(tmp_path: Path) -> None:
    tl = CursorTimeline(width=1280, height=900)
    tl.add(CursorEvent(t_ms=10, type="move", x=0.2, y=0.3, beat_id="hook"))
    tl.add(CursorEvent(t_ms=40, type="click", x=0.2, y=0.3, beat_id="hook", label="Got it"))
    path = tl.write(tmp_path / "cursor.json")
    loaded = CursorTimeline.load(path)
    assert loaded.width == 1280
    assert len(loaded.events) == 2
    assert loaded.focus_per_beat()["hook"] == (0.2, 0.3)
    side = write_openscreen_sidecar(loaded, tmp_path / "cursor.openscreen.json")
    data = json.loads(side.read_text(encoding="utf-8"))
    assert data["version"] == 2
    assert len(data["samples"]) == 2
