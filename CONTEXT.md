# demo-studio — Context

## Status

Phase 0 scaffold. Beat schema + validate/dry-run CLI. Capture, TTS mux, and NEO actuation land in later phases.

## Decision

Build a **thin orchestrator** for product demo videos on DevHost. Reuse Pocket TTS and review-package ideas from `qwen-video-studio`; do not expand that repo’s generative-advert thesis into screen recording.

## Layers

1. **Subject** — throwaway/demo site (never confidential client pilot data).
2. **Actuation** — BrowserOS NEO MCP (`run` scripts / helpers).
3. **Capture** — browser/CDP screencast or ffmpeg on a fixed display (browser-only first).
4. **Narration** — Pocket TTS (`POCKET_TTS_URL`, default `http://127.0.0.1:8000`).
5. **Package** — ffmpeg mux, WebVTT, `review.html`.

## Contract

A **beat file** is the source of truth. Each beat has narration, actions, asserts, and timing hints. Success = same beat file produces a recognisably similar video on a second run.

## Reuse map

| Source | Take |
|---|---|
| qwen-video-studio | Pocket TTS HTTP adapter shape, narration-duration lessons, review package |
| BrowserOS NEO | Actuator for the product under demo |
| Recordly | Visual taste only (zooms/frames) — not runtime |
| AIQA / UIQA | Later, only when a beat leaves the browser |

## Non-negotiables

- No client names, domains, or `client-data/` in demos or outputs committed to git.
- Fail the run on assert failure; never ship a wrong click.
- Secrets stay in env / local sidecars, never in beat files.

## Workflow

1. Author/edit `demos/<product>/demo.beats.json`.
2. `demo-studio validate` then `dry-run`.
3. When capture lands: `record` → `narrate` → `package`.
4. Human watches `outputs/<run>/review.html` before publishing.
