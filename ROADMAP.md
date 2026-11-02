# ROADMAP.md — demo-studio

Living plan. Historical phase checklist: [docs/plans/2026-11-02-demo-studio-roadmap.md](docs/plans/2026-11-02-demo-studio-roadmap.md). Acceptance: [SPEC.md](SPEC.md). Queue: [TASKS.md](TASKS.md).

## v0.1 — MVP pipeline (shipped)

Beat schema → validate → Playwright capture → Pocket/Piper narrate → ffmpeg package → `review.html`. Multi-product packs, install helpers, `run-demo`, jobs + stdio MCP, MIT, public GitHub.

**Exit evidence:** tag `v0.1.0`, `scripts/verify-roadmap.py` 22/22, packaged AlongFor / Realms / astro-cms runs.

## v0.2 — Discoverability & hygiene

Finish the onboarding surface so strangers and agents hit the happy path without tribal knowledge.

- Commit/push `QUICKSTART.md`, `docs/USAGE.md`, `run-demo.ps1`, spine docs (`SPEC` / `TASKS` / `ROADMAP` / `LINKS` / `MCP`).
- Point `origin` at `HappyMonkeyAI/demo-studio`.
- Human FINAL_REVIEW before first public social post.
- Optional tag `v0.1.1` after docs land.

## v0.3 — Capture reliability

- Harden cookie / beta / dialog dismiss patterns in packs.
- Visible-only `wait_text` / assert discipline (already started).
- Peer Chrome screenshot path if Playwright isn’t enough on a host.
- Optional Realms “Enter Realm” WebGL beat if stills stay stable.

## v1.0 — Recordly-inspired polish (taste, not runtime)

Original intent: product videos should *feel* like polished demos (zooms, frames, light motion) — inspired by Recordly’s look, implemented in **our** ffmpeg/frame pipeline so we stay MIT-clean and headless-friendly ([ADR 0001](adr/0001-demo-studio-scope.md)).

| Theme | Direction |
|---|---|
| Motion | Soft zoom / Ken Burns on still beats; optional crossfades |
| Focus | Cursor/click emphasis overlays driven by beat actions |
| Editorial | Chapters, stronger title/end cards, look presets |
| Guardrail | Do **not** vendor or spawn Recordly GUI; AGPL stays out of the runtime |

Exit: one public pack re-cut with a documented polish preset, re-run gate still green.

## v1.1 — Desktop beats (AIQA / UIQA)

Pull off the shelf only when a product demo must leave the browser (installer, OS dialog, native shell). See [docs/aiqa-desktop-deferred.md](docs/aiqa-desktop-deferred.md) and SPEC S8.

## v1.2 — Real publish

Opt-in upload helpers (YouTube, X) after dry-run drafts; credentials never in beats or git.

## Standing rules

- Prefer beat edits over one-off recorders.
- Do not block browser MVP work on Recordly, AIQA, or a VM (already true for v0).
- No client names / `client-data/` in demos or committed outputs.
