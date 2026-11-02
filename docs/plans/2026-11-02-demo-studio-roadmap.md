# demo-studio development roadmap

**Date:** 2026-11-02 · **Host:** DevHost `192.168.5.215`

Re-runnable product walkthrough → MP4. Picture = live UI (NEO). Voice/package patterns from `qwen-video-studio`. Not Recordly runtime; not generative UI.

## Phase 0 — Foundation

1. ADR `0001` — scope, layers, reuse, non-goals
2. `schema/beat.schema.json`
3. `pyproject.toml` + CLI: `doctor`, `validate`, `dry-run`
4. Pocket TTS client; `doctor` checks TTS + ffmpeg
5. `demos/astro-cms/` sample beats + README
6. Sync to `/home/stephen/projects/demo-studio` on `.215`
7. `PROGRESS.md`

**Exit:** `demo-studio validate` + `doctor` green on `.215`.

## Phase 1 — Actuation

8. NEO runner from beats
9. Action vocabulary (navigate, act, wait)
10. Asserts; fail run + `run-log.json`
11. Throwaway/lawyer-demo fixture only (no `client-data/`)
12. `dry-run` full beat list

**Exit:** Two dry-runs succeed on the same beat file.

## Phase 2 — Capture

13. CDP/browser screencast (preferred) or ffmpeg display
14. `record` → `outputs/<run>/`
15. Fixed resolution contract (e.g. 1920×1080)
16. Silent `picture.mp4`

**Exit:** Watchable silent walkthrough.

## Phase 3 — Narration + package

17. Per-beat Pocket TTS → WAV
18. ffmpeg mux + WebVTT
19. `review.html` + manifest
20. `package` CLI

**Exit:** Draft MP4 + review package for astro-cms.

## Phase 4 — Content + polish

21. Lock VO script in beats
22. READY vs one-blocker ending choice
23. Title cards / chapters / light ffmpeg polish
24. YouTube/X packaging notes
25. Re-run gate after a small beat edit

**Exit:** Approved first public-ready asset.

## Phase 5 — Productize (optional)

26. Second `demos/<product>/`
27. Optional job/MCP API
28. AIQA desktop beats if needed
29. Dedicated display / light isolation
30. Upload helpers (dry-run then real)

## Standing rules

- No client names, domains, or `client-data/` in demos or committed outputs
- Prefer beat edits over one-off scripts
- Do not block on Recordly, AIQA, or a VM before Phase 3 exit
