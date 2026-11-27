from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from demo_studio.clips import build_segment_cmd, probe_streams


def _max_volume_db(path: Path) -> float:
    """Decode the audio stream and return volumedetect's max_volume in dB."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-vn", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    m = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", proc.stderr)
    assert m, f"volumedetect produced no max_volume for {path}"
    return float(m.group(1))


def _vf(cmd: list[str]) -> str:  # extract -vf argument
    return cmd[cmd.index("-vf") + 1]


def _stream_sar(path: Path) -> str:
    """Video-stream sample aspect ratio as stamped in the container.

    Strict on purpose: an unstamped track probes as "N/A", and assemble.py's
    concat filter only accepts a segment whose SAR matches the others, so the
    assertion is on the explicit square stamp, not on "square by omission".
    """
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=sample_aspect_ratio",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip()


def test_build_segment_cmd_core() -> None:
    cmd = build_segment_cmd("ffmpeg", Path("/in.mp4"), Path("/out.mp4"),
                            in_sec=42.0, out_sec=97.0, width=1920, height=1080)
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd and "42.000" in cmd
    assert "-to" in cmd and "97.000" in cmd
    vf = _vf(cmd)
    assert "scale=1920:1080:force_original_aspect_ratio=decrease" in vf
    assert "pad=1920:1080:(ow-iw)/2:(oh-ih)/2" in vf
    # setsar must land right after pad (polish.py / studio_compose.py convention):
    # assemble.py's concat filter rejects a segment whose SAR differs from the rest
    assert "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" in vf
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


@pytest.mark.parametrize("target_dur_s", [0.0, -1.0])
def test_build_segment_cmd_rejects_non_positive_target(target_dur_s: float) -> None:
    with pytest.raises(ValueError, match="target_dur_s"):
        build_segment_cmd("ffmpeg", Path("/in.mp4"), Path("/out.mp4"),
                          in_sec=0.0, out_sec=4.0, width=1920, height=1080,
                          target_dur_s=target_dur_s)


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
    # container duration alone passes on the "video 6.0 / audio 2.0 / loud"
    # regression, so pin both streams and silence explicitly
    streams = probe_streams(out)
    video_dur = streams.get("video")
    audio_dur = streams.get("audio")
    assert video_dur is not None and audio_dur is not None, f"streams: {streams}"
    assert abs(audio_dur - video_dur) < 0.1   # silent track spans the whole clip
    assert _max_volume_db(out) <= -80.0       # any source audio leaking is a defect


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_clip_segment_stamps_square_sar_on_non_unity_source(tmp_path: Path) -> None:
    """A non-unity-SAR source must leave the segment builder square-pixelled.

    The repo's other fixtures are unity-SAR color/testsrc sources, so they can
    never go red on this: the segment filter chain has to normalise SAR itself.
    Run 1 of the ai-update reel hit exactly this — ~/Videos/untitled.mp4
    (848x478, DAR 424:239) came out stamped SAR 114480:114481 and broke
    `concat=n=24:v=1:a=1` with "Input link ... parameters ... do not match".
    """
    from demo_studio.clips import clip_segment
    src = tmp_path / "nonunity.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=size=320x240:rate=30",
                    "-vf", "setsar=4:3", "-t", "3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)], check=True)
    # the fixture is only meaningful if it really carries a non-unity SAR
    assert _stream_sar(src) not in ("1:1", "N/A", ""), f"fixture SAR: {_stream_sar(src)}"
    out = tmp_path / "seg.mp4"
    clip_segment(src, out, in_sec=0.0, out_sec=2.0, width=640, height=360)
    assert _stream_sar(out) == "1:1", f"segment SAR not square: {_stream_sar(out)}"
