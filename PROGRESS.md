# PROGRESS — demo-studio

## Now

**Roadmap goal complete.** `scripts/verify-roadmap.py` → **22/22** locally and on DevHost `.215`. Optional human eyeball: `demos/astro-cms/FINAL_REVIEW.md` before a public YouTube post.

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

- Human visual sign-off on `FINAL_REVIEW.md`
- Optional: real upload (still dry-run), AIQA desktop, fix peer Chrome screenshot
