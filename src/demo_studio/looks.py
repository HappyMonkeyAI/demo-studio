from __future__ import annotations

"""Recordly-inspired look presets (ffmpeg only — no third-party GUI runtime).

Important: do not bake zoom into a short picture.mp4 that mux later loops —
that restarts the Ken Burns every loop (jerky zoom → cut → zoom). Apply motion
across the full VO duration in one pass instead.
"""

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


def _ffprobe_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not on PATH (install ffmpeg)")
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "ffprobe duration failed")
    try:
        return max(float((proc.stdout or "0").strip()), 0.1)
    except ValueError as exc:
        raise RuntimeError(f"bad duration for {path}") from exc


def product_zoom_filter(*, width: int, height: int, duration_s: float, fps: float = 30.0) -> str:
    """One continuous ~8% center push-in over duration_s (output frame index `on`)."""
    fps = max(float(fps), 1.0)
    total_frames = max(int(duration_s * fps), 2)
    denom = total_frames - 1
    zoom_extra = 0.08
    z_expr = f"min(1+{zoom_extra}*on/{denom},{1 + zoom_extra})"
    # Upscale slightly so zoompan can crop without inventing empty edges.
    return (
        f"fps={fps},"
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"scale=iw*1.12:ih*1.12,"
        f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={width}x{height}:fps={fps}"
    )


def apply_look(
    picture_mp4: Path,
    out_mp4: Path,
    *,
    look: str = "clean",
    duration_s: float | None = None,
) -> Path:
    """Render a full-length looked picture track.

    For `product-zoom`, loops the source as needed and applies **one** continuous
    zoom across `duration_s` (required for sensible motion; defaults to source
    duration only for short unit tests).
    """
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
    target_dur = float(duration_s) if duration_s is not None else float(meta["duration"] or 1.0)
    target_dur = max(target_dur, 0.5)
    fps = 30.0
    vf = product_zoom_filter(width=w, height=h, duration_s=target_dur, fps=fps)

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    target = out_mp4
    tmp = out_mp4
    if picture_mp4.resolve() == out_mp4.resolve():
        tmp = out_mp4.with_suffix(".look.tmp.mp4")

    # Loop source while generating a single continuous zoom spanning target_dur.
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(picture_mp4),
            "-vf",
            vf,
            "-t",
            f"{target_dur:.3f}",
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


def mux_video_filter_for_look(
    look: str,
    *,
    picture: Path,
    duration_s: float,
) -> str | None:
    """Return an ffmpeg -vf string for mux, or None for clean/passthrough."""
    look = (look or "clean").strip().lower()
    if look == "clean":
        return None
    if look != "product-zoom":
        raise ValueError(f"unknown look {look!r}; choose from {', '.join(LOOK_PRESETS)}")
    meta = _ffprobe_video(picture)
    return product_zoom_filter(
        width=meta["width"],
        height=meta["height"],
        duration_s=duration_s,
        fps=30.0,
    )
