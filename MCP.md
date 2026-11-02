# MCP.md — demo-studio intent map

Portable routing map, not a live catalogue dump. Confirm tools are mounted in the session before use. Machine-specific URLs/ports belong in ignored `MCP.local.md` (do not commit secrets).

## Built-in: demo-studio stdio MCP

Start from a configured venv:

```bash
demo-studio mcp-serve
# or: demo-studio-mcp
```

| Tool | Intent |
|---|---|
| `demo_validate` | Validate a beat file |
| `demo_create_job` | Create `outputs/job-*` from beats (+ optional base URL) |
| `demo_run_job` | capture → narrate → package for a job |
| `demo_get_job` / `demo_list_jobs` | Status / recent jobs |
| `demo_approve_final` | Mark packaged job approved after human review |
| `demo_publication_draft` | YouTube/X **dry-run** draft only |

Prefer CLI/`scripts/run-demo.*` for local interactive runs; use MCP when an agent host needs tool calls.

## External MCP / hosts by intent

| Intent | Preferred | Notes |
|---|---|---|
| Warm-start this repo | `spine` (`session_brief`, `checkpoint`, …) | Pass absolute project path |
| Browser actuate / verify product UI | BrowserOS **neo** | Optional; Playwright capture is default for packaging |
| Desktop / OS UI (future) | AIQA / UIQA | Only when SPEC S8 / TASKS P5 are in play — see [docs/aiqa-desktop-deferred.md](docs/aiqa-desktop-deferred.md) |
| Heavy peer work | `resource_sentinel` → DevHost | Capture/mux can be CPU-heavy; offload when policy says peer |
| Agent coordination on LAN | `agent_communication` | Optional; not required for MVP packs |
| Knowledge / prior art | `neo4j-semantic-search` / kb_vault | Research polish recipes; don’t invent AGPL forks |

## Env the tools care about

| Var | Use |
|---|---|
| `DEMO_BASE_URL` | Subject site (required for capture) |
| `POCKET_TTS_URL` / `PIPER_TTS_URL` | Narration sidecars |
| `DEMO_TTS_PROVIDER` | `pocket` \| `piper` |
| `BROWSEROS_NEO_MCP_URL` / `NEO_MCP_URL` | Informational for `doctor` |
| Admin fill envs | e.g. `ADMIN_PASSWORD` via `.local/*.env` |

## Rules

1. Route by intent, then verify the live tool list.
2. Never put tokens, passwords, or raw credential paths in this file.
3. Do not auto-publish; MCP approve ≠ social upload.
4. Recordly is **not** an MCP dependency — polish is ffmpeg/frame work in-repo (SPEC S7).
