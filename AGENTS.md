# AGENTS.md — demo-studio

## How to use (any agent)

1. Read [QUICKSTART.md](QUICKSTART.md), [docs/USAGE.md](docs/USAGE.md), then [TASKS.md](TASKS.md) / [ROADMAP.md](ROADMAP.md) for what’s next.
2. Setup: `./install.sh` or `.\install.ps1`, activate `.venv`, `demo-studio doctor`.
3. Prefer one-shot runs over inventing scripts:
   - `./scripts/run-demo.sh alongfor`
   - `./scripts/run-demo.sh mrpg-realms --provider piper`
4. Change demos by editing `demos/<product>/demo.beats.json`, then re-validate / re-run.
5. After package, point a human at `outputs/<run>/review.html` — do not auto-publish.
6. Recordly = taste only (SPEC S7); AIQA/UIQA only when a beat leaves the browser (SPEC S8). Tool map: [MCP.md](MCP.md).

If Spine MCP is available: `session_brief(project="demo-studio")` or this repo’s absolute path. Checkpoint before stopping (`agent: cursor` or your name).

## Rules

- Prefer editing beat files and small orchestration code over one-off manual recording scripts.
- Never point demos at confidential pilot/`client-data` trees.
- Keep the beat schema stable; extend via schema + Playwright actions, not ad-hoc recorders.
- When adding TTS or package behaviour, prefer matching `qwen-video-studio` conventions over inventing new ones.
- Secrets in env / `.local/*.env` only — never in beat JSON.

## Optional LAN hosts (maintainers)

- Primary runtime: DevHost `192.168.5.215`.
- Browser: BrowserOS NEO MCP (optional; Playwright is the default public path).
- TTS: Pocket TTS or Piper on loopback (often already up on the peer).
