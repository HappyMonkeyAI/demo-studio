from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def apply_local_demo_env(root: Path | None = None) -> None:
    """Load .local/*.env into os.environ without overriding existing keys."""
    base = root or Path.cwd()
    for path in sorted((base / ".local").glob("*.env")) if (base / ".local").is_dir() else []:
        for key, val in load_env_file(path).items():
            os.environ.setdefault(key, val)
            # Throwaway site.sh writes BASE=; demo-studio expects DEMO_BASE_URL.
            if key == "BASE":
                os.environ.setdefault("DEMO_BASE_URL", val.replace("localhost", "127.0.0.1"))

