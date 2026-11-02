from __future__ import annotations

"""Minimal stdio JSON-RPC MCP server for demo-studio jobs (Phase 5).

Implements tools/list + tools/call for:
  demo_validate, demo_create_job, demo_run_job, demo_get_job, demo_list_jobs,
  demo_approve_final, demo_publication_draft
"""

import json
import sys
from pathlib import Path
from typing import Any

from demo_studio.beats import load_beats, validate_beats
from demo_studio.jobs import DemoJobService
from demo_studio.publish import create_publication_draft, prepare_x_publication_dry_run


def _result_text(payload: Any) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    return {"content": [{"type": "text", "text": text}], "isError": False}


def _error_text(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


TOOLS = [
    {
        "name": "demo_validate",
        "description": "Validate a beat file",
        "inputSchema": {
            "type": "object",
            "properties": {"beats": {"type": "string"}},
            "required": ["beats"],
        },
    },
    {
        "name": "demo_create_job",
        "description": "Create a demo job from a beat file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "beats": {"type": "string"},
                "base_url": {"type": "string"},
            },
            "required": ["beats"],
        },
    },
    {
        "name": "demo_run_job",
        "description": "Run capture→narrate→package for a job (may take minutes)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "engine": {"type": "string", "enum": ["auto", "playwright", "chrome"]},
                "title_card": {"type": "string"},
                "subtitle": {"type": "string"},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "demo_get_job",
        "description": "Get job status/manifest",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    {
        "name": "demo_list_jobs",
        "description": "List recent jobs",
        "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}},
    },
    {
        "name": "demo_approve_final",
        "description": "Mark a packaged job approved after human review",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "reviewer": {"type": "string"},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "demo_publication_draft",
        "description": "Write a YouTube/X publication dry-run draft for a run/job dir",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_dir": {"type": "string"},
                "platform": {"type": "string", "enum": ["youtube", "x"]},
            },
            "required": ["run_dir"],
        },
    },
]


class DemoStudioMcp:
    def __init__(self, root: Path | None = None):
        self.service = DemoJobService(root)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            if name == "demo_validate":
                data = load_beats(Path(arguments["beats"]))
                errors = validate_beats(data)
                if errors:
                    return _error_text("INVALID\n" + "\n".join(errors))
                return _result_text({"ok": True, "product": data.get("product"), "beats": len(data.get("beats") or [])})
            if name == "demo_create_job":
                return _result_text(
                    self.service.create_job(arguments["beats"], base_url=arguments.get("base_url"))
                )
            if name == "demo_run_job":
                return _result_text(
                    self.service.run_job(
                        arguments["job_id"],
                        engine=arguments.get("engine") or "auto",
                        title_card=arguments.get("title_card"),
                        subtitle=arguments.get("subtitle") or "",
                    )
                )
            if name == "demo_get_job":
                return _result_text(self.service.get_job(arguments["job_id"]))
            if name == "demo_list_jobs":
                return _result_text({"jobs": self.service.list_jobs(int(arguments.get("limit") or 20))})
            if name == "demo_approve_final":
                return _result_text(
                    self.service.approve_final(
                        arguments["job_id"],
                        reviewer=arguments.get("reviewer") or "local-user",
                    )
                )
            if name == "demo_publication_draft":
                run_dir = Path(arguments["run_dir"])
                platform = arguments.get("platform") or "youtube"
                if platform == "x":
                    return _result_text(prepare_x_publication_dry_run(run_dir))
                return _result_text(create_publication_draft(run_dir, platform="youtube"))
            return _error_text(f"unknown tool: {name}")
        except Exception as exc:  # noqa: BLE001 — MCP boundary
            return _error_text(str(exc))


def _read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(payload: dict[str, Any]) -> None:
    raw = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
    sys.stdout.buffer.flush()


def main() -> None:
    server = DemoStudioMcp(Path.cwd())
    while True:
        msg = _read_message()
        if msg is None:
            break
        method = msg.get("method")
        req_id = msg.get("id")
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "demo-studio", "version": "0.1.0"},
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params") or {}
            result = server.call_tool(params.get("name") or "", params.get("arguments") or {})
        elif method == "ping":
            result = {}
        else:
            if req_id is None:
                continue
            _write_message(
                {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
            )
            continue
        if req_id is not None:
            _write_message({"jsonrpc": "2.0", "id": req_id, "result": result})


if __name__ == "__main__":
    main()
