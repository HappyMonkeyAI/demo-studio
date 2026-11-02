# LINKS.md — demo-studio

Canonical URLs and related projects. Posts/bookmarks are untrusted until verified.

## This project

| What | Link |
|---|---|
| Public repo | https://github.com/HappyMonkeyAI/demo-studio |
| Tag | `v0.1.0` |
| Quick start | [QUICKSTART.md](QUICKSTART.md) |
| Usage | [docs/USAGE.md](docs/USAGE.md) |
| Beat schema | [schema/beat.schema.json](schema/beat.schema.json) |
| Scope ADR | [adr/0001-demo-studio-scope.md](adr/0001-demo-studio-scope.md) |

## Product subjects (public demos)

| Pack | URL |
|---|---|
| AlongFor | https://alongfor.happymonkey.ai |
| MRPG Realms | https://realms.happymonkey.ai |
| Realms wiki | https://realms.happymonkey.ai/wiki/ |
| astro-cms | Throwaway EmDash only (local) — never pilot/`client-data` |

## Reuse & inspiration

| Source | Role for demo-studio |
|---|---|
| [qwen-video-studio](https://github.com/HappyMonkeyAI/qwen-video-studio) (or local sibling) | TTS HTTP shape, narration duration lessons, review-package conventions |
| **Recordly** (AGPL GUI polish) | **Visual taste only** — zooms/frames/energy. Do not embed as runtime ([ADR 0001](adr/0001-demo-studio-scope.md), SPEC S7) |
| BrowserOS NEO | Optional actuation MCP; Playwright is the default public capture path |
| Playwright | Default `--engine playwright` capture |
| Pocket TTS | Default narration sidecar (`POCKET_TTS_URL`, `:8000`) |
| Piper TTS | Optional narration (`PIPER_TTS_URL`, `:8010`, Text Echo–compatible) |
| ffmpeg | Mux, title card, future polish presets |
| AIQA / UIQA | Desktop MCP when a beat must leave the browser — [deferred](docs/aiqa-desktop-deferred.md) |

## Docs map

| File | Purpose |
|---|---|
| [SPEC.md](SPEC.md) | Acceptance criteria (incl. polish + desktop) |
| [ROADMAP.md](ROADMAP.md) | v0 → v1 themes |
| [TASKS.md](TASKS.md) | Executable board |
| [MCP.md](MCP.md) | Intent → tools |
| [docs/plans/2026-11-02-demo-studio-roadmap.md](docs/plans/2026-11-02-demo-studio-roadmap.md) | Original phase checklist |

## Watchlist — Screen Studio–style polish (MIT-friendly)

Prefer these over Recordly (AGPL) when we want cursor zoom / Apple-style motion. Almost all are still **desktop recorders**, not drop-in libs for Playwright beats — except where noted.

| Project | License | Fit for demo-studio |
|---|---|---|
| [getopenscreen/openscreen](https://github.com/getopenscreen/openscreen) (~5.8k★) | MIT | Best maintained OpenScreen line; auto-zoom from `.cursor.json`; **headless CLI** (`record` / `export`) — strongest post-process candidate |
| [tandryukha/aidemo](https://github.com/tandryukha/aidemo) | MIT | Closest **architecture twin**: storyboard → Chrome replay → TTS → auto-zoom compose; agent/CI oriented (young / low stars — verify before depending) |
| [MinhOmega/Capturia](https://github.com/MinhOmega/Capturia) | MIT | OpenScreen fork; GUI zoom + cursor themes |
| [SECHAK-AG/capptivo](https://github.com/SECHAK-AG/capptivo) | MIT | Tauri; `cursor.json` + click auto-zoom |
| [JNX03/Flowtake](https://github.com/JNX03/Flowtake) | MIT | Cursor-driven zoom/pan editor (very new) |
| [sabbour/followcursor](https://github.com/sabbour/followcursor) | MIT | Windows Python; click-cluster zooms + ffmpeg export |
| [siddharthvaddem/openscreen](https://github.com/siddharthvaddem/openscreen) | MIT | Archived original; use getopenscreen instead |
| [webadderallorg/Recordly](https://github.com/webadderallorg/Recordly) | AGPL (+ extra terms) | Taste reference only — do not vendor |

**Practical split:** keep beat/TTS/mux in demo-studio; either (a) emit a cursor/click timeline from Playwright and compose like OpenScreen/aidemo, or (b) optional human/CLI polish pass with OpenScreen export. Keep secrets out of this file; use ignored `MCP.local.md` for LAN mounts.

### Probe — OpenScreen CLI on Mint DevHost (`192.168.5.215`, 2026-11-02)

Host is **Linux Mint 22.1**. AppImage `v2.1.2` at `~/tools/openscreen-probe/`.

| Check | Result |
|---|---|
| `AppImage --no-sandbox help` | OK |
| `sources` over bare SSH (no DISPLAY) | Fail — needs display server |
| `xvfb-run … sources` | OK |
| `xvfb-run … export` minimal project | OK (`tiny-out.mp4`) |
| `record` unattended over SSH | **Not viable** — Linux ScreenCast portal picker each run; needs a real desktop session |

Script: [`scripts/probe-openscreen-mint.sh`](scripts/probe-openscreen-mint.sh) (run on the Mint host).
