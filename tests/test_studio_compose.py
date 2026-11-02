from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from demo_studio.cursor_timeline import CursorEvent, CursorTimeline
from demo_studio.studio_compose import compose_studio_mp4


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_compose_studio_from_two_frames(tmp_path: Path) -> None:
    frames = tmp_path / "frames"
    frames.mkdir()
    for name, color in (("01_hook.png", "0x224466"), ("02_next.png", "0x663322")):
        proc = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=640x360:d=0.04",
                "-frames:v",
                "1",
                str(frames / name),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr[-400:]

    tl = CursorTimeline(width=640, height=360)
    tl.add(CursorEvent(t_ms=0, type="beat", x=0.5, y=0.5, beat_id="hook"))
    tl.add(CursorEvent(t_ms=100, type="click", x=0.35, y=0.4, beat_id="hook", label="A"))
    tl.add(CursorEvent(t_ms=200, type="beat", x=0.5, y=0.5, beat_id="next"))
    tl.add(CursorEvent(t_ms=300, type="click", x=0.7, y=0.55, beat_id="next", label="B"))
    tl.write(tmp_path / "cursor.json")
    (tmp_path / "narration").mkdir()
    (tmp_path / "narration" / "narration.json").write_text(
        json.dumps(
            {
                "cues": [
                    {"start_ms": 0, "end_ms": 1500, "file": "a.wav"},
                    {"start_ms": 1500, "end_ms": 3000, "file": "b.wav"},
                ]
            }
        ),
        encoding="utf-8",
    )

    out = tmp_path / "picture.mp4"
    result = compose_studio_mp4(tmp_path, out, zoom=1.35, fps=24)
    assert result["ok"]
    assert out.is_file() and out.stat().st_size > 0
