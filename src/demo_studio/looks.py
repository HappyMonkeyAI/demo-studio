from __future__ import annotations

"""Recordly-inspired look presets (ffmpeg only — no third-party GUI runtime)."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

LOOK_PRESETS = ("clean", "product-zoom")


def list_looks() -> tuple[str, ...]:
    return LOOK_PRESETS


def _ffprobe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not on PATH (install ffmpeg)")
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,nb_frames:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "ffprobe failed")
    data = json.loads(proc.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}
    width = int(stream.get("width") or 1280)
    height = int(stream.get("height") or 720)
    duration = float(fmt.get("duration") or 0.0)
    rate = stream.get("r_frame_rate") or "30/1"
    try:
        num, den = rate.split("/", 1)
        fps = float(num) / float(den) if float(den) else 30.0
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    nb = stream.get("nb_frames")
    try:
        frames = int(nb) if nb and str(nb).isdigit() else max(int(duration * fps), 1)
    except (TypeError, ValueError):
        frames = max(int(duration * fps), 1)
    return {"width": width, "height": height, "fps": fps, "duration": duration, "frames": frames}


def apply_look(
    picture_mp4: Path,
    out_mp4: Path,
    *,
    look: str = "clean",
) -> Path:
    """Rewrite picture track with a named look. `clean` copies through."""
    look = (look or "clean").strip().lower()
    if look not in LOOK_PRESETS:
        raise ValueError(f"unknown look {look!r}; choose from {', '.join(LOOK_PRESETS)}")

    if not picture_mp4.is_file():
        raise FileNotFoundError(str(picture_mp4))

    if look == "clean":
        if picture_mp4.resolve() != out_mp4.resolve():
            out_mp4.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(picture_mp4, out_mp4)
        return out_mp4

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")

    meta = _ffprobe_video(picture_mp4)
    w, h = meta["width"], meta["height"]
    fps = max(1.0, float(meta["fps"]))
    frames = max(int(meta["frames"]), 2)
    # ~8% push-in over the clip (Recordly-ish product energy, still readable UI)
    zoom_extra = 0.08
    denom = frames - 1
    z_expr = f"min(1+{zoom_extra}*on/{denom},{1 + zoom_extra})"
    vf = (
        f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={w}x{h}:fps={fps}"
    )

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    # Write to temp name if in-place
    target = out_mp4
    tmp = out_mp4
    if picture_mp4.resolve() == out_mp4.resolve():
        tmp = out_mp4.with_suffix(".look.tmp.mp4")

    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(picture_mp4),
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(tmp),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or "look filter failed")

    if tmp != target:
        tmp.replace(target)
    return target
