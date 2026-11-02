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

## Watchlist (polish / desktop)

Add verified links here when researching T24–T32 (ffmpeg Ken Burns recipes, cursor overlays, AIQA/UIQA MCP endpoints). Keep secrets out of this file; use ignored `MCP.local.md` for LAN mounts.
