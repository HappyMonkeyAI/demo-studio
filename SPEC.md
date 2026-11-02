# SPEC.md — demo-studio acceptance

Each criterion is independently verifiable. Evidence: CLI output, packaged `review.html` / `demo.mp4`, or schema validation.

## S0 — Intent

- [x] Beat files are the source of truth; success = same beats → recognisably similar video on re-run.
- [x] Picture comes from a **live product** (Playwright / optional NEO), not generative UI.
- [x] Never demo confidential pilot / `client-data` trees.

## S1 — Install & doctor

- [x] `./install.sh` / `.\install.ps1` create `.venv`, install `.[dev,capture]`, offer Chromium + ffmpeg.
- [x] `demo-studio doctor` reports ffmpeg + Pocket TTS; Piper optional via `DEMO_TTS_PROVIDER=piper`.

## S2 — Beat contract

- [x] `schema/beat.schema.json` validates packs under `demos/*/demo.beats.json`.
- [x] Actions include navigate / wait_text / wait_ms / click_text / fill / scroll / press (and schema-listed peers).
- [x] Assert failures fail the run (no silent wrong-click ship).

## S3 — Capture → narrate → package

- [x] `capture` writes frames + silent `picture.mp4` (`--engine playwright` default path).
- [x] `narrate` writes per-beat audio (Pocket or Piper).
- [x] `package` muxes to `demo.mp4` + WebVTT + `review.html` (optional title card).
- [x] One-shot: `./scripts/run-demo.sh <pack>` (Windows: `.\scripts\run-demo.ps1`).

## S4 — Multi-product packs

- [x] Public packs: `alongfor`, `mrpg-realms` (default URLs in run-demo).
- [x] Self-hosted: `astro-cms` against throwaway EmDash only.
- [x] Secrets via env / `.local/*.env` — never in committed beat JSON.

## S5 — Jobs + MCP (thin)

- [x] `job-create` / `job-run` / `job-status` / `job-approve` under `outputs/job-*`.
- [x] `demo-studio mcp-serve` exposes validate / job / publication-draft tools over stdio.
- [x] YouTube/X helpers are **dry-run drafts** only (no auto-upload).

## S6 — Human gate

- [x] Operator opens `review.html` before publishing.
- [ ] Human ticks `demos/astro-cms/FINAL_REVIEW.md` (or equivalent) before a first public YouTube/X post. *(live)*

## S7 — Recordly-style visual polish (post-MVP)

Taste inspiration only — **not** embedding Recordly’s AGPL GUI as runtime ([ADR 0001](adr/0001-demo-studio-scope.md)). Notes: [docs/recordly-polish-notes.md](docs/recordly-polish-notes.md).

- [x] Beat- or package-level **Ken Burns / soft zoom** via `--look product-zoom` (`demo_studio.looks`).
- [ ] Optional **crossfade / dissolve** between beats when capture is still-frame based.
- [ ] Optional **cursor highlight / click ripple** overlay for click actions.
- [ ] Chapter markers / richer title cards beyond Phase 4 `burn_title_card`.
- [x] Documented “look” presets (`clean`, `product-zoom`) on `package` / `job-run` / `run-demo` — no GUI app.

## S8 — AIQA / UIQA desktop actuation (post-MVP)

Deferred until a beat must leave the browser ([docs/aiqa-desktop-deferred.md](docs/aiqa-desktop-deferred.md)).

- [ ] Beat actions for native/OS targets (`desktop_*` or equivalent) when AIQA/UIQA MCP is healthy.
- [ ] Adapter beside NEO/Playwright without breaking browser-only packs.
- [ ] Isolation story (dedicated display / light sandbox) only if a pack needs it.

## S9 — Publish (real)

- [x] Dry-run publication drafts.
- [ ] Real YouTube upload helper (opt-in, credentials out of repo).
- [ ] Real X media post helper (opt-in).

## Non-goals (remain false)

Recordly as headless runtime · generative fake UI · auto-publish without human review · confidential client subjects.
