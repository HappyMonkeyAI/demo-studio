from __future__ import annotations

import json
import os
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

from demo_studio.tts_pocket import PocketTTSAdapter


def _wav_duration_ms(path: Path) -> int:
    """Prefer ffprobe; wave module mis-reads some Pocket TTS headers."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            try:
                return max(1, int(float(proc.stdout.strip()) * 1000))
            except ValueError:
                pass
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate() or 1
        if rate < 1000:
            # Guard against bogus headers that inflate duration into hours.
            raise RuntimeError(f"suspicious WAV rate {rate} for {path}")
        return int(frames * 1000 / rate)


def narrate_beats(
    data: dict[str, Any],
    out_dir: Path,
    *,
    pocket_tts_url: str | None = None,
) -> dict[str, Any]:
    """Synthesize one WAV per beat; write captions cue list."""
    out_dir.mkdir(parents=True, exist_ok=True)
    adapter = PocketTTSAdapter(
        pocket_tts_url or os.environ.get("POCKET_TTS_URL", "http://127.0.0.1:8000")
    )
    health = adapter.check_health()
    if health.get("status") != "ready":
        raise RuntimeError(f"Pocket TTS unavailable: {health}")

    cues: list[dict[str, Any]] = []
    t_ms = 0
    for i, beat in enumerate(data.get("beats") or [], start=1):
        text = (beat.get("narration") or "").strip()
        wav_path = out_dir / f"{i:02d}_{beat.get('id')}.wav"
        wav_path.write_bytes(adapter.synthesize_wav(text))
        dur = _wav_duration_ms(wav_path)
        min_ms = int(beat.get("min_narration_ms") or 0)
        pad_ms = max(0, min_ms - dur)
        end = t_ms + dur + pad_ms
        cues.append(
            {
                "beat": beat.get("id"),
                "file": wav_path.name,
                "start_ms": t_ms,
                "end_ms": end,
                "duration_ms": dur,
                "pad_ms": pad_ms,
                "text": text,
            }
        )
        t_ms = end

    manifest = {"cues": cues, "total_ms": t_ms}
    (out_dir / "narration.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
