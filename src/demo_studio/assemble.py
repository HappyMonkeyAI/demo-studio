from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from demo_studio.beats import resolve_clip_path, visual_kind
from demo_studio.capture import frames_to_mp4
from demo_studio.clips import clip_segment, probe_streams


def _ensure_silent_audio(ffmpeg: str, seg: Path, dur_s: float) -> None:
    """Give a still segment (frames_to_mp4 output) a silent audio track.

    Plan deviation (Task 4): the brief's concat_segments maps [i:a] on every
    segment, but frames_to_mp4 encodes video-only, so the verbatim code fails
    its own integration test on ffmpeg 9 ("Stream specifier ':a' ... matches
    no streams"). Clip segments already carry silent AAC from clips.py, so only
    still segments need this. Explicit -map 0:v:0 -map 1:a:0 is mandatory with
    an anullsrc input (host quirk note; a mono source false-passes without it),
    and -t pins the track to the cue duration because -shortest is imprecise
    with -c:v copy.
    """
    if probe_streams(seg).get("audio") is not None:
        return
    tmp = seg.with_name(seg.stem + ".mux.mp4")
    cmd = [
        ffmpeg, "-y", "-v", "error",
        "-i", str(seg),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-ar", "48000",
        "-t", f"{dur_s:.3f}", "-shortest", str(tmp),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"silent audio attach failed for {seg}: {proc.stderr[-800:]}")
    tmp.replace(seg)


def concat_segments(ffmpeg: str, segs: list[Path], out: Path) -> None:
    cmd = [ffmpeg, "-y", "-v", "error"]
    for s in segs:
        cmd += ["-i", str(s)]
    labels = "".join(f"[{i}:v][{i}:a]" for i in range(len(segs)))
    cmd += [
        "-filter_complex", f"{labels}concat=n={len(segs)}:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "48000", str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"picture concat failed: {proc.stderr[-800:]}")


def assemble_picture(
    data: dict[str, Any],
    cues: list[dict[str, Any]],
    frames_dir: Path,
    job_dir: Path,
    *,
    pack_dir: Path,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Build picture.mp4 as per-beat segments aligned to narration cues."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    beats = data.get("beats") or []
    if len(cues) != len(beats):
        raise RuntimeError(f"cue count {len(cues)} != beat count {len(beats)}")
    segs_dir = job_dir / "segments"
    segs_dir.mkdir(parents=True, exist_ok=True)
    segs: list[Path] = []
    total_s = 0.0
    for i, (beat, cue) in enumerate(zip(beats, cues)):
        bid = str(beat.get("id") or f"beat{i}")
        dur_s = max(0.5, float(cue.get("duration_ms") or 500) / 1000.0)
        seg = segs_dir / f"{i:02d}_{bid}.mp4"
        if visual_kind(beat) == "clip":
            src = resolve_clip_path(beat, pack_dir)
            if src is None or not src.is_file():
                raise RuntimeError(f"clip file missing for beat {bid}: {(beat.get('visual') or {}).get('file')}")
            v = beat.get("visual") or {}
            clip_segment(src, seg,
                         in_sec=float(v.get("in_sec") or 0.0),
                         out_sec=v.get("out_sec"),
                         width=width, height=height, target_dur_s=dur_s)
        else:
            beat_frames = sorted(frames_dir.glob(f"*_{bid}.png")) + sorted(frames_dir.glob(f"*_{bid}.jpg"))
            if not beat_frames:
                raise RuntimeError(f"no frames for beat {bid}")
            per = dur_s / len(beat_frames)
            frames_to_mp4(frames_dir, seg, width=width, height=height,
                          durations_sec=[per] * len(beat_frames), frames=beat_frames)
            _ensure_silent_audio(ffmpeg, seg, dur_s)
        segs.append(seg)
        total_s += dur_s
    picture = job_dir / "picture.mp4"
    concat_segments(ffmpeg, segs, picture)
    # mux_package must stay untouched, and its unmapped 2-input selection
    # prefers the lowest-index audio: an audio-bearing picture would beat
    # voice.wav (silent looped track) and -stream_loop -1 + -shortest would
    # never terminate (verified via ffmpeg "Stream mapping" on host, 2026-11-26).
    # Per-segment audio only satisfies the concat v=1:a=1 contract; ship the
    # picture video-only, exactly like the capture-path picture, so mux picks
    # voice.wav as it always has.
    stripped = job_dir / "picture.noaudio.mp4"
    cmd = [ffmpeg, "-y", "-v", "error", "-i", str(picture), "-an", "-c:v", "copy", str(stripped)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"picture audio strip failed: {proc.stderr[-800:]}")
    stripped.replace(picture)
    return {"segments": len(segs), "picture": str(picture), "total_s": total_s}
