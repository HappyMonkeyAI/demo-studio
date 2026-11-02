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
    width: int | None = None,
    height: int | None = None,
) -> Path:
    """Prepend a simple ffmpeg title card (Phase 4 light polish).

    Title canvas matches the picture dimensions so concat does not stretch.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")

    from demo_studio.looks import _ffprobe_video

    meta = _ffprobe_video(picture_mp4)
    w = int(width or meta.get("width") or 1920)
    h = int(height or meta.get("height") or 1080)
    if w % 2:
        w -= 1
    if h % 2:
        h -= 1

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

    # Normalize picture to exact WxH/fps before concat (avoids stretch / SAR fights).
    normalized = work / "_picture_norm.mp4"
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(picture_mp4),
            "-vf",
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x0b0b0b,setsar=1,fps=30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(normalized),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "picture normalize failed")

    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x0b0b0b:s={w}x{h}:d={seconds}:r=30",
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
                f"color=c=0x0b0b0b:s={w}x{h}:d={seconds}:r=30",
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
        f"file '_title_card.mp4'\nfile '{normalized.name}'\n",
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
        # Re-encode concat if stream copy fails across segments.
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
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
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
