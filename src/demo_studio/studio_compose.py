from __future__ import annotations

"""Compose beat stills + cursor timeline into a soft zoom / pointer demo clip."""

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from demo_studio.cursor_timeline import CursorTimeline

def _ensure_cursor_png(work: Path) -> Path:
    """Generate a simple arrow-ish cursor PNG via ffmpeg (no binary assets)."""
    out = work / "_studio_cursor.png"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black@0.0:s=48x48:d=0.04,format=rgba",
            "-vf",
            (
                "drawbox=x=6:y=4:w=4:h=28:color=white@1.0:t=fill,"
                "drawbox=x=6:y=4:w=18:h=4:color=white@1.0:t=fill,"
                "drawbox=x=6:y=16:w=14:h=4:color=white@1.0:t=fill,"
                "drawbox=x=4:y=2:w=8:h=32:color=black@0.85:t=1"
            ),
            "-frames:v",
            "1",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not out.is_file():
        raise RuntimeError(proc.stderr[-1500:] or "cursor png failed")
    return out


def _beat_durations_sec(
    frames: list[Path],
    *,
    narration_json: Path | None,
    default_sec: float = 4.0,
) -> list[float]:
    if narration_json and narration_json.is_file():
        data = json.loads(narration_json.read_text(encoding="utf-8"))
        cues = data.get("cues") or []
        if len(cues) == len(frames):
            out = []
            for cue in cues:
                start = int(cue.get("start_ms") or 0)
                end = int(cue.get("end_ms") or start + 4000)
                out.append(max(1.2, (end - start) / 1000.0))
            return out
    return [default_sec] * len(frames)


def _zoom_crop_filter(
    *,
    width: int,
    height: int,
    cx: float,
    cy: float,
    zoom: float,
) -> str:
    """ffmpeg vf: scale up then crop viewport centered near (cx,cy)."""
    z = max(1.0, min(float(zoom), 2.2))
    # Crop window in source pixels after scale=z
    # Using zoompan single-frame style via scale+crop.
    cx = min(max(cx, 0.05), 0.95)
    cy = min(max(cy, 0.05), 0.95)
    # Expression-friendly integers for crop size
    return (
        f"scale=iw*{z}:ih*{z},"
        f"crop={width}:{height}:"
        f"'min(max(iw*{cx}-ow/2\\,0)\\,iw-ow)':"
        f"'min(max(ih*{cy}-oh/2\\,0)\\,ih-oh)'"
    )


def compose_studio_mp4(
    run_dir: Path,
    out_mp4: Path | None = None,
    *,
    zoom: float = 1.45,
    fps: int = 30,
) -> dict[str, Any]:
    """Build a soft-zoom + cursor overlay MP4 from frames/ + cursor.json."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")

    frames_dir = run_dir / "frames"
    cursor_path = run_dir / "cursor.json"
    if not cursor_path.is_file():
        raise FileNotFoundError(f"missing {cursor_path} (re-capture with Playwright)")

    frames = sorted(
        [*frames_dir.glob("*.png"), *frames_dir.glob("*.jpg"), *frames_dir.glob("*.jpeg")]
    )
    if not frames:
        raise RuntimeError(f"no frames in {frames_dir}")

    timeline = CursorTimeline.load(cursor_path)
    width = timeline.width
    height = timeline.height
    foci = timeline.focus_per_beat()
    durations = _beat_durations_sec(
        frames,
        narration_json=run_dir / "narration" / "narration.json",
    )

    work = run_dir / "_studio_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    cursor_png = _ensure_cursor_png(work)

    # Map frame filename beat id: "01_hook.png" -> hook
    segment_clips: list[Path] = []
    prev_focus = (0.5, 0.5)
    for i, frame in enumerate(frames):
        stem = frame.stem
        beat_id = stem.split("_", 1)[1] if "_" in stem else stem
        cx, cy = foci.get(beat_id, (0.5, 0.5))
        for ev in timeline.events:
            if ev.beat_id == beat_id and ev.type == "click":
                cx, cy = ev.x, ev.y
        dur = durations[i] if i < len(durations) else 4.0

        if i > 0:
            mid_x = (prev_focus[0] + cx) / 2
            mid_y = (prev_focus[1] + cy) / 2
            bridge = work / f"bridge_{i:02d}.mp4"
            vf_b = _zoom_crop_filter(width=width, height=height, cx=mid_x, cy=mid_y, zoom=1.2)
            oxb = max(0, min(int(mid_x * width) - 4, width - 48))
            oyb = max(0, min(int(mid_y * height) - 4, height - 48))
            filt_b = (
                f"[0:v]{vf_b}[base];"
                f"[1:v]scale=40:40[cur];"
                f"[base][cur]overlay={oxb}:{oyb}:format=auto"
            )
            proc = subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(frame),
                    "-i",
                    str(cursor_png),
                    "-filter_complex",
                    filt_b,
                    "-t",
                    "0.35",
                    "-r",
                    str(fps),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(bridge),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                segment_clips.append(bridge)

        seg = work / f"seg_{i:02d}.mp4"
        vf = _zoom_crop_filter(width=width, height=height, cx=cx, cy=cy, zoom=zoom)
        ox = max(0, min(int(cx * width) - 4, width - 48))
        oy = max(0, min(int(cy * height) - 4, height - 48))
        filt = (
            f"[0:v]{vf}[base];"
            f"[1:v]scale=48:48[cur];"
            f"[base][cur]overlay={ox}:{oy}:format=auto"
        )
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-i",
                str(frame),
                "-i",
                str(cursor_png),
                "-filter_complex",
                filt,
                "-t",
                f"{dur:.3f}",
                "-r",
                str(fps),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(seg),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-2000:] or f"studio segment {i} failed")
        segment_clips.append(seg)
        prev_focus = (cx, cy)

    concat = work / "concat.txt"
    concat.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in segment_clips) + "\n",
        encoding="utf-8",
    )
    out = out_mp4 or (run_dir / "picture.mp4")
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        # re-encode if copy fails
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-2000:] or "studio concat failed")

    return {
        "ok": True,
        "out": str(out),
        "segments": len(segment_clips),
        "frames": len(frames),
        "look": "studio",
        "zoom": zoom,
    }


def ease_in_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)
