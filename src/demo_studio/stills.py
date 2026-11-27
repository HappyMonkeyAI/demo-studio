from __future__ import annotations

"""Stills engine: build picture.mp4 from one image per beat, timed to narration.

Use this when the picture is not a live site but a set of images, e.g. slides
or frames pulled from a recording. Run *after* `narrate`, so each still is held
for exactly its beat's narration length (from narration/narration.json), then
`package` as usual.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

MOTIONS = ("push", "none")


def plan_stills(data: dict[str, Any], beats_path: Path, cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pair each beat's `still` image with its narration cue duration.

    Fails closed: every beat needs a `still` that exists, and the cues must be
    the same beats in the same order (i.e. narrate was run on this beat file).
    """
    beats = list(data.get("beats") or [])
    base = beats_path.resolve().parent
    problems: list[str] = []
    if len(beats) != len(cues):
        problems.append(f"{len(beats)} beats but {len(cues)} narration cues; re-run narrate on this beat file")
    plan: list[dict[str, Any]] = []
    for i, beat in enumerate(beats):
        bid = beat.get("id")
        still = beat.get("still")
        if not still:
            problems.append(f"beat {bid!r} has no 'still' image")
            continue
        image = (base / still).resolve()
        if not image.is_file():
            problems.append(f"beat {bid!r}: still not found: {image}")
            continue
        if i >= len(cues):
            continue
        cue = cues[i]
        if cue.get("beat") != bid:
            problems.append(f"cue {i + 1} is for beat {cue.get('beat')!r}, expected {bid!r}")
            continue
        duration_ms = int(cue["end_ms"]) - int(cue["start_ms"])
        if duration_ms <= 0:
            problems.append(f"beat {bid!r}: non-positive cue duration {duration_ms} ms")
            continue
        plan.append({"beat": bid, "image": image, "duration_s": duration_ms / 1000.0})
    if problems:
        raise ValueError("; ".join(problems))
    return plan


def _segment_filter(
    *,
    width: int,
    height: int,
    fps: int,
    frames: int,
    duration_s: float,
    motion: str,
    fade_s: float,
) -> str:
    fit = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x0b0b0b,setsar=1"
    )
    parts = [fit]
    if motion == "push":
        # Gentle ~5% centre push-in per still. Upscale first so zoompan's integer
        # crop positions don't make the image visibly judder.
        denom = max(frames - 1, 1)
        parts.append(f"scale={width * 2}:{height * 2}")
        parts.append(
            f"zoompan=z='1+0.05*on/{denom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s={width}x{height}:fps={fps}"
        )
    fade = min(max(fade_s, 0.0), duration_s / 3)
    if fade > 0:
        parts.append(f"fade=t=in:st=0:d={fade:.3f}")
        parts.append(f"fade=t=out:st={max(duration_s - fade, 0):.3f}:d={fade:.3f}")
    return ",".join(parts)


def compose_stills_mp4(
    data: dict[str, Any],
    beats_path: Path,
    narration_json: Path,
    out_mp4: Path,
    *,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    motion: str = "push",
    fade_s: float = 0.3,
) -> dict[str, Any]:
    """Render one segment per still and concatenate them into a silent picture.mp4."""
    if motion not in MOTIONS:
        raise ValueError(f"unknown motion {motion!r}; choose from {', '.join(MOTIONS)}")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    width -= width % 2
    height -= height % 2

    cues = json.loads(narration_json.read_text(encoding="utf-8"))["cues"]
    plan = plan_stills(data, beats_path, cues)

    work = out_mp4.parent / "stills"
    work.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []
    for i, item in enumerate(plan, start=1):
        frames = max(int(round(item["duration_s"] * fps)), 1)
        seg = work / f"{i:02d}_{item['beat']}.mp4"
        vf = _segment_filter(
            width=width,
            height=height,
            fps=fps,
            frames=frames,
            duration_s=item["duration_s"],
            motion=motion,
            fade_s=fade_s,
        )
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-framerate",
                str(fps),
                "-i",
                str(item["image"]),
                "-vf",
                vf,
                "-frames:v",
                str(frames),
                "-r",
                str(fps),
                "-an",
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
            raise RuntimeError(f"still {item['beat']!r} failed: {proc.stderr[-1500:]}")
        segments.append(seg)
        item["frames"] = frames

    list_file = work / "segments.txt"
    list_file.write_text(
        "".join(f"file '{seg.resolve().as_posix()}'\n" for seg in segments),
        encoding="utf-8",
    )
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_mp4)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1500:] or "stills concat failed")

    manifest = {
        "picture": str(out_mp4),
        "width": width,
        "height": height,
        "fps": fps,
        "motion": motion,
        "fade_s": fade_s,
        "stills": [
            {"beat": p["beat"], "image": str(p["image"]), "duration_s": p["duration_s"], "frames": p["frames"]}
            for p in plan
        ],
        "total_s": round(sum(p["frames"] for p in plan) / fps, 3),
    }
    (out_mp4.parent / "stills.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
