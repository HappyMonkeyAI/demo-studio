# TASKS.md — demo-studio board

Status: `todo` → `doing` → `done`. Evidence in PROGRESS / memories / tags. Spec refs: [SPEC.md](SPEC.md). Plan: [ROADMAP.md](ROADMAP.md).

## P0 — Foundation (done)

- [x] T1 ADR 0001 scope + layers — SPEC S0
- [x] T2 Beat schema + validate CLI — SPEC S2
- [x] T3 Doctor (ffmpeg + Pocket TTS) — SPEC S1
- [x] T4 Pocket TTS client + narrate — SPEC S3
- [x] T5 Playwright capture → picture.mp4 — SPEC S3
- [x] T6 Package mux + review.html + title card — SPEC S3
- [x] T7 Jobs CLI + mcp-serve + publish dry-run — SPEC S5
- [x] T8 Roadmap verifier 22/22 — tag path to `v0.1.0`

## P1 — Multi-product MVP (done)

- [x] T9 Piper TTS adapter + `--provider` — SPEC S1/S3
- [x] T10 Extended astro-cms beats (SSO / editor / plugins / import)
- [x] T11 `demos/alongfor` public pack — SPEC S4
- [x] T12 `demos/mrpg-realms` wiki pack — SPEC S4
- [x] T13 MIT LICENSE + public HappyMonkeyAI repo + tag `v0.1.0`
- [x] T14 `install.sh` / `install.ps1`
- [x] T15 `scripts/run-demo.sh` one-shot

## P2 — Discoverability (now)

- [x] T16 Commit/push `QUICKSTART.md`, `docs/USAGE.md`, `scripts/run-demo.ps1`, README/AGENTS/CONTEXT updates
- [x] T17 Land spine docs: `SPEC.md`, `TASKS.md`, `ROADMAP.md`, `LINKS.md`, `MCP.md`
- [x] T18 Fix git `origin` → `https://github.com/HappyMonkeyAI/demo-studio.git`
- [ ] T19 Human FINAL_REVIEW tick before first public social post — SPEC S6
- [x] T20 Tag `v0.1.1` (OpenScreen Mint probe + polish docs)

## P3 — Reliability

- [ ] T21 Harden cookie/beta dialog dismiss across packs
- [ ] T22 Peer Chrome capture fallback notes / fix if still broken on `.215`
- [ ] T23 Optional Realms Enter-Realm WebGL still beat (only if repeatable)

## P4 — Recordly-style polish (SPEC S7)

- [x] T24 Research note: Recordly look → ffmpeg/frame primitives we can own (no AGPL runtime)
- [x] T25 Soft zoom / Ken Burns preset on still beats (`product-zoom`)
- [ ] T26 Optional crossfade between beats
- [x] T27 Cursor timeline from Playwright + `--look studio` compose (zoom-to-click + pointer)
- [x] T28 Look presets (`clean`, `product-zoom`, `studio`) wired into `package` / `job-run` / run-demo
- [x] T29 Re-cut packaged run with `--look product-zoom` (`outputs/polish-product-zoom-t29/`) — human eyeball still owed
- [ ] T27b Smooth cursor path between clicks + fill I-beam; optional OpenScreen export handoff via `cursor.openscreen.json`

## P5 — AIQA / UIQA desktop (SPEC S8)

- [ ] T30 Confirm AIQA/UIQA MCP health on demo host before coding
- [ ] T31 Desktop action vocabulary + adapter (browser packs unchanged)
- [ ] T32 One native-installer or OS-dialog demo pack as proof

## P6 — Real publish (SPEC S9)

- [ ] T33 YouTube upload helper (opt-in credentials)
- [ ] T34 X media post helper (opt-in)

## Parked

- AIQA desktop before a real desktop beat need — see `docs/aiqa-desktop-deferred.md`
- Recordly GUI embedding / forking — out of scope (taste only)
- Auto-publish without human `review.html` — non-goal
