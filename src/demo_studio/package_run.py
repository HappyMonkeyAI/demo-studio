from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from demo_studio.looks import _ffprobe_duration, mux_video_filter_for_look


def _ms_to_vtt(ms: int) -> str:
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def write_vtt(cues: list[dict[str, Any]], path: Path) -> None:
    lines = ["WEBVTT", ""]
    for i, cue in enumerate(cues, start=1):
        lines.append(str(i))
        lines.append(f"{_ms_to_vtt(cue['start_ms'])} --> {_ms_to_vtt(cue['end_ms'])}")
        lines.append(cue.get("text") or "")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def concat_wavs(wav_paths: list[Path], out_wav: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    list_file = out_wav.parent / "wavs.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in wav_paths) + "\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_wav)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        # re-encode if copy fails (mismatched formats)
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
                "-c:a",
                "pcm_s16le",
                str(out_wav),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-1500:] or "wav concat failed")


def mux_package(
    run_dir: Path,
    *,
    picture_mp4: Path | None = None,
    narration_dir: Path | None = None,
    look: str = "clean",
) -> dict[str, Any]:
    """Build demo.mp4 + captions.vtt + review.html under run_dir."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")

    picture = picture_mp4 or (run_dir / "picture.mp4")
    narr_dir = narration_dir or (run_dir / "narration")
    narr_json = json.loads((narr_dir / "narration.json").read_text(encoding="utf-8"))
    cues = narr_json["cues"]
    write_vtt(cues, run_dir / "captions.vtt")

    wavs = [narr_dir / c["file"] for c in cues]
    voice = run_dir / "voice.wav"
    concat_wavs(wavs, voice)
    audio_dur = _ffprobe_duration(voice)

    out_mp4 = run_dir / "demo.mp4"
    look_name = (look or "clean").strip().lower()
    if picture.is_file():
        # Loop/pad video to audio length. Motion looks must span the full VO
        # in one pass — never bake zoom into a short picture then loop it.
        vf = mux_video_filter_for_look(look_name, picture=picture, duration_s=audio_dur)
        cmd = [
            ffmpeg,
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(picture),
            "-i",
            str(voice),
        ]
        if vf:
            cmd += ["-vf", vf]
        cmd += [
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_mp4),
        ]
    else:
        # Audio-only visual: color source sized 1920x1080
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x111111:s=1920x1080:r=30",
            "-i",
            str(voice),
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_mp4),
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or "mux failed")

    review = run_dir / "review.html"
    review.write_text(
        """<!doctype html>
<html lang="en"><meta charset="utf-8"/>
<title>demo-studio review</title>
<body style="font-family:system-ui;max-width:960px;margin:2rem auto;background:#111;color:#eee">
<h1>demo-studio review</h1>
<video controls src="demo.mp4" style="width:100%;background:#000"></video>
<p><a href="captions.vtt">captions.vtt</a> · <a href="run-log.json">run-log.json</a></p>
</body></html>
""",
        encoding="utf-8",
    )
    manifest = {
        "demo_mp4": str(out_mp4),
        "captions": str(run_dir / "captions.vtt"),
        "review_html": str(review),
        "total_ms": narr_json.get("total_ms"),
        "has_picture": picture.is_file(),
        "look": look_name,
        "audio_duration_s": audio_dur,
    }
    (run_dir / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
