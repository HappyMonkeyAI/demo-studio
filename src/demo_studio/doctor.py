from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from demo_studio.tts_piper import PiperTTSAdapter
from demo_studio.tts_pocket import PocketTTSAdapter


def _ffmpeg_ok() -> dict[str, Any]:
    path = shutil.which("ffmpeg")
    if not path:
        return {"status": "missing", "detail": "ffmpeg not on PATH"}
    try:
        proc = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        first = (proc.stdout or proc.stderr or "").splitlines()[:1]
        return {
            "status": "ready" if proc.returncode == 0 else "error",
            "path": path,
            "detail": first[0] if first else f"exit {proc.returncode}",
        }
    except OSError as exc:
        return {"status": "error", "path": path, "detail": str(exc)}


def run_doctor(*, pocket_tts_url: str | None = None) -> dict[str, Any]:
    tts_url = pocket_tts_url or os.environ.get("POCKET_TTS_URL", "http://127.0.0.1:8000")
    tts = PocketTTSAdapter(tts_url).check_health()
    piper = PiperTTSAdapter(os.environ.get("PIPER_TTS_URL", "http://127.0.0.1:8010")).check_health()
    ffmpeg = _ffmpeg_ok()
    neo_hint = os.environ.get("BROWSEROS_NEO_MCP_URL") or os.environ.get("NEO_MCP_URL") or "(unset)"
    ok = tts.get("status") == "ready" and ffmpeg.get("status") == "ready"
    return {
        "ok": ok,
        "ffmpeg": ffmpeg,
        "pocket_tts": tts,
        "piper_tts": piper,
        "neo_mcp_url_env": neo_hint,
        "notes": [
            "Doctor requires ffmpeg + Pocket TTS (default path).",
            "Piper is optional via DEMO_TTS_PROVIDER=piper and PIPER_TTS_URL (default :8010).",
            "NEO actuation URL env is informational.",
        ],
    }
