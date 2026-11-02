from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from demo_studio.cursor_timeline import CursorEvent, CursorTimeline, write_openscreen_sidecar


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


def _norm_box(box: dict[str, float], width: int, height: int) -> tuple[float, float, float, float]:
    cx = (box["x"] + box["width"] / 2) / max(width, 1)
    cy = (box["y"] + box["height"] / 2) / max(height, 1)
    return (
        min(max(cx, 0.0), 1.0),
        min(max(cy, 0.0), 1.0),
        box["x"] + box["width"] / 2,
        box["y"] + box["height"] / 2,
    )


def _click_locator(
    page: Any,
    locator: Any,
    *,
    timeline: CursorTimeline,
    t0: float,
    beat_id: str,
    label: str,
    width: int,
    height: int,
    cursor: str = "pointer",
) -> None:
    box = locator.bounding_box(timeout=8_000)
    if not box:
        locator.click(timeout=8_000)
        return
    nx, ny, px, py = _norm_box(box, width, height)
    page.mouse.move(px, py, steps=18)
    timeline.add(
        CursorEvent(
            t_ms=int((time.monotonic() - t0) * 1000),
            type="move",
            x=nx,
            y=ny,
            beat_id=beat_id,
            label=label,
            cursor=cursor,
        )
    )
    page.wait_for_timeout(80)
    locator.click(timeout=8_000)
    timeline.add(
        CursorEvent(
            t_ms=int((time.monotonic() - t0) * 1000),
            type="click",
            x=nx,
            y=ny,
            beat_id=beat_id,
            label=label,
            cursor=cursor,
        )
    )


def capture_beat_frames_playwright(
    data: dict[str, Any],
    base: str,
    frames_dir: Path,
    *,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Run beat actions in one browser session and screenshot each beat.

    Also writes ``cursor.json`` (+ OpenScreen-shaped ``cursor.openscreen.json``)
    beside the frames directory for studio polish.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright not installed; pip install playwright && playwright install chromium"
        ) from exc

    frames_dir.mkdir(parents=True, exist_ok=True)
    run_dir = frames_dir.parent
    base = base.rstrip("/")
    written: list[Path] = []
    n = 0
    timeline = CursorTimeline(width=width, height=height)
    t0 = time.monotonic()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(base + "/", wait_until="domcontentloaded", timeout=60_000)
        _dismiss_overlays(page)

        for beat in data.get("beats") or []:
            beat_id = str(beat.get("id") or f"beat{n}")
            actions = list(beat.get("actions") or [])
            took_shot = False
            timeline.add(
                CursorEvent(
                    t_ms=int((time.monotonic() - t0) * 1000),
                    type="beat",
                    x=0.5,
                    y=0.5,
                    beat_id=beat_id,
                    label=beat_id,
                )
            )
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
                    clicked = False
                    for role in ("button", "link"):
                        try:
                            loc = page.get_by_role(role, name=label, exact=exact).first
                            _click_locator(
                                page,
                                loc,
                                timeline=timeline,
                                t0=t0,
                                beat_id=beat_id,
                                label=label,
                                width=width,
                                height=height,
                            )
                            clicked = True
                            break
                        except Exception:
                            continue
                    if not clicked:
                        try:
                            loc = page.get_by_text(label, exact=exact).first
                            _click_locator(
                                page,
                                loc,
                                timeline=timeline,
                                t0=t0,
                                beat_id=beat_id,
                                label=label,
                                width=width,
                                height=height,
                            )
                            clicked = True
                        except Exception:
                            if not optional:
                                raise
                    page.wait_for_timeout(500)
                elif atype == "fill":
                    selector = action.get("selector")
                    value = _resolve_value(action)
                    if selector:
                        loc = page.locator(str(selector)).first
                    else:
                        label = action.get("label") or action.get("placeholder")
                        if not label:
                            raise RuntimeError("fill requires selector or label")
                        loc = page.get_by_label(str(label), exact=False).first
                    box = loc.bounding_box(timeout=15_000)
                    if box:
                        nx, ny, px, py = _norm_box(box, width, height)
                        page.mouse.move(px, py, steps=14)
                        timeline.add(
                            CursorEvent(
                                t_ms=int((time.monotonic() - t0) * 1000),
                                type="move",
                                x=nx,
                                y=ny,
                                beat_id=beat_id,
                                cursor="text",
                            )
                        )
                    loc.click(timeout=15_000)
                    if box:
                        timeline.add(
                            CursorEvent(
                                t_ms=int((time.monotonic() - t0) * 1000),
                                type="fill",
                                x=nx,
                                y=ny,
                                beat_id=beat_id,
                                cursor="text",
                                label=str(action.get("label") or action.get("selector") or ""),
                            )
                        )
                    loc.fill(value, timeout=15_000)
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
                    timeline.add(
                        CursorEvent(
                            t_ms=int((time.monotonic() - t0) * 1000),
                            type="scroll",
                            x=0.5,
                            y=0.5,
                            beat_id=beat_id,
                        )
                    )
                    page.wait_for_timeout(400)
                elif atype == "screenshot":
                    n += 1
                    out = frames_dir / f"{n:02d}_{beat.get('id')}.png"
                    page.screenshot(path=str(out), full_page=False)
                    written.append(out)
                    took_shot = True
                else:
                    continue

            if not took_shot:
                n += 1
                out = frames_dir / f"{n:02d}_{beat.get('id')}.png"
                page.wait_for_timeout(int(beat.get("pause_ms") or 300))
                page.screenshot(path=str(out), full_page=False)
                written.append(out)

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

    timeline.write(run_dir / "cursor.json")
    write_openscreen_sidecar(timeline, run_dir / "cursor.openscreen.json")

    if not written:
        raise RuntimeError("no frames captured")
    return written
