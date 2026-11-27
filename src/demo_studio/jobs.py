from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from demo_studio.assemble import assemble_picture
from demo_studio.beats import load_beats, validate_beats, visual_kind
from demo_studio.capture import frames_to_mp4
from demo_studio.chrome_capture import capture_beat_frames
from demo_studio.narrate import narrate_beats
from demo_studio.neo_script import compile_neo_run_js
from demo_studio.package_run import mux_package
from demo_studio.playwright_capture import capture_beat_frames_playwright
from demo_studio.polish import burn_title_card
from demo_studio.preflight import resolve_base, run_python_asserts, write_run_log
from demo_studio.studio_compose import compose_studio_mp4


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

        # Clip-source packs (Task 4): engines skip clip beats, so the picture
        # is assembled after narration, per-beat, aligned to cue durations.
        beats_list = list(data.get("beats") or [])
        kinds = [visual_kind(b) for b in beats_list]
        has_clip = "clip" in kinds
        all_clip = bool(kinds) and all(k == "clip" for k in kinds)
        cap = data.get("capture") or {}
        width = int(cap.get("width") or 1920)
        height = int(cap.get("height") or 1080)

        if not skip_capture:
            if all_clip:
                # A clip-only pack has nothing to screenshot: the engines write
                # zero frames and playwright_capture raises "no frames captured",
                # which is the expected outcome here, not a failure. Same rule as
                # cli._cmd_capture so both entry paths behave identically.
                meta["steps"]["capture"] = {"engine": "none", "picture": "deferred"}
            else:
                frames = job_dir / "frames"
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
                if has_clip:
                    # Frames for clip beats legitimately do not exist; assembling
                    # the whole frames dir here would mis-time the picture.
                    meta["steps"]["capture"] = {"engine": used, "picture": "deferred"}
                else:
                    picture = frames_to_mp4(frames, job_dir / "picture.mp4", fps=2, width=width, height=height)
                    meta["steps"]["capture"] = {"engine": used, **picture}
        elif has_clip:
            # skip_capture never assembles, so whatever picture.mp4 holds is
            # what ships. With no picture at all, mux_package falls back to its
            # color-card branch and the job reaches awaiting_final_review with
            # none of the clip segments in it — fail loudly instead.
            existing = job_dir / "picture.mp4"
            if not existing.is_file():
                raise RuntimeError(
                    "clip packs get their picture from per-beat assembly, which runs during capture; "
                    f"{existing} is missing — re-run without skip_capture (or package with --beats)"
                )
            print(
                f"warning: skip_capture with clip beats packages {existing} as-is; "
                "it may predate the clip beats and be missing their segments",
                file=sys.stderr,
            )

        narr: dict[str, Any] | None = None
        if not skip_narrate:
            narr = narrate_beats(data, job_dir / "narration", provider=os.environ.get("DEMO_TTS_PROVIDER"))
            meta["steps"]["narrate"] = {
                "provider": narr.get("provider"),
                "total_ms": narr.get("total_ms"),
                "cues": len(narr.get("cues") or []),
            }

        if has_clip and not skip_capture:
            cues = (narr or {}).get("cues")
            if cues is None:
                narr_json = job_dir / "narration" / "narration.json"
                if not narr_json.is_file():
                    raise RuntimeError(
                        "clip packs require narration cues to assemble the picture (drop skip_narrate or run narrate)"
                    )
                cues = json.loads(narr_json.read_text(encoding="utf-8")).get("cues") or []
            meta["steps"]["assemble"] = assemble_picture(
                data, cues, job_dir / "frames", job_dir,
                pack_dir=Path(meta["beats"]).parent, width=width, height=height,
            )

        picture = job_dir / "picture.mp4"
        if title_card and picture.is_file():
            polished = job_dir / "picture.polished.mp4"
            burn_title_card(picture, polished, title=title_card, subtitle=subtitle)
            polished.replace(picture)
            meta["steps"]["polish"] = {"title_card": title_card, "subtitle": subtitle}

        look_name = look or "clean"
        mux_look = look_name
        look_step: dict[str, Any] = {"look": look_name}
        if look_name == "studio" and has_clip:
            # Studio compose rebuilds from frames + cursor.json, which clip
            # packs never fully populate — fall back to clean for v1.
            mux_look = "clean"
            look_step = {"look": "clean", "note": "studio look disabled for mixed packs (v1)"}
        elif look_name == "studio" and (job_dir / "cursor.json").is_file():
            compose_studio_mp4(job_dir, job_dir / "picture.mp4")
            mux_look = "clean"
        pkg = mux_package(job_dir, look=mux_look)
        pkg["look"] = look_name
        meta["steps"]["package"] = pkg
        meta["steps"]["look"] = look_step
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
