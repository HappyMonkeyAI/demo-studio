"""Task 4: per-beat picture assembly aligned to narration cues.

The still+clip integration test asserts MEASURED per-stream durations
(clips.probe_streams), not the requested value echoed by clip_segment —
Task 2's Important finding: a container-level check can hide a short or
missing audio track.
"""

import json
import shutil
import subprocess
import pytest
from pathlib import Path
from demo_studio.assemble import concat_segments


def test_concat_segments_argv(tmp_path, monkeypatch):
    from demo_studio import assemble
    calls = []
    monkeypatch.setattr(assemble.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd) or type("P", (), {"returncode": 0, "stderr": ""})())
    monkeypatch.setattr(shutil, "which", lambda n: "ffmpeg")
    segs = [tmp_path / "00_a.mp4", tmp_path / "01_b.mp4"]
    for s in segs:
        s.write_bytes(b"")
    concat_segments("ffmpeg", segs, tmp_path / "picture.mp4")
    cmd = " ".join(calls[0])
    assert "concat=n=2:v=1:a=1" in cmd and "-vsync" not in cmd


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_assemble_picture_requires_frames(tmp_path):
    from demo_studio.assemble import assemble_picture
    data = {"version": 1, "product": "p", "beats": [{"id": "a", "narration": "x"}]}
    cues = [{"file": "a.wav", "duration_ms": 1000, "start_ms": 0, "end_ms": 1000}]
    with pytest.raises(RuntimeError, match="no frames for beat a"):
        assemble_picture(data, cues, tmp_path / "frames", tmp_path,
                         pack_dir=tmp_path, width=320, height=240)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_assemble_picture_still_plus_clip(tmp_path):
    from demo_studio.assemble import assemble_picture
    from demo_studio.clips import probe_streams, probe_video
    frames = tmp_path / "frames"
    frames.mkdir()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "color=c=red:s=320x240", "-frames:v", "1",
                    str(frames / "01_a.png")], check=True)
    clip = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=size=160x120:rate=30", "-t", "2",
                    "-c:v", "libx264", str(clip)], check=True)
    data = {"version": 1, "product": "p", "beats": [
        {"id": "a", "narration": "x"},
        {"id": "b", "narration": "y", "visual": {"kind": "clip", "file": "clip.mp4", "in_sec": 0.5, "out_sec": 1.5}},
    ]}
    cues = [{"file": "a.wav", "duration_ms": 1500, "start_ms": 0, "end_ms": 1500},
            {"file": "b.wav", "duration_ms": 2000, "start_ms": 1500, "end_ms": 3500}]
    res = assemble_picture(data, cues, frames, tmp_path, pack_dir=tmp_path, width=320, height=240)
    assert res["segments"] == 2
    info = probe_video(Path(res["picture"]))
    assert 3.0 <= info["duration_s"] <= 4.0  # 1.5s still + 2.0s clip segment
    assert info["width"] == 320

    # Measured (not echoed) stream-level assertions on the assembled picture:
    # the concat carries audio per segment (v=1:a=1), but the shipped
    # picture.mp4 is stripped video-only so mux_package's unmapped selection
    # keeps preferring voice.wav (see assemble.py) — total duration is the
    # MEASURED video stream, expected 1.5 + 2.0 = 3.5 s.
    streams = probe_streams(Path(res["picture"]))
    assert streams.get("video") is not None
    assert streams.get("audio") is None
    assert 3.0 <= streams["video"] <= 4.0
    assert abs(res["total_s"] - 3.5) < 0.01
    # Segment files use the NN_<beat-id>.mp4 naming under job_dir/segments/.
    seg_names = sorted(p.name for p in (tmp_path / "segments").iterdir())
    assert seg_names == ["00_a.mp4", "01_b.mp4"]

    # The clip segment itself must be probe-verified, not trusted from
    # clip_segment's echoed duration_s: window 1.0s frozen (tpad) to the
    # 2.0s cue, scaled to the canvas, with a real silent audio track.
    seg_streams = probe_streams(tmp_path / "segments" / "01_b.mp4")
    assert seg_streams.get("audio") is not None
    assert abs(seg_streams["video"] - 2.0) < 0.15
    assert abs(seg_streams["video"] - seg_streams["audio"]) < 0.1
    seg_info = probe_video(tmp_path / "segments" / "01_b.mp4")
    assert (seg_info["width"], seg_info["height"]) == (320, 240)


def test_frames_to_mp4_uses_explicit_frames(tmp_path, monkeypatch):
    """assemble.py passes a per-beat frame subset; the glob must be bypassed."""
    from demo_studio import capture

    calls = []
    monkeypatch.setattr(capture.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd) or type("P", (), {"returncode": 0, "stderr": ""})())
    monkeypatch.setattr(capture.shutil, "which", lambda n: "ffmpeg")
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    a, b = frames_dir / "01_a.png", frames_dir / "02_b.png"
    a.write_bytes(b"")
    b.write_bytes(b"")
    res = capture.frames_to_mp4(frames_dir, tmp_path / "seg.mp4",
                                durations_sec=[2.0], frames=[b])
    assert res["frames"] == 1
    list_txt = (frames_dir / "frames.txt").read_text(encoding="utf-8")
    assert "02_b.png" in list_txt
    assert "01_a.png" not in list_txt
    assert "duration 2.000000" in list_txt


# --- Task 4 review, fix round 1 -------------------------------------------------


def _write_clip_only_pack(tmp_path: Path) -> Path:
    beats = tmp_path / "demo.beats.json"
    beats.write_text(
        json.dumps(
            {
                "version": 1,
                "product": "clips-only",
                "beats": [
                    {"id": "a", "narration": "one",
                     "visual": {"kind": "clip", "file": "clip.mp4", "in_sec": 0.0, "out_sec": 1.0}},
                    {"id": "b", "narration": "two",
                     "visual": {"kind": "clip", "file": "clip.mp4", "in_sec": 0.0, "out_sec": 1.0}},
                ],
            }
        ),
        encoding="utf-8",
    )
    return beats


def _install_fake_playwright(monkeypatch, shots: list[str]) -> None:
    """Fake browser module around the REAL engine loop (test_capture_skip style).

    With every beat `kind: clip` the real per-beat loop writes zero frames and
    playwright_capture raises "no frames captured" — finding 1. Only the browser
    is faked; the CLI/jobs orchestration under test is unmocked, so the failure
    (and its absence after the fix) is the real one.
    """
    import sys
    import types
    from unittest.mock import MagicMock

    page = MagicMock()
    page.url = "http://x/"
    page.screenshot.side_effect = lambda *, path, **kw: shots.append(Path(path).name)
    session = MagicMock()
    session.__enter__.return_value.chromium.launch.return_value.new_page.return_value = page
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = lambda: session
    pkg = types.ModuleType("playwright")
    pkg.sync_api = sync_api  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", pkg)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)


def test_cli_capture_all_clip_pack_skips_engine(tmp_path, monkeypatch, capsys):
    """Finding 1: a clip-only pack must not die in the engine at capture time."""
    from demo_studio import cli

    shots: list[str] = []
    _install_fake_playwright(monkeypatch, shots)
    monkeypatch.setenv("DEMO_BASE_URL", "http://x")
    beats = _write_clip_only_pack(tmp_path)
    run_dir = tmp_path / "run"
    args = cli.build_parser().parse_args(
        ["capture", str(beats), "--run-dir", str(run_dir), "--engine", "playwright"]
    )

    rc = cli._cmd_capture(args)
    captured = capsys.readouterr()

    assert rc == 0, f"capture failed: {captured.err}"
    assert shots == []  # no browser work for a pack with nothing to screenshot
    payload = json.loads(captured.out)
    assert payload["picture"] == {"deferred": True}
    assert payload["frames"] == []
    assert "deferred" in captured.err


def test_run_job_all_clip_pack_skips_engine(tmp_path, monkeypatch):
    """Finding 1, jobs path: same deferral as the CLI, no engine dispatch."""
    from demo_studio import jobs

    shots: list[str] = []
    _install_fake_playwright(monkeypatch, shots)
    monkeypatch.setattr(
        jobs, "capture_beat_frames",
        lambda *a, **k: pytest.fail("chrome engine dispatched for a clip-only pack"),
    )
    cues = [
        {"file": "a.wav", "duration_ms": 1000, "start_ms": 0, "end_ms": 1000},
        {"file": "b.wav", "duration_ms": 1000, "start_ms": 1000, "end_ms": 2000},
    ]
    monkeypatch.setattr(jobs, "narrate_beats",
                        lambda *a, **k: {"provider": "fake", "total_ms": 2000, "cues": cues})
    monkeypatch.setattr(jobs, "assemble_picture",
                        lambda *a, **k: {"segments": 2, "picture": "x", "total_s": 2.0})
    monkeypatch.setattr(jobs, "mux_package",
                        lambda job_dir, look="clean": {"demo": str(Path(job_dir) / "demo.mp4")})

    svc = jobs.DemoJobService(tmp_path)
    meta = svc.create_job(str(_write_clip_only_pack(tmp_path)), base_url="http://x")
    out = svc.run_job(meta["job_id"], engine="playwright")

    assert out["status"] == "awaiting_final_review"
    assert out["steps"]["capture"] == {"engine": "none", "picture": "deferred"}
    assert out["steps"]["assemble"]["segments"] == 2
    assert shots == []


def test_run_job_skip_capture_clip_pack_without_picture_fails(tmp_path, monkeypatch):
    """Finding 2: skip_capture + clip beats + no picture must not ship a color card."""
    from demo_studio import jobs

    def fake_mux(job_dir, look="clean"):
        # Stands in for mux_package's color-card branch (package_run.py:124-145),
        # which happily produces a clip-free demo.mp4 and a green job.
        demo = Path(job_dir) / "demo.mp4"
        demo.write_bytes(b"")
        return {"demo": str(demo)}

    monkeypatch.setattr(jobs, "narrate_beats", lambda *a, **k: {"provider": "fake", "cues": []})
    monkeypatch.setattr(jobs, "mux_package", fake_mux)

    svc = jobs.DemoJobService(tmp_path)
    meta = svc.create_job(str(_write_clip_only_pack(tmp_path)), base_url="http://x")
    job_dir = svc._job_dir(meta["job_id"])

    with pytest.raises(RuntimeError, match="picture.mp4"):
        svc.run_job(meta["job_id"], skip_capture=True, skip_narrate=True)

    assert not (job_dir / "demo.mp4").is_file()
    assert svc.get_job(meta["job_id"])["status"] != "awaiting_final_review"


def test_run_job_skip_capture_clip_pack_with_picture_warns(tmp_path, monkeypatch, capsys):
    """Finding 2, stale picture: packaging an existing picture is allowed but loud."""
    from demo_studio import jobs

    monkeypatch.setattr(jobs, "narrate_beats", lambda *a, **k: {"provider": "fake", "cues": []})
    monkeypatch.setattr(jobs, "mux_package",
                        lambda job_dir, look="clean": {"demo": str(Path(job_dir) / "demo.mp4")})

    svc = jobs.DemoJobService(tmp_path)
    meta = svc.create_job(str(_write_clip_only_pack(tmp_path)), base_url="http://x")
    job_dir = svc._job_dir(meta["job_id"])
    (job_dir / "picture.mp4").write_bytes(b"")  # e.g. from an earlier capture

    out = svc.run_job(meta["job_id"], skip_capture=True, skip_narrate=True)

    assert out["status"] == "awaiting_final_review"
    err = capsys.readouterr().err
    assert "picture.mp4" in err and "clip" in err
