from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def _abs(base: str, path: str) -> str:
    if str(path).startswith("http"):
        return str(path)
    if not str(path).startswith("/"):
        path = "/" + path
    return base.rstrip("/") + path


def _resolve_value(action: dict[str, Any]) -> str:
    if action.get("env"):
        val = os.environ.get(str(action["env"]), "")
        if not val:
            raise RuntimeError(f"missing env {action['env']} (load .local/*.env)")
        return val
    return str(action.get("text") or action.get("value") or "")


def _dismiss_overlays(page: Any) -> None:
    """Best-effort dismiss cookie/consent banners that cover the demo subject."""
    for label in (
        "Accept essential cookies",
        "Got it",
        "Reject non-essential",
        "Accept all",
        "Accept",
        "Close",
    ):
        try:
            page.get_by_role("button", name=label, exact=False).first.click(timeout=800)
            page.wait_for_timeout(200)
            return
        except Exception:
            continue


def capture_beat_frames_playwright(
    data: dict[str, Any],
    base: str,
    frames_dir: Path,
    *,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Run beat actions in one browser session and screenshot each beat.

    Unlike the old path, note-only beats keep the current page (no homepage
    fallback). Use navigate/fill/click_text so each beat matches its narration.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright not installed; pip install playwright && playwright install chromium"
        ) from exc

    frames_dir.mkdir(parents=True, exist_ok=True)
    base = base.rstrip("/")
    written: list[Path] = []
    n = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(base + "/", wait_until="domcontentloaded", timeout=60_000)
        _dismiss_overlays(page)

        for beat in data.get("beats") or []:
            actions = list(beat.get("actions") or [])
            took_shot = False
            for action in actions:
                atype = action.get("type")
                if atype == "note":
                    continue
                if atype == "navigate":
                    page.goto(
                        _abs(base, action.get("path") or action.get("url") or "/"),
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )
                    page.wait_for_timeout(400)
                    _dismiss_overlays(page)
                elif atype == "wait_ms":
                    page.wait_for_timeout(int(action.get("ms") or 0))
                elif atype == "wait_text":
                    needle = str(action.get("text") or "")
                    loc = page.get_by_text(needle, exact=False)
                    found = False
                    for _ in range(40):  # ~20s
                        for i in range(loc.count()):
                            try:
                                if loc.nth(i).is_visible():
                                    found = True
                                    break
                            except Exception:
                                continue
                        if found:
                            break
                        page.wait_for_timeout(500)
                    if not found:
                        loc.first.wait_for(timeout=5_000)
                elif atype == "click_text":
                    label = str(action.get("text") or "")
                    exact = bool(action.get("exact"))
                    optional = bool(action.get("optional")) or label in {
                        "Get Started",
                        "Got it",
                        "Accept essential cookies",
                        "Reject non-essential",
                        "Accept all",
                    }
                    # Prefer a button/link role so we don't hit headings or duplicate text.
                    try:
                        page.get_by_role("button", name=label, exact=exact).first.click(timeout=8_000)
                    except Exception:
                        try:
                            page.get_by_role("link", name=label, exact=exact).first.click(timeout=8_000)
                        except Exception:
                            try:
                                page.get_by_text(label, exact=exact).first.click(timeout=4_000 if optional else 15_000)
                            except Exception:
                                if not optional:
                                    raise
                    page.wait_for_timeout(500)
                elif atype == "fill":
                    selector = action.get("selector")
                    value = _resolve_value(action)
                    if selector:
                        page.locator(str(selector)).first.fill(value, timeout=15_000)
                    else:
                        label = action.get("label") or action.get("placeholder")
                        if not label:
                            raise RuntimeError("fill requires selector or label")
                        page.get_by_label(str(label), exact=False).first.fill(value, timeout=15_000)
                    page.wait_for_timeout(200)
                elif atype == "wait_url_not":
                    needle = str(action.get("value") or action.get("text") or "")
                    page.wait_for_function(
                        "needle => !location.href.includes(needle)",
                        arg=needle,
                        timeout=int(action.get("ms") or 20_000),
                    )
                elif atype == "press":
                    page.keyboard.press(str(action.get("text") or "Enter"))
                elif atype == "scroll":
                    delta = int(action.get("px") or action.get("ms") or 600)
                    page.mouse.wheel(0, delta)
                    page.wait_for_timeout(400)
                elif atype == "screenshot":
                    n += 1
                    out = frames_dir / f"{n:02d}_{beat.get('id')}.png"
                    page.screenshot(path=str(out), full_page=False)
                    written.append(out)
                    took_shot = True
                else:
                    # unknown action: ignore for capture
                    continue

            if not took_shot:
                # One frame per beat at the end of its actions (current page).
                n += 1
                out = frames_dir / f"{n:02d}_{beat.get('id')}.png"
                page.wait_for_timeout(int(beat.get("pause_ms") or 300))
                page.screenshot(path=str(out), full_page=False)
                written.append(out)

            # Optional assert: page_has_text / url_contains
            for assertion in beat.get("assert") or []:
                if assertion.get("type") == "url_contains":
                    needle = str(assertion.get("value") or "")
                    if needle and needle not in page.url:
                        raise RuntimeError(f"url_contains failed in {beat.get('id')}: {page.url}")
                elif assertion.get("type") == "page_has_text":
                    needle = str(assertion.get("value") or "")
                    body = page.inner_text("body")
                    if needle and needle.lower() not in body.lower():
                        raise RuntimeError(f"page_has_text failed in {beat.get('id')}: {needle!r}")

        browser.close()

    if not written:
        raise RuntimeError("no frames captured")
    return written
