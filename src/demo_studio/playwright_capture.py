from __future__ import annotations

from pathlib import Path
from typing import Any


def capture_beat_frames_playwright(
    data: dict[str, Any],
    base: str,
    frames_dir: Path,
    *,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Screenshot navigate targets with Playwright (preferred when Chrome headless hangs)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("playwright not installed; pip install playwright && playwright install chromium") from exc

    frames_dir.mkdir(parents=True, exist_ok=True)
    base = base.rstrip("/")
    written: list[Path] = []
    n = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        for beat in data.get("beats") or []:
            urls: list[str] = []
            for action in beat.get("actions") or []:
                if action.get("type") != "navigate":
                    continue
                path = action.get("path") or action.get("url") or "/"
                if str(path).startswith("http"):
                    urls.append(str(path))
                else:
                    if not str(path).startswith("/"):
                        path = "/" + path
                    urls.append(base + path)
            if not urls:
                urls = [base + "/"]
            for url in urls:
                n += 1
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(500)
                out = frames_dir / f"{n:02d}_{beat.get('id')}.png"
                page.screenshot(path=str(out), full_page=False)
                written.append(out)
        browser.close()
    return written
