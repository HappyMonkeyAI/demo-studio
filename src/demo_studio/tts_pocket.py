from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PocketTTSAdapter:
    """HTTP client for the local Pocket TTS sidecar (qwen-video-studio shape)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> dict[str, str]:
        try:
            with urlopen(Request(f"{self.base_url}/health"), timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if response.status == 200 and payload.get("status") in {"ok", "healthy", "ready"}:
                    return {"status": "ready", "provider": "pocket-tts", "base_url": self.base_url}
        except (OSError, URLError, json.JSONDecodeError, ValueError):
            pass
        return {"status": "unavailable", "provider": "pocket-tts", "base_url": self.base_url}

    def synthesize_wav(self, text: str, voice_url: str | None = None) -> bytes:
        if not text.strip():
            raise ValueError("text must not be blank")
        fields = {"text": text}
        if voice_url:
            fields["voice_url"] = voice_url
        request = Request(
            f"{self.base_url}/tts",
            data=urlencode(fields).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            audio = response.read()
        if not audio.startswith(b"RIFF") or b"WAVE" not in audio[:16]:
            raise RuntimeError("Pocket TTS returned a non-WAV response")
        return audio
