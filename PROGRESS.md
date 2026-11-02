# PROGRESS — demo-studio

## Now

**v0.1 MVP shipped** (public `HappyMonkeyAI/demo-studio`, tag `v0.1.0`). Next: P2 discoverability docs on `main`, then P4 Recordly-inspired polish + P5 AIQA when needed — see [ROADMAP.md](ROADMAP.md) / [TASKS.md](TASKS.md). Optional human eyeball: `demos/astro-cms/FINAL_REVIEW.md` before a public YouTube post.

## Done

- Phase 0: ADR, schema, CLI, TTS client, astro-cms beats, `.215` sync, doctor green.
- Phase 1: neo-run.js, http_ok, throwaway `:4335`, NEO smoke, dry-runs.
- Phase 2: Playwright capture → `picture.mp4` (peer Chrome headless hangs).
- Phase 3: Pocket TTS + mux → ~44s `demo.mp4` + captions + `review.html`.
- Phase 4: title-card polish, `PUBLISH.md` / `FINAL_REVIEW.md`, second capture `rerun-gate-b` packaged.
- Phase 5: `demos/example-static`, `job-*` CLI, stdio `mcp-serve`, YouTube/X **dry-run** drafts (`publish.py`). Job `job-20261102T101440630167Z-68d3d828` marked `approved` by pipeline-gate.

## Commits

- `3c27a27` jobs/MCP/publish/polish
- `6a43216` initial pipeline scaffold

## Blockers / leftover

- Commit spine + QUICKSTART/USAGE/run-demo.ps1 still local (TASKS P2)
- Human visual sign-off on `FINAL_REVIEW.md`
- Planned (not blockers): Recordly-style ffmpeg polish (SPEC S7), AIQA/UIQA desktop (SPEC S8), real upload (SPEC S9)
