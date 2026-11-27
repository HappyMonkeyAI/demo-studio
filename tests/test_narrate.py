from __future__ import annotations

import io
import shutil
import wave
from pathlib import Path

import pytest

from demo_studio import narrate


class _FakeAdapter:
    def check_health(self) -> dict[str, str]:
        return {"status": "ready", "provider": "fake"}

    def synthesize_wav(self, text: str) -> bytes:
        buffer = io.BytesIO()
        rate = 8000
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            frames = bytearray(rate * 2)
            for i in range(rate // 10):
                frames[i * 2 : i * 2 + 2] = (1000).to_bytes(2, "little", signed=True)
            wav.writeframes(frames)
        return buffer.getvalue()


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_gap_ms_appends_real_silence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrate, "_make_adapter", lambda _provider, voice=None: _FakeAdapter())
    data = {
        "version": 1,
        "product": "p",
        "beats": [{"id": "a", "narration": "hi", "gap_ms": 650}],
    }

    manifest = narrate.narrate_beats(data, tmp_path, provider="fake")
    cue = manifest["cues"][0]
    wav_path = tmp_path / cue["file"]

    with wave.open(str(wav_path), "rb") as wav:
        rate = wav.getframerate()
        frames = wav.getnframes()
        duration_s = frames / rate
        wav.setpos(max(0, frames - int(rate * 0.6)))
        trailing = wav.readframes(int(rate * 0.6))

    assert 1.60 <= duration_s <= 1.75
    assert cue["duration_ms"] == pytest.approx(duration_s * 1000, abs=5)
    assert not any(trailing)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_min_narration_ms_appends_silence_after_gap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrate, "_make_adapter", lambda _provider, voice=None: _FakeAdapter())
    data = {
        "version": 1,
        "product": "p",
        "beats": [{"id": "a", "narration": "hi", "gap_ms": 200, "min_narration_ms": 1800}],
    }

    manifest = narrate.narrate_beats(data, tmp_path, provider="fake")
    cue = manifest["cues"][0]
    with wave.open(str(tmp_path / cue["file"]), "rb") as wav:
        duration_s = wav.getnframes() / wav.getframerate()

    assert 1.80 <= duration_s <= 1.90
    assert cue["duration_ms"] == pytest.approx(1800, abs=5)
    assert cue["pad_ms"] == pytest.approx(600, abs=5)
    assert cue["end_ms"] - cue["start_ms"] == cue["duration_ms"]
