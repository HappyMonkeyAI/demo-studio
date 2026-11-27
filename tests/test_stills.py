from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from demo_studio.beats import validate_beats
from demo_studio.package_run import write_vtt
from demo_studio.stills import compose_stills_mp4, plan_stills


def _beats(*ids_and_stills: tuple[str, str | None]) -> dict:
    beats = []
    for bid, still in ids_and_stills:
        beat = {"id": bid, "narration": f"Beat {bid}."}
        if still:
            beat["still"] = still
        beats.append(beat)
    return {"version": 1, "product": "stills-test", "beats": beats}


def _cues(*pairs: tuple[str, int]) -> list[dict]:
    cues, t = [], 0
    for bid, dur in pairs:
        cues.append({"beat": bid, "start_ms": t, "end_ms": t + dur})
        t += dur
    return cues


def test_schema_accepts_still() -> None:
    assert validate_beats(_beats(("a", "a.png"))) == []


def test_plan_pairs_stills_with_cue_durations(tmp_path: Path) -> None:
    (tmp_path / "a.png").write_bytes(b"x")
    (tmp_path / "b.png").write_bytes(b"x")
    data = _beats(("a", "a.png"), ("b", "b.png"))
    plan = plan_stills(data, tmp_path / "demo.beats.json", _cues(("a", 1500), ("b", 2250)))
    assert [p["beat"] for p in plan] == ["a", "b"]
    assert [p["duration_s"] for p in plan] == [1.5, 2.25]
    assert plan[0]["image"] == (tmp_path / "a.png").resolve()


def test_plan_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "a.png").write_bytes(b"x")
    data = _beats(("a", "a.png"), ("b", None), ("c", "missing.png"))
    with pytest.raises(ValueError) as exc:
        plan_stills(data, tmp_path / "demo.beats.json", _cues(("a", 1000), ("x", 1000)))
    msg = str(exc.value)
    assert "3 beats but 2 narration cues" in msg
    assert "'b' has no 'still'" in msg
    assert "still not found" in msg
    assert "expected 'a'" not in msg  # first cue matches


def test_vtt_offset(tmp_path: Path) -> None:
    out = tmp_path / "c.vtt"
    write_vtt([{"start_ms": 0, "end_ms": 1000, "text": "hi"}], out, offset_ms=2500)
    assert "00:00:02.500 --> 00:00:03.500" in out.read_text(encoding="utf-8")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
@pytest.mark.parametrize("motion", ["push", "none"])
def test_compose_matches_narration_length(tmp_path: Path, motion: str) -> None:
    from demo_studio.looks import _ffprobe_duration, _ffprobe_video

    for name, colour, size in (("a.png", "red", "800x600"), ("b.png", "blue", "1920x1080")):
        proc = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={colour}:s={size}", "-frames:v", "1", str(tmp_path / name)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr[-500:]
    data = _beats(("a", "a.png"), ("b", "b.png"))
    narration = tmp_path / "narration.json"
    narration.write_text(json.dumps({"cues": _cues(("a", 1200), ("b", 800))}), encoding="utf-8")
    out = tmp_path / "run" / "picture.mp4"

    manifest = compose_stills_mp4(
        data, tmp_path / "demo.beats.json", narration, out, width=640, height=360, motion=motion
    )

    assert out.is_file()
    assert abs(_ffprobe_duration(out) - 2.0) < 0.15
    meta = _ffprobe_video(out)
    assert (meta["width"], meta["height"]) == (640, 360)
    assert [s["frames"] for s in manifest["stills"]] == [36, 24]
    assert (out.parent / "stills.json").is_file()
