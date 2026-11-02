from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _fontfile() -> str | None:
    env = os.environ.get("DEMO_STUDIO_FONT")
    if env and Path(env).is_file():
        return str(Path(env))
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


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

    work = out_mp4.parent
    text = title.replace(":", "\\:").replace("'", "").replace("%", "\\%")
    sub = subtitle.replace(":", "\\:").replace("'", "").replace("%", "\\%")

    font = _fontfile()
    font_opt = ""
    if font:
        local_font = work / "_title_font.ttf"
        if not local_font.is_file() or local_font.stat().st_size == 0:
            shutil.copy2(font, local_font)
        # Relative path + cwd=work avoids Windows drive-letter colons in filters.
        font_opt = ":fontfile=_title_font.ttf"

    draw = f"drawtext=text='{text}'{font_opt}:fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2"
    if sub:
        draw += (
            f",drawtext=text='{sub}'{font_opt}:fontcolor=gray:fontsize=28:"
            "x=(w-text_w)/2:y=(h-text_h)/2+60"
        )

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
            "_title_card.mp4",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(work),
    )
    if proc.returncode != 0:
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x0b0b0b:s=1920x1080:d={seconds}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "_title_card.mp4",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(work),
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-1500:] or "title card failed")

    (work / "_concat.txt").write_text(
        f"file '_title_card.mp4'\nfile '{picture_mp4.name}'\n",
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
            "_concat.txt",
            "-c",
            "copy",
            out_mp4.name,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(work),
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "concat polish failed")
    return out_mp4
