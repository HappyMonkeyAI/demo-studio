# Recordly-inspired polish — research notes (T24)

**Decision:** Copy the *feel* (gentle motion, focus, editorial cards) in our MIT ffmpeg/frame pipeline. Do **not** vendor, spawn, or link Recordly’s AGPL GUI as runtime ([ADR 0001](../adr/0001-demo-studio-scope.md), SPEC S7).

## What “Recordly-style” means for us

| Taste | Our primitive |
|---|---|
| Slow push-in on a still UI | `product-zoom` look — ffmpeg `zoompan` over `picture.mp4` |
| Soft cut energy | Later: short crossfade between beat segments (needs per-beat clip boundaries) |
| “Someone clicked here” | Later: cursor/ripple overlay from action metadata + click coords |
| Opening slap | Existing `burn_title_card` (keep; strengthen in T28) |

## Presets (v1)

| Name | Behaviour |
|---|---|
| `clean` | No motion (default) |
| `product-zoom` | ~8% center zoom across the silent picture track before mux |

Apply **before** title-card prepend so the card stays static.

## Non-goals

- Embedding Recordly or any AGPL recorder GUI
- Generative fake UI
- Auto-publish

## Next slices

T26 crossfade · T27 click emphasis · T28 richer presets wired into `package` / `run-demo` (partially started via `--look`).
