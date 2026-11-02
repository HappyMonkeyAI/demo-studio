# PROGRESS — demo-studio

## Now

**Goal active:** complete roadmap Phases 0–5.  
Phases **0–3 verified**. Phase **4** needs human review of `demo.mp4` + re-run gate execution. Phase **5** has second pack + MCP stub; full job server / uploads still open.

## Done

- 2026-11-02: Phase 0 — ADR, beat schema, CLI (`doctor`/`validate`/`dry-run`), Pocket TTS client, astro-cms beats, sync to `.215`. **Exit met:** `validate` + `doctor` green on peer.
- 2026-11-02: Phase 1 — `neo-run.js` compiler, http_ok preflight, throwaway `demostudio` on `:4335`, two dry-runs OK, NEO smoke (home + admin login) via tunnel.
- 2026-11-02: Phase 2 — Playwright capture → `picture.mp4` (Chrome headless on peer hangs; Playwright preferred).
- 2026-11-02: Phase 3 — Pocket TTS narrate + ffmpeg mux → `demo.mp4` (~44s), `captions.vtt`, `review.html` on peer (`outputs/run-playwright-capture/`). Fixed WAV duration via ffprobe.

## Next

1. Phase 4 — lock VO, chapter cards, re-run gate, human review of `demo.mp4`.
2. Phase 5 — second demo pack / optional MCP job API / upload helpers.
3. Optional: fix peer Chrome headless; bind throwaway for LAN without SSH tunnel.

## Blockers

- Peer `google-chrome --screenshot` hangs (use Playwright or NEO for frames).
- Throwaway ports bound `127.0.0.1` — Windows NEO/Playwright need SSH `-L` tunnel.
