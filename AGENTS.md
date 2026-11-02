# AGENTS.md — demo-studio

## Session

If Spine MCP is available: `session_brief(project="demo-studio")` or this repo’s absolute path. Checkpoint before stopping (`agent: cursor` or your name).

## Rules

- Prefer editing beat files and small orchestration code over one-off manual recording scripts.
- Never point demos at confidential pilot/`client-data` trees.
- Capture and NEO actuation may be stubbed until Phase 1–2; keep the beat schema stable.
- When adding TTS or package behaviour, prefer matching `qwen-video-studio` conventions over inventing new ones.

## Skills / hosts

- Primary runtime: DevHost `192.168.5.215`.
- Browser: BrowserOS NEO MCP.
- TTS: Pocket TTS on loopback (often already up on the peer).
