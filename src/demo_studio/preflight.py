from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def resolve_base(data: dict[str, Any], environ: dict[str, str]) -> str | None:
    env_name = data.get("base_url_env") or "DEMO_BASE_URL"
    return environ.get(env_name) or environ.get("DEMO_BASE_URL")


def check_http_ok(base: str, path: str, timeout: float = 15.0) -> dict[str, Any]:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = base + path
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as response:
            code = response.status
            return {"ok": 200 <= code < 400, "url": url, "status": code}
    except HTTPError as exc:
        return {"ok": False, "url": url, "status": exc.code, "error": str(exc)}
    except URLError as exc:
        return {"ok": False, "url": url, "status": None, "error": str(exc.reason)}


def run_python_asserts(data: dict[str, Any], base: str) -> list[dict[str, Any]]:
    """Execute asserts that do not need a browser (http_ok)."""
    results: list[dict[str, Any]] = []
    for beat in data.get("beats") or []:
        bid = beat.get("id")
        for assertion in beat.get("assert") or []:
            if assertion.get("type") != "http_ok":
                continue
            path = assertion.get("path") or "/"
            r = check_http_ok(base, path)
            r["beat"] = bid
            r["assertion"] = assertion
            results.append(r)
    return results


def write_run_log(path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
