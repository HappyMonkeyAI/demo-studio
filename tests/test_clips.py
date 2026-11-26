from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from demo_studio.clips import build_segment_cmd


def _vf(cmd: list[str]) -> str:  # extract -vf argument
    return cmd[cmd.index("-vf") + 1]


def test_build_segment_cmd_core() -> None:
    cmd = build_segment_cmd("ffmpeg", Path("/in.mp4"), Path("/out.mp4"),
                            in_sec=42.0, out_sec=97.0, width=1920, height=1080)
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd and "42.000" in cmd
    assert "-to" in cmd and "97.000" in cmd
    vf = _vf(cmd)
    assert "scale=1920:1080:force_original_aspect_ratio=decrease" in vf
    assert "pad=1920:1080:(ow-iw)/2:(oh-ih)/2" in vf
    assert "fps=30" in vf and "format=yuv420p" in vf
    assert "tpad" not in vf                      # no padding without target
    assert "anullsrc" in " ".join(cmd)           # silent audio track always
    # explicit maps: the lavfi anullsrc track must win over the clip's own audio
    assert "-map" in cmd and "0:v:0" in cmd and "1:a:0" in cmd
    assert "-vsync" not in " ".join(cmd)         # removed in ffmpeg 9


def test_build_segment_cmd_pads_short_clip() -> None:
    cmd = build_segment_cmd("ffmpeg", Path("/in.mp4"), Path("/out.mp4"),
                            in_sec=0.0, out_sec=4.0, width=1920, height=1080,
                            target_dur_s=10.0)
    vf = _vf(cmd)
    assert "tpad=stop_mode=clone:stop_duration=6.000" in vf
    assert "-t" in cmd and "10.000" in cmd


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_clip_segment_real_trim_and_pad(tmp_path: Path) -> None:
    from demo_studio.clips import clip_segment, probe_video
    src = tmp_path / "src.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=size=320x240:rate=60", "-t", "4",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-shortest", "-c:v", "libx264", str(src)], check=True)
    out = tmp_path / "seg.mp4"
    clip_segment(src, out, in_sec=1.0, out_sec=3.0, width=640, height=360, target_dur_s=6.0)
    info = probe_video(out)
    assert info["width"] == 640 and info["height"] == 360
    assert 5.5 <= info["duration_s"] <= 6.5   # 2s window padded to 6s
