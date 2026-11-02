# ADR 0001: demo-studio scope and layers

## Status

Accepted — 2026-11-02

## Context

We want automated YouTube/X demos of website apps (first: astro-cms). Pieces available: BrowserOS NEO, Pocket TTS / qwen-video-studio packaging, Recordly (GUI polish), AIQA (desktop MCP). Mixing them into one blob would stall shipping.

## Decision

Build **demo-studio** as a thin orchestrator on DevHost:

| Layer | Choice |
|---|---|
| Subject | Throwaway/demo sites only |
| Actuation | BrowserOS NEO |
| Capture | Browser/CDP screencast first; ffmpeg display later if needed |
| Narration | Pocket TTS HTTP sidecar |
| Package | ffmpeg + WebVTT + `review.html` (qwen-video-studio conventions) |

**Beat files** are the source of truth. Success = same beats → recognisably similar video on re-run.

## Consequences

- Reuse TTS/package ideas from qwen-video-studio; do not stretch that repo into screen recording.
- Recordly = visual taste only (AGPL GUI, not headless API).
- AIQA / sandbox VM deferred until a beat must leave the browser or needs hard isolation.
- Confidential pilot data never enters demos or committed outputs.
