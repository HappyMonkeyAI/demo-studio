from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


class PiperTTSAdapter:
    """HTTP client for Text Echo–compatible Piper (`GET /health`, `POST /speak`)."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8010",
        timeout: float = 60.0,
        voice: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.voice = voice

    def check_health(self) -> dict[str, str]:
        try:
            with urlopen(Request(f"{self.base_url}/health"), timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                status = payload.get("status")
                if response.status == 200 and status in {"ok", "healthy", "ready"}:
                    return {
                        "status": "ready",
                        "provider": "piper",
                        "base_url": self.base_url,
                        "voice": str(payload.get("voice") or self.voice or ""),
                    }
        except (OSError, URLError, json.JSONDecodeError, ValueError):
            pass
        return {"status": "unavailable", "provider": "piper", "base_url": self.base_url}

    def synthesize_wav(self, text: str, voice: str | None = None) -> bytes:
        if not text.strip():
            raise ValueError("text must not be blank")
        body: dict[str, str] = {"text": text}
        chosen = voice or self.voice
        if chosen:
            body["voice"] = chosen
        request = Request(
            f"{self.base_url}/speak",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            audio = response.read()
        if not audio.startswith(b"RIFF") or b"WAVE" not in audio[:16]:
            raise RuntimeError("Piper TTS returned a non-WAV response")
        return audio
