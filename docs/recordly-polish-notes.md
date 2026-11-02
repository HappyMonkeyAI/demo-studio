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
| `product-zoom` | ~8% center zoom across the **full VO length** in one mux pass |
| `studio` | Playwright `cursor.json` → zoom toward click foci + enlarged pointer on beat stills |

`product-zoom` applies during `mux_package` across VO length (never bake into a short looped picture).  
`studio` rebuilds `picture.mp4` from `frames/` + `cursor.json` first, then muxes clean. Capture also writes `cursor.openscreen.json` for optional OpenScreen CLI export experiments.

## Non-goals

- Embedding Recordly or any AGPL recorder GUI
- Generative fake UI
- Auto-publish

## Next slices

T26 crossfade · T27 click emphasis · T28 richer presets wired into `package` / `run-demo` (partially started via `--look`).
