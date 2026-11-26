from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def probe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not on PATH")
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr[-400:]}")
    data = json.loads(proc.stdout)
    stream = (data.get("streams") or [{}])[0]
    return {
        "duration_s": float(data["format"]["duration"]),
        "width": int(stream.get("width") or 0),
        "height": int(stream.get("height") or 0),
    }


def probe_streams(path: Path) -> dict[str, float | None]:
    """Per-stream durations in seconds keyed by codec_type (video/audio/...).

    A missing or unparseable stream duration is reported as None so callers
    can assert parity explicitly (container duration alone hides a short
    audio track behind a correct-looking total).
    """
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not on PATH")
    proc = subprocess.run(
        [ffprobe, "-v", "error",
         "-show_entries", "stream=codec_type,duration,duration_time",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr[-400:]}")
    durations: dict[str, float | None] = {}
    for stream in json.loads(proc.stdout).get("streams") or []:
        ctype = stream.get("codec_type")
        if not ctype or ctype in durations:
            continue
        raw = stream.get("duration") or stream.get("duration_time")
        try:
            durations[ctype] = float(raw)
        except (TypeError, ValueError):
            durations[ctype] = None
    return durations


def build_segment_cmd(
    ffmpeg: str,
    source: Path,
    out: Path,
    *,
    in_sec: float,
    out_sec: float,
    width: int,
    height: int,
    target_dur_s: float | None = None,
) -> list[str]:
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        # setsar=1 after pad: a source with a non-unity SAR (e.g. 848x478 DAR
        # 424:239) otherwise keeps a near-unity stamp and breaks the
        # concat=n=N:v=1:a=1 in assemble.py. Same convention as polish.py and
        # studio_compose.py.
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p"
    )
    window = out_sec - in_sec
    if target_dur_s and target_dur_s > window:
        vf += f",tpad=stop_mode=clone:stop_duration={target_dur_s - window:.3f}"
    cmd = [
        ffmpeg, "-y", "-v", "error",
        "-ss", f"{in_sec:.3f}", "-to", f"{out_sec:.3f}", "-i", str(source),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        # Map explicitly: without this ffmpeg picks the clip's own audio stream
        # (lowest index) instead of the lavfi source, so the track is not silent
        # and -shortest truncates the output at the un-padded window length.
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-ar", "48000",
    ]
    if target_dur_s:
        cmd += ["-t", f"{target_dur_s:.3f}"]
    cmd += ["-shortest", str(out)]
    return cmd


def clip_segment(
    source: Path,
    out: Path,
    *,
    in_sec: float = 0.0,
    out_sec: float | None = None,
    width: int = 1920,
    height: int = 1080,
    target_dur_s: float | None = None,
) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    info = probe_video(source)
    if in_sec >= info["duration_s"]:
        raise RuntimeError(f"{source}: in_sec {in_sec} beyond clip duration {info['duration_s']:.1f}s")
    end = min(float(out_sec), info["duration_s"]) if out_sec else info["duration_s"]
    if end <= in_sec:
        raise RuntimeError(f"{source}: out_sec {end} must be greater than in_sec {in_sec}")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_segment_cmd(ffmpeg, source, out, in_sec=in_sec, out_sec=end,
                            width=width, height=height, target_dur_s=target_dur_s)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"clip segment failed for {source}: {proc.stderr[-800:]}")
    return {"out": str(out), "duration_s": target_dur_s or (end - in_sec), "cmd": cmd}
