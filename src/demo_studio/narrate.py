from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

from demo_studio.tts_piper import PiperTTSAdapter
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


def load_lexicon(path: Path | None) -> dict[str, str]:
    """Read a JSON object of {"written": "spoken"} pronunciation fixes."""
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError(f"{path}: lexicon must be a JSON object of string -> string")
    return data


def apply_pronunciations(text: str, mapping: dict[str, str]) -> str:
    """Respell words/phrases for the TTS only (captions keep the original text).

    Matches whole words, case-insensitively, longest key first, so a phrase like
    "go-live" wins over a bare "live". Hyphens count as part of a word, so "live"
    does not match inside "go-live" or "live-stream".
    """
    if not mapping:
        return text
    keys = sorted((k for k in mapping if k.strip()), key=len, reverse=True)
    if not keys:
        return text
    lowered = {k.lower(): v for k, v in mapping.items()}
    pattern = re.compile(
        r"(?<![\w-])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w-])",
        re.IGNORECASE,
    )
    return pattern.sub(lambda m: lowered[m.group(1).lower()], text)


def _make_adapter(provider: str, voice: str | None = None):
    provider = (provider or "pocket").strip().lower()
    if provider == "piper":
        return PiperTTSAdapter(
            os.environ.get("PIPER_TTS_URL", "http://127.0.0.1:8010"),
            voice=voice or os.environ.get("PIPER_VOICE") or None,
        )
    if provider in {"pocket", "pocket-tts"}:
        return PocketTTSAdapter(
            os.environ.get("POCKET_TTS_URL", "http://127.0.0.1:8000"),
            voice=voice or os.environ.get("POCKET_TTS_VOICE") or None,
        )
    raise ValueError(f"unknown TTS provider: {provider}")


def narrate_beats(
    data: dict[str, Any],
    out_dir: Path,
    *,
    provider: str | None = None,
    pocket_tts_url: str | None = None,
    voice: str | None = None,
    lexicon: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Synthesize one WAV per beat; write captions cue list.

    Pronunciations come from the beat file's `pronunciations` plus `lexicon`
    (the lexicon wins on clashes) and only change what the TTS is sent.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    chosen = (provider or os.environ.get("DEMO_TTS_PROVIDER") or "pocket").strip().lower()
    if pocket_tts_url and chosen in {"pocket", "pocket-tts"}:
        os.environ.setdefault("POCKET_TTS_URL", pocket_tts_url)
    adapter = _make_adapter(chosen, voice)
    mapping = {**(data.get("pronunciations") or {}), **(lexicon or {})}
    health = adapter.check_health()
    if health.get("status") != "ready":
        raise RuntimeError(f"TTS unavailable ({chosen}): {health}")

    cues: list[dict[str, Any]] = []
    t_ms = 0
    for i, beat in enumerate(data.get("beats") or [], start=1):
        text = (beat.get("narration") or "").strip()
        wav_path = out_dir / f"{i:02d}_{beat.get('id')}.wav"
        spoken = apply_pronunciations(text, mapping)
        wav_path.write_bytes(adapter.synthesize_wav(spoken))
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
                **({"spoken": spoken} if spoken != text else {}),
            }
        )
        t_ms = end

    manifest = {
        "provider": health.get("provider") or chosen,
        "voice": voice or health.get("voice") or None,
        "cues": cues,
        "total_ms": t_ms,
    }
    (out_dir / "narration.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
