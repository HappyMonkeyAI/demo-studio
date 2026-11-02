from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def burn_title_card(
    picture_mp4: Path,
    out_mp4: Path,
    *,
    title: str = "demo-studio",
    subtitle: str = "",
    seconds: float = 2.5,
) -> Path:
    """Prepend a simple ffmpeg title card (Phase 4 light polish)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    card = out_mp4.parent / "_title_card.mp4"
    text = title.replace(":", "\\:").replace("'", "")
    sub = subtitle.replace(":", "\\:").replace("'", "")
    draw = f"drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2"
    if sub:
        draw += f",drawtext=text='{sub}':fontcolor=gray:fontsize=28:x=(w-text_w)/2:y=(h-text_h)/2+60"
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x0b0b0b:s=1920x1080:d={seconds}",
            "-vf",
            draw,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(card),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "title card failed")
    list_file = out_mp4.parent / "_concat.txt"
    list_file.write_text(
        f"file '{card.resolve().as_posix()}'\nfile '{picture_mp4.resolve().as_posix()}'\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(out_mp4),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "concat polish failed")
    return out_mp4
