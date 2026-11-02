"""Optional Phase 5 job/MCP sketch.

Not a full MCP server yet. Documents the intended tool surface so a later
slice can mirror qwen-video-studio's create→poll→export flow.
"""

from __future__ import annotations

TOOLS = [
    {
        "name": "demo_validate",
        "description": "Validate a beat file path",
        "input": {"beats": "string"},
    },
    {
        "name": "demo_run",
        "description": "Enqueue dry-run → capture → narrate → package",
        "input": {"beats": "string", "base_url": "string"},
    },
    {
        "name": "demo_status",
        "description": "Poll a run id under outputs/",
        "input": {"run_id": "string"},
    },
]


def list_tools() -> list[dict]:
    return list(TOOLS)
