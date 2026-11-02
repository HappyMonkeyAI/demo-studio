from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from demo_studio.beats import load_beats, validate_beats
from demo_studio.capture import frames_to_mp4
from demo_studio.chrome_capture import capture_beat_frames
from demo_studio.narrate import narrate_beats
from demo_studio.neo_script import compile_neo_run_js
from demo_studio.looks import apply_look
from demo_studio.package_run import mux_package
from demo_studio.playwright_capture import capture_beat_frames_playwright
from demo_studio.polish import burn_title_card
from demo_studio.preflight import resolve_base, run_python_asserts, write_run_log


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


class DemoJobService:
    def __init__(self, root: Path | None = None):
        self.root = (root or Path.cwd()).resolve()
        self.outputs = self.root / "outputs"
        self.outputs.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, job_id: str) -> Path:
        return self.outputs / job_id

    def create_job(self, beats_path: str, *, base_url: str | None = None) -> dict[str, Any]:
        path = Path(beats_path)
        if not path.is_file():
            path = self.root / beats_path
        data = load_beats(path)
        errors = validate_beats(data)
        if errors:
            raise ValueError("; ".join(errors[:8]))
        job_id = f"job-{_utc_stamp()}-{uuid.uuid4().hex[:8]}"
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, job_dir / "demo.beats.json")
        env = dict(os.environ)
        if base_url:
            env["DEMO_BASE_URL"] = base_url
        base = base_url or resolve_base(data, env)
        meta = {
            "job_id": job_id,
            "status": "created",
            "beats": str(path.resolve()),
            "base_url": base,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "steps": {},
        }
        write_run_log(job_dir / "job.json", meta)
        (job_dir / "neo-run.js").write_text(
            compile_neo_run_js(data, base_url=base or "http://127.0.0.1:0"),
            encoding="utf-8",
        )
        return meta

    def get_job(self, job_id: str) -> dict[str, Any]:
        path = self._job_dir(job_id) / "job.json"
        if not path.is_file():
            raise FileNotFoundError(f"unknown job_id: {job_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, meta: dict[str, Any]) -> dict[str, Any]:
        job_dir = self._job_dir(meta["job_id"])
        write_run_log(job_dir / "job.json", meta)
        return meta

    def run_job(
        self,
        job_id: str,
        *,
        engine: str = "auto",
        title_card: str | None = None,
        subtitle: str = "",
        look: str = "clean",
        skip_capture: bool = False,
        skip_narrate: bool = False,
    ) -> dict[str, Any]:
        meta = self.get_job(job_id)
        job_dir = self._job_dir(job_id)
        data = load_beats(job_dir / "demo.beats.json")
        base = meta.get("base_url") or resolve_base(data, dict(os.environ))
        if not base:
            raise RuntimeError("DEMO_BASE_URL / job base_url required")
        meta["base_url"] = base
        meta["status"] = "running"
        self._save(meta)

        http = run_python_asserts(data, base)
        meta["steps"]["http_asserts"] = http
        if any(not r.get("ok") for r in http):
            meta["status"] = "failed"
            meta["error"] = "http_ok assert failed"
            return self._save(meta)

        if not skip_capture:
            frames = job_dir / "frames"
            cap = data.get("capture") or {}
            width = int(cap.get("width") or 1920)
            height = int(cap.get("height") or 1080)
            used = engine
            if engine == "auto":
                try:
                    capture_beat_frames_playwright(data, base, frames, width=width, height=height)
                    used = "playwright"
                except Exception:
                    capture_beat_frames(data, base, frames, width=width, height=height)
                    used = "chrome"
            elif engine == "playwright":
                capture_beat_frames_playwright(data, base, frames, width=width, height=height)
            else:
                capture_beat_frames(data, base, frames, width=width, height=height)
            picture = frames_to_mp4(frames, job_dir / "picture.mp4", fps=2, width=width, height=height)
            meta["steps"]["capture"] = {"engine": used, **picture}

        picture = job_dir / "picture.mp4"
        if picture.is_file() and look and look != "clean":
            looked = job_dir / "picture.look.mp4"
            apply_look(picture, looked, look=look)
            looked.replace(picture)
            meta["steps"]["look"] = {"look": look}

        if title_card and picture.is_file():
            polished = job_dir / "picture.polished.mp4"
            burn_title_card(picture, polished, title=title_card, subtitle=subtitle)
            polished.replace(picture)
            meta["steps"]["polish"] = {"title_card": title_card, "subtitle": subtitle}

        if not skip_narrate:
            narr = narrate_beats(data, job_dir / "narration", provider=os.environ.get("DEMO_TTS_PROVIDER"))
            meta["steps"]["narrate"] = {
                "provider": narr.get("provider"),
                "total_ms": narr.get("total_ms"),
                "cues": len(narr.get("cues") or []),
            }

        pkg = mux_package(job_dir)
        meta["steps"]["package"] = pkg
        meta["status"] = "awaiting_final_review"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._save(meta)

    def approve_final(self, job_id: str, reviewer: str = "local-user") -> dict[str, Any]:
        meta = self.get_job(job_id)
        if meta.get("status") not in {"awaiting_final_review", "approved"}:
            raise RuntimeError(f"job not ready for approval: {meta.get('status')}")
        demo = self._job_dir(job_id) / "demo.mp4"
        if not demo.is_file():
            raise RuntimeError("demo.mp4 missing")
        meta["status"] = "approved"
        meta["approved_by"] = reviewer
        meta["approved_at"] = datetime.now(timezone.utc).isoformat()
        return self._save(meta)

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        jobs = []
        for path in sorted(self.outputs.glob("job-*/job.json"), reverse=True)[:limit]:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        return jobs
