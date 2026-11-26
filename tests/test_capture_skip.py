"""Task 3: capture engines must never visit clip-source beats.

Frames for clip beats must not exist at all — Task 4 assembles per-beat pictures
by globbing ``NN_<beat-id>.png`` and errors when a *capture* beat has no frames.
The engine tests below drive the real per-beat loops with the screenshot call
site intercepted, so removing the ``visual_kind(beat) == "clip"`` guard fails.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

from demo_studio.beats import visual_kind


def test_clip_beats_filter_helper():
    beats = [
        {"id": "a", "narration": "x"},
        {"id": "b", "narration": "y", "visual": {"kind": "clip", "file": "f.mp4"}},
    ]
    browser_beats = [b for b in beats if visual_kind(b) == "capture"]
    assert [b["id"] for b in browser_beats] == ["a"]


def _pack() -> dict:
    # Beat b carries a navigate action on purpose: without the clip guard the
    # engine would visit it and write a frame, which is exactly what Task 4
    # must never see. (validate_visuals rejects actions on clip beats; the
    # engines still have to be safe against them.) Beat c comes *after* the
    # clip beat so a `break` in place of `continue` cannot pass.
    return {
        "version": 1,
        "product": "p",
        "beats": [
            {"id": "a", "narration": "x", "actions": [{"type": "navigate", "path": "/a"}]},
            {
                "id": "b",
                "narration": "y",
                "visual": {"kind": "clip", "file": "f.mp4"},
                "actions": [{"type": "navigate", "path": "/b"}],
            },
            {"id": "c", "narration": "z", "actions": [{"type": "navigate", "path": "/c"}]},
        ],
    }


def test_chrome_capture_skips_clip_beats(tmp_path, monkeypatch):
    from demo_studio import chrome_capture

    written_shots: list[str] = []

    class _Proc:
        returncode = 0
        stderr = ""

    def fake_run(cmd, **kwargs):
        # Real call site: chrome is invoked as ``--screenshot=<path>``.
        out = next(str(a) for a in cmd if str(a).startswith("--screenshot=")).split("=", 1)[1]
        Path(out).write_bytes(b"")
        written_shots.append(Path(out).name)
        return _Proc()

    monkeypatch.setattr(chrome_capture, "_chrome_bin", lambda: "/bin/chrome")
    monkeypatch.setattr(chrome_capture.subprocess, "run", fake_run)

    frames = tmp_path / "frames"
    result = chrome_capture.capture_beat_frames(
        _pack(), "http://x", frames, width=320, height=240
    )

    assert written_shots == ["01_a.png", "02_c.png"]
    assert not any("_b." in n for n in written_shots)
    assert [p.name for p in result] == ["01_a.png", "02_c.png"]
    assert sorted(p.name for p in frames.iterdir()) == ["01_a.png", "02_c.png"]


def test_playwright_capture_skips_clip_beats(tmp_path, monkeypatch):
    from demo_studio import playwright_capture

    shots: list[str] = []

    page = MagicMock()
    page.url = "http://x/a"

    def fake_screenshot(*, path: str, **kwargs):
        shots.append(Path(path).name)

    page.screenshot.side_effect = fake_screenshot

    # playwright_capture imports sync_playwright inside the function, so inject
    # a fake module rather than requiring the real browser.
    session = MagicMock()
    session.__enter__.return_value.chromium.launch.return_value.new_page.return_value = page
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = lambda: session
    pkg = types.ModuleType("playwright")
    pkg.sync_api = sync_api  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", pkg)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)

    frames = tmp_path / "frames"
    result = playwright_capture.capture_beat_frames_playwright(
        _pack(), "http://x", frames, width=320, height=240
    )

    assert shots == ["01_a.png", "02_c.png"]
    assert not any("_b." in n for n in shots)
    assert [p.name for p in result] == ["01_a.png", "02_c.png"]
    # Never visited at all: base page + beat a + beat c navigated, no
    # cursor-timeline marker for the clip beat.
    assert page.goto.call_count == 3
    timeline = json.loads((tmp_path / "cursor.json").read_text(encoding="utf-8"))
    assert {e["beat_id"] for e in timeline["events"]} == {"a", "c"}
