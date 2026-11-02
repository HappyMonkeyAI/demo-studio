from __future__ import annotations

"""Compose beat stills + cursor timeline into animated zoom / pointer demo clip."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from demo_studio.cursor_timeline import CursorTimeline
from demo_studio.looks import _ffprobe_video


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
            "color=c=black@0.0:s=64x64:d=0.04,format=rgba",
            "-vf",
            (
                "drawbox=x=8:y=6:w=5:h=36:color=white@1.0:t=fill,"
                "drawbox=x=8:y=6:w=24:h=5:color=white@1.0:t=fill,"
                "drawbox=x=8:y=22:w=18:h=5:color=white@1.0:t=fill,"
                "drawbox=x=6:y=4:w=9:h=40:color=black@0.9:t=1"
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
                out.append(max(1.8, (end - start) / 1000.0))
            return out
    return [default_sec] * len(frames)


def _fit_pad(width: int, height: int) -> str:
    """Letterbox into canvas without stretching."""
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x0b0b0b,"
        f"setsar=1"
    )


def _animated_zoom_vf(
    *,
    width: int,
    height: int,
    cx: float,
    cy: float,
    zoom_start: float,
    zoom_end: float,
    frames: int,
    fps: float,
) -> str:
    """Ken Burns push-in toward (cx,cy) over `frames` output frames."""
    cx = min(max(cx, 0.08), 0.92)
    cy = min(max(cy, 0.08), 0.92)
    z0 = max(1.02, float(zoom_start))
    z1 = max(z0 + 0.08, float(zoom_end))
    n = max(int(frames) - 1, 1)
    # Linear push-in (reliable across ffmpeg builds); ease comes from xfade between beats.
    z_expr = f"{z0}+({z1}-{z0})*on/{n}"
    # Keep focus point near center as we zoom
    x_expr = f"(iw-iw/zoom)*{cx}"
    y_expr = f"(ih-ih/zoom)*{cy}"
    fit = _fit_pad(width, height)
    # Upscale canvas so zoompan has headroom without resampling stretch artifacts
    return (
        f"{fit},"
        f"scale=iw*2:ih*2,"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}'"
        f":d=1:s={width}x{height}:fps={fps}"
    )


def _render_segment(
    ffmpeg: str,
    *,
    frame: Path,
    cursor_png: Path,
    out: Path,
    width: int,
    height: int,
    cx: float,
    cy: float,
    dur: float,
    fps: int,
    zoom_start: float,
    zoom_end: float,
) -> None:
    total_frames = max(int(dur * fps), 2)
    vf = _animated_zoom_vf(
        width=width,
        height=height,
        cx=cx,
        cy=cy,
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        frames=total_frames,
        fps=float(fps),
    )
    # Static pointer at focus (zoompan carries the motion). Keep expressions simple —
    # overlay eval is picky about commas/escapes on Windows shells.
    ox = max(8, min(int(width * cx) - 8, width - 72))
    oy = max(8, min(int(height * cy) - 8, height - 72))
    filt = (
        f"[0:v]{vf}[base];"
        f"[1:v]scale=64:64[cur];"
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
            "-loop",
            "1",
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
            "-an",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2200:] or f"studio segment failed: {out.name}")


def _xfade_concat(
    ffmpeg: str,
    clips: list[Path],
    durations: list[float],
    out: Path,
    *,
    fade: float = 0.55,
) -> None:
    """Smooth dissolve between segments (no hard cuts)."""
    if len(clips) == 1:
        shutil.copy2(clips[0], out)
        return

    fade = max(0.25, min(float(fade), 0.9))
    # Ensure each clip is longer than fade
    durs = [max(d, fade + 0.35) for d in durations]

    inputs: list[str] = []
    for clip in clips:
        inputs += ["-i", str(clip)]

    parts: list[str] = []
    # Build chained xfade graph
    # offset_i = sum(durs[0:i]) - fade * i
    offset = durs[0] - fade
    parts.append(
        f"[0:v][1:v]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}[v1]"
    )
    last = "[v1]"
    for i in range(2, len(clips)):
        offset = sum(durs[:i]) - fade * i
        out_lab = f"[v{i}]"
        parts.append(
            f"{last}[{i}:v]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}{out_lab}"
        )
        last = out_lab

    filt = ";".join(parts)
    cmd = [ffmpeg, "-y", *inputs, "-filter_complex", filt, "-map", last, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2500:] or "studio xfade failed")


def compose_studio_mp4(
    run_dir: Path,
    out_mp4: Path | None = None,
    *,
    zoom: float = 1.55,
    fps: int = 30,
) -> dict[str, Any]:
    """Build animated zoom-to-focus + cursor overlay MP4 from frames/ + cursor.json."""
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
    # Prefer real frame pixels so we don't stretch a 1280x720 shot into 1280x900.
    meta0 = _ffprobe_video(frames[0])
    width = int(meta0["width"] or timeline.width or 1280)
    height = int(meta0["height"] or timeline.height or 720)
    # Even canvas dims for yuv420p / x264
    if width % 2:
        width -= 1
    if height % 2:
        height -= 1

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

    segment_clips: list[Path] = []
    seg_durs: list[float] = []
    prev_zoom = 1.08
    for i, frame in enumerate(frames):
        stem = frame.stem
        beat_id = stem.split("_", 1)[1] if "_" in stem else stem
        cx, cy = foci.get(beat_id, (0.5, 0.42))
        for ev in timeline.events:
            if ev.beat_id == beat_id and ev.type == "click":
                cx, cy = ev.x, ev.y
                break
        # Cookie-bar clicks near the bottom look bad as zoom targets — bias upward.
        if cy > 0.82:
            cy = 0.55
        dur = durations[i] if i < len(durations) else 4.0
        # Alternate / escalate zoom so motion stays visible across beats
        z_end = zoom if i % 2 == 0 else min(zoom + 0.12, 1.75)
        z_start = min(prev_zoom, z_end - 0.12)
        seg = work / f"seg_{i:02d}.mp4"
        _render_segment(
            ffmpeg,
            frame=frame,
            cursor_png=cursor_png,
            out=seg,
            width=width,
            height=height,
            cx=cx,
            cy=cy,
            dur=dur,
            fps=fps,
            zoom_start=z_start,
            zoom_end=z_end,
        )
        segment_clips.append(seg)
        seg_durs.append(dur)
        prev_zoom = 1.1  # next beat eases out a little then pushes in again

    out = out_mp4 or (run_dir / "picture.mp4")
    faded = work / "studio_xfade.mp4"
    _xfade_concat(ffmpeg, segment_clips, seg_durs, faded, fade=0.55)
    shutil.copy2(faded, out)

    return {
        "ok": True,
        "out": str(out),
        "segments": len(segment_clips),
        "frames": len(frames),
        "look": "studio",
        "zoom": zoom,
        "width": width,
        "height": height,
        "transition": "xfade-fade",
    }
