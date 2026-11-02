from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def frames_to_mp4(
    frames_dir: Path,
    out_mp4: Path,
    *,
    fps: int = 2,
    width: int = 1920,
    height: int = 1080,
    durations_sec: list[float] | None = None,
) -> dict:
    """Assemble ordered PNG/JPG frames into a silent MP4 (Phase 2 capture path).

    When durations_sec is provided (one per frame), each still is held for that
    many seconds so narration-aligned beats stay on screen. Otherwise each frame
    lasts 1/fps seconds.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    frames = sorted(
        [*frames_dir.glob("*.png"), *frames_dir.glob("*.jpg"), *frames_dir.glob("*.jpeg")]
    )
    if not frames:
        raise RuntimeError(f"no frames in {frames_dir}")

    list_file = frames_dir / "frames.txt"
    lines = []
    for i, frame in enumerate(frames):
        if durations_sec and i < len(durations_sec):
            dur = max(0.5, float(durations_sec[i]))
        else:
            dur = 1.0 / max(fps, 1)
        lines.append(f"file '{frame.resolve().as_posix()}'")
        lines.append(f"duration {dur:.6f}")
    lines.append(f"file '{frames[-1].resolve().as_posix()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        str(out_mp4),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or proc.stdout[-2000:] or "ffmpeg failed")
    return {
        "ok": True,
        "frames": len(frames),
        "out": str(out_mp4),
        "fps": fps,
        "durations_sec": durations_sec,
    }
