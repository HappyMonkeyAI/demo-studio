from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _chrome_bin() -> str | None:
    for name in (
        os.environ.get("CHROME_BIN"),
        "google-chrome-stable",
        "google-chrome",
        "chromium-browser",
        "chromium",
        "chrome",
    ):
        if not name:
            continue
        path = shutil.which(name) if os.sep not in name else (name if Path(name).exists() else None)
        if path:
            return path
    return None


def capture_beat_frames(
    data: dict[str, Any],
    base: str,
    frames_dir: Path,
    *,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Headless Chrome screenshots for navigate actions (Phase 2 on DevHost)."""
    chrome = _chrome_bin()
    if not chrome:
        raise RuntimeError("Chrome/Chromium not found (set CHROME_BIN)")
    frames_dir.mkdir(parents=True, exist_ok=True)
    base = base.rstrip("/")
    written: list[Path] = []
    n = 0
    for beat in data.get("beats") or []:
        paths: list[str] = []
        for action in beat.get("actions") or []:
            if action.get("type") != "navigate":
                continue
            path = action.get("path") or action.get("url") or "/"
            if str(path).startswith("http"):
                url = str(path)
            else:
                if not str(path).startswith("/"):
                    path = "/" + path
                url = base + path
            paths.append(url)
        if not paths:
            # still capture home-ish note beats as base URL once
            paths = [base + "/"]
        for url in paths:
            n += 1
            out = frames_dir / f"{n:02d}_{beat.get('id')}.png"
            cmd = [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size={width},{height}",
                f"--screenshot={out}",
                url,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=90)
            if not out.is_file():
                raise RuntimeError(
                    f"screenshot failed for {url}: exit={proc.returncode} err={proc.stderr[-500:]}"
                )
            written.append(out)
    return written
