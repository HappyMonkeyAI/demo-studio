# Clip-Source Beats + AI Update Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a demo-studio beat file use trimmed existing mp4 clips as a beat's visual (alongside Playwright captures), then produce the `ai-update-2026-11` reel (~17 min, 6 approved segments) end-to-end.

**Architecture:** Additive `visual: {kind: "clip", file, in_sec, out_sec}` on beats. Capture engines skip clip beats; when a pack contains clip beats, picture assembly is deferred until after narrate and becomes per-beat segments (stills held for the beat's narration duration, clips trimmed/scale-padded/tpad-padded) concat'd into `picture.mp4`. Everything downstream (polish, mux, captions, review.html, publish draft) is unchanged.

**Tech Stack:** Python 3 (package `demo_studio`), jsonschema, ffmpeg 9.0 CLI via subprocess, pytest.

**Spec:** `docs/plans/2026-11-26-youtube-ai-update-video-design.md` (includes C-probe findings — read it before Task 1)

## Global Constraints

- Host ffmpeg is **9.0**: removed flags like `-vsync` are forbidden; use `-fps_mode` if frame-rate dropping must be explicit.
- Beat schema `version` stays `1`; the `visual` object is a pure additive property; `additionalProperties: false` everywhere.
- Never auto-publish. `publish.py` stays dry-run; human uploads.
- Clip files are read-only inputs; all trims live in the beats file.
- Common segment encode profile: canvas from `capture.width/height` (default 1920×1080), 30 fps, `libx264` + `yuv420p`, silent AAC 48 kHz stereo track on every segment.
- Letterbox/pillarbox with black pad only in v1 (no blur fill, no crop).
- TDD: failing test first, minimal implementation, commit per task. Tests live in `tests/test_*.py`; ffmpeg-dependent tests use `@pytest.mark.skipif(not shutil.which("ffmpeg"), ...)`.
- Packs must not point at confidential pilot/`client-data` trees; secrets in env/`.local/*.env` only.
- Both entry paths must work: `demo-studio job-run` (jobs.py) and standalone `validate → capture → narrate → package` (scripts/run-demo.sh + run-demo.ps1).
- Run tests from the venv at repo root: `python -m pytest tests/<file> -v`.

---

### Task 1: Schema + visual validation + docs

**Files:**
- Modify: `src/demo_studio/beat.schema.json` (beat definition, `$defs`)
- Modify: `src/demo_studio/beats.py` (new helpers at end of file)
- Modify: `src/demo_studio/cli.py` (validate command handler; parser around line 242)
- Modify: `docs/USAGE.md` (add "Clip sources" section)
- Test: `tests/test_beats.py` (append)
- Mirror: if `schema/beat.schema.json` exists at repo root, apply the identical schema edit there too (beats.py falls back to it)

**Interfaces:**
- Produces: `visual_kind(beat: dict) -> str` (returns `"capture"` or `"clip"`); `validate_visuals(data: dict, pack_dir: Path) -> list[str]` (empty = valid). Task 3 and 4 import both from `demo_studio.beats`.
- Schema: beat gains optional `visual` object; `kind` required within it; `file` optional at schema level (enforced by `validate_visuals` so error text names the beat).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_beats.py`:

```python
from demo_studio.beats import validate_visuals, visual_kind

def _clip_beat(**vis):
    b = {"id": "c1", "narration": "hi", "visual": {"kind": "clip", **vis}}
    return {"version": 1, "product": "p", "beats": [b]}

def test_visual_kind_defaults_capture():
    assert visual_kind({"id": "a", "narration": "x"}) == "capture"
    assert visual_kind({"id": "a", "narration": "x", "visual": {"kind": "clip", "file": "f.mp4"}}) == "clip"

def test_clip_beat_passes_schema(tmp_path):
    from demo_studio.beats import validate_beats
    data = _clip_beat(file="f.mp4", in_sec=1.5, out_sec=9.0)
    assert validate_beats(data) == []
    (tmp_path / "f.mp4").write_bytes(b"")
    assert validate_visuals(data, tmp_path) == []

def test_clip_missing_file_and_bad_range(tmp_path):
    assert any("requires visual.file" in e for e in validate_visuals(_clip_beat(), tmp_path))
    (tmp_path / "f.mp4").write_bytes(b"")
    assert any("not found" in e for e in validate_visuals(_clip_beat(file="nope.mp4"), tmp_path))
    assert any("out_sec" in e for e in validate_visuals(_clip_beat(file="f.mp4", in_sec=5, out_sec=5), tmp_path))
    assert any("extension" in e for e in validate_visuals(_clip_beat(file="f.txt"), tmp_path))

def test_clip_with_actions_fails(tmp_path):
    data = _clip_beat(file="f.mp4")
    data["beats"][0]["actions"] = [{"type": "navigate", "url": "http://x"}]
    (tmp_path / "f.mp4").write_bytes(b"")
    assert any("actions" in e for e in validate_visuals(data, tmp_path))
```

- [ ] **Step 2: Run tests, verify they fail** — `python -m pytest tests/test_beats.py -v` → ImportError on `visual_kind`.

- [ ] **Step 3: Extend the schema.** In `beat.schema.json`, inside `$defs.beat.properties` add:

```json
"visual": { "$ref": "#/$defs/visual" }
```

and inside `$defs` add:

```json
"visual": {
  "type": "object",
  "required": ["kind"],
  "additionalProperties": false,
  "properties": {
    "kind": { "type": "string", "enum": ["capture", "clip"] },
    "file": { "type": "string", "minLength": 1 },
    "in_sec": { "type": "number", "minimum": 0 },
    "out_sec": { "type": "number", "minimum": 0 }
  }
}
```

- [ ] **Step 4: Implement helpers** — append to `src/demo_studio/beats.py`:

```python
CLIP_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

def visual_kind(beat: dict[str, Any]) -> str:
    return str(((beat.get("visual") or {}).get("kind") or "capture"))

def resolve_clip_path(beat: dict[str, Any], pack_dir: Path) -> Path | None:
    f = (beat.get("visual") or {}).get("file")
    if not f:
        return None
    p = Path(f)
    return p if p.is_absolute() else Path(pack_dir) / f

def validate_visuals(data: dict[str, Any], pack_dir: Path) -> list[str]:
    """Clip-source checks beyond JSON schema. Empty list = valid."""
    errors: list[str] = []
    for i, beat in enumerate(data.get("beats") or []):
        bid = str(beat.get("id") or f"beat{i}")
        if visual_kind(beat) != "clip":
            continue
        v = beat.get("visual") or {}
        if not v.get("file"):
            errors.append(f"{bid}: visual.kind=clip requires visual.file")
            continue
        p = resolve_clip_path(beat, pack_dir)
        assert p is not None
        if not p.is_file():
            errors.append(f"{bid}: clip file not found: {p}")
        if p.suffix.lower() not in CLIP_EXTENSIONS:
            errors.append(f"{bid}: unsupported clip extension {p.suffix or '(none)'}")
        if beat.get("actions"):
            errors.append(f"{bid}: clip beats must not carry browser actions")
        in_sec = float(v.get("in_sec") or 0.0)
        out_sec = v.get("out_sec")
        if out_sec is not None and float(out_sec) <= in_sec:
            errors.append(f"{bid}: visual.out_sec must be greater than in_sec")
    return errors
```

- [ ] **Step 5: Wire into `cli.py` validate handler** — where the `validate` subcommand calls `validate_beats(data)`, also run `validate_visuals(data, Path(beats_path).parent)` and append its errors to the reported list (same exit code path).

- [ ] **Step 6: Run tests green** — `python -m pytest tests/test_beats.py -v` → all PASS (including pre-existing).

- [ ] **Step 7: Document in `docs/USAGE.md`** — add a "Clip sources" subsection under beat anatomy: the `visual` object fields, relative-vs-absolute file resolution (relative to the beats file's directory), clip beats skip the browser, picture assembly is deferred to after narrate for packs containing clips (Task 4), and a minimal example beat JSON.

- [ ] **Step 8: Commit**

```bash
git add src/demo_studio/beat.schema.json src/demo_studio/beats.py src/demo_studio/cli.py docs/USAGE.md tests/test_beats.py schema/beat.schema.json
git commit -m "feat: clip visual source in beat schema + validation"
```

(omit `schema/beat.schema.json` if that file does not exist)

---

### Task 2: clips.py — segment builder

**Files:**
- Create: `src/demo_studio/clips.py`
- Test: `tests/test_clips.py`

**Interfaces:**
- Consumes: `shutil.which("ffmpeg")`, `ffprobe` (pattern copied from `demo_studio.looks._ffprobe_duration`).
- Produces: `probe_video(path: Path) -> dict` with keys `duration_s: float, width: int, height: int`; `build_segment_cmd(ffmpeg: str, source: Path, out: Path, *, in_sec: float, out_sec: float, width: int, height: int, target_dur_s: float | None = None) -> list[str]`; `clip_segment(source: Path, out: Path, *, in_sec: float, out_sec: float | None, width: int, height: int, target_dur_s: float | None = None) -> dict` (returns `{"out", "duration_s", "cmd"}`). Task 4 calls `clip_segment` and `probe_video`.

- [ ] **Step 1: Write the failing tests** — `tests/test_clips.py`:

```python
import shutil
import pytest
from pathlib import Path
from demo_studio.clips import build_segment_cmd

def _vf(cmd):  # extract -vf argument
    return cmd[cmd.index("-vf") + 1]

def test_build_segment_cmd_core():
    cmd = build_segment_cmd("ffmpeg", Path("/in.mp4"), Path("/out.mp4"),
                             in_sec=42.0, out_sec=97.0, width=1920, height=1080)
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd and "42.000" in cmd
    assert "-to" in cmd and "97.000" in cmd
    vf = _vf(cmd)
    assert "scale=1920:1080:force_original_aspect_ratio=decrease" in vf
    assert "pad=1920:1080:(ow-iw)/2:(oh-ih)/2" in vf
    assert "fps=30" in vf and "format=yuv420p" in vf
    assert "tpad" not in vf                      # no padding without target
    assert "anullsrc" in " ".join(cmd)           # silent audio track always
    assert "-vsync" not in " ".join(cmd)         # removed in ffmpeg 9

def test_build_segment_cmd_pads_short_clip():
    cmd = build_segment_cmd("ffmpeg", Path("/in.mp4"), Path("/out.mp4"),
                            in_sec=0.0, out_sec=4.0, width=1920, height=1080,
                            target_dur_s=10.0)
    vf = _vf(cmd)
    assert "tpad=stop_mode=clone:stop_duration=6.000" in vf
    assert "-t" in cmd and "10.000" in cmd
```

- [ ] **Step 2: Run → FAIL** (`ModuleNotFoundError: demo_studio.clips`).

- [ ] **Step 3: Implement `src/demo_studio/clips.py`:**

```python
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def probe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not on PATH")
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr[-400:]}")
    data = json.loads(proc.stdout)
    stream = (data.get("streams") or [{}])[0]
    return {
        "duration_s": float(data["format"]["duration"]),
        "width": int(stream.get("width") or 0),
        "height": int(stream.get("height") or 0),
    }


def build_segment_cmd(
    ffmpeg: str,
    source: Path,
    out: Path,
    *,
    in_sec: float,
    out_sec: float,
    width: int,
    height: int,
    target_dur_s: float | None = None,
) -> list[str]:
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p"
    )
    window = out_sec - in_sec
    if target_dur_s and target_dur_s > window:
        vf += f",tpad=stop_mode=clone:stop_duration={target_dur_s - window:.3f}"
    cmd = [
        ffmpeg, "-y", "-v", "error",
        "-ss", f"{in_sec:.3f}", "-to", f"{out_sec:.3f}", "-i", str(source),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        # explicit maps required: without them ffmpeg's audio selection is
        # input-dependent — a stereo source track beats the lavfi nullsrc and
        # -shortest then truncates the tpad (mono sources can look fine)
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-ar", "48000",
    ]
    if target_dur_s:
        cmd += ["-t", f"{target_dur_s:.3f}"]
    cmd += ["-shortest", str(out)]
    return cmd


def clip_segment(
    source: Path,
    out: Path,
    *,
    in_sec: float = 0.0,
    out_sec: float | None = None,
    width: int = 1920,
    height: int = 1080,
    target_dur_s: float | None = None,
) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    info = probe_video(source)
    if in_sec >= info["duration_s"]:
        raise RuntimeError(f"{source}: in_sec {in_sec} beyond clip duration {info['duration_s']:.1f}s")
    end = min(float(out_sec), info["duration_s"]) if out_sec else info["duration_s"]
    if end <= in_sec:
        raise RuntimeError(f"{source}: out_sec {end} must be greater than in_sec {in_sec}")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_segment_cmd(ffmpeg, source, out, in_sec=in_sec, out_sec=end,
                            width=width, height=height, target_dur_s=target_dur_s)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"clip segment failed for {source}: {proc.stderr[-800:]}")
    return {"out": str(out), "duration_s": target_dur_s or (end - in_sec), "cmd": cmd}
```

- [ ] **Step 4: Run unit tests → PASS.**

- [ ] **Step 5: Add ffmpeg integration test** to `tests/test_clips.py` (mirrors the skipif pattern in `tests/test_looks.py`):

```python
import subprocess

@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_clip_segment_real_trim_and_pad(tmp_path):
    from demo_studio.clips import clip_segment, probe_video
    src = tmp_path / "src.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=size=320x240:rate=60", "-t", "4",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-shortest", "-c:v", "libx264", str(src)], check=True)
    out = tmp_path / "seg.mp4"
    clip_segment(src, out, in_sec=1.0, out_sec=3.0, width=640, height=360, target_dur_s=6.0)
    info = probe_video(out)
    assert info["width"] == 640 and info["height"] == 360
    assert 5.5 <= info["duration_s"] <= 6.5   # 2s window padded to 6s
```

- [ ] **Step 6: Run → PASS (or skip without ffmpeg). Commit:**

```bash
git add src/demo_studio/clips.py tests/test_clips.py
git commit -m "feat: clip segment builder (trim, scale-pad, tpad, silent aac)"
```

---

### Task 3: Capture engines skip clip beats

**Files:**
- Modify: `src/demo_studio/playwright_capture.py` (`capture_beat_frames_playwright`, beats loop around line 135)
- Modify: `src/demo_studio/chrome_capture.py` (`capture_beat_frames` beats loop)
- Test: `tests/test_capture_skip.py` (new)

**Interfaces:**
- Consumes: `visual_kind` from `demo_studio.beats` (Task 1).
- Produces: unchanged signatures — behavior change only: beats with `visual.kind == "clip"` are never visited and produce no frames. Task 4 relies on frames existing only for capture beats.

- [ ] **Step 1: Write the failing test** — `tests/test_capture_skip.py`. The Playwright capture takes a page factory-ish flow; test via monkeypatching the module's internals is brittle, so test the pure decision instead plus a chrome-engine smoke:

```python
from pathlib import Path
from demo_studio.beats import visual_kind

def test_clip_beats_filter_helper():
    beats = [
        {"id": "a", "narration": "x"},
        {"id": "b", "narration": "y", "visual": {"kind": "clip", "file": "f.mp4"}},
    ]
    browser_beats = [b for b in beats if visual_kind(b) == "capture"]
    assert [b["id"] for b in browser_beats] == ["a"]

def test_chrome_capture_skips_clip_beats(tmp_path, monkeypatch):
    from demo_studio import chrome_capture

    visited: list[str] = []
    monkeypatch.setattr(
        chrome_capture, "capture_beat_frames",
        chrome_capture.capture_beat_frames,  # real fn; we intercept its screenshot writer below
    )
    def fake_shot(frames_dir, name, **kw):
        visited.append(name)
    monkeypatch.setattr(chrome_capture, "_screenshot", fake_shot, raising=True)
    data = {"version": 1, "product": "p", "beats": [
        {"id": "a", "narration": "x", "actions": [{"type": "navigate", "url": "http://x"}]},
        {"id": "b", "narration": "y", "visual": {"kind": "clip", "file": "f.mp4"}},
    ]}
    chrome_capture.capture_beat_frames(data, "http://x", tmp_path / "frames", width=320, height=240)
    assert not any("_b." in n for n in visited)
```

NOTE (implementer): open `chrome_capture.py` first and adapt the second test to the module's real screenshot call site — if there is no `_screenshot` seam, add one (a one-line module-level function wrapping the existing screenshot subprocess) as part of this task; that seam is the testable change. If chrome_capture's structure makes this test disproportionate, replace it with the equivalent assertion inside the playwright path's existing test style and keep the pure filter test. Do not skip writing a test.

- [ ] **Step 2: Run → FAIL** (clip beat `b` still visited).

- [ ] **Step 3: Implement.** In both `playwright_capture.capture_beat_frames_playwright` and `chrome_capture.capture_beat_frames`, at the top of the per-beat loop add:

```python
if visual_kind(beat) == "clip":
    continue
```

importing `visual_kind` from `demo_studio.beats`. In playwright_capture, also ensure the frame counter `n` keeps incrementing only for captured frames (existing behavior) — clip beats simply never appear in `frames_dir`.

- [ ] **Step 4: Run tests → PASS; full suite `python -m pytest tests -v` → PASS. Commit:**

```bash
git add src/demo_studio/playwright_capture.py src/demo_studio/chrome_capture.py tests/test_capture_skip.py
git commit -m "feat: capture engines skip clip-source beats"
```

---

### Task 4: Per-beat picture assembly + pipeline rewiring

**Files:**
- Modify: `src/demo_studio/capture.py` (`frames_to_mp4` gains optional `frames` param)
- Create: `src/demo_studio/assemble.py`
- Modify: `src/demo_studio/jobs.py` (`run_job` ordering: frames → narrate → assemble → polish → package)
- Modify: `src/demo_studio/cli.py` (`capture` defers picture for clip packs; `package` gains `--beats`)
- Modify: `scripts/run-demo.sh`, `scripts/run-demo.ps1` (pass `--beats "$BEATS"` to package)
- Test: `tests/test_assemble.py` (new)

**Interfaces:**
- Consumes: `visual_kind`, `resolve_clip_path` (Task 1); `clip_segment`, `probe_video` (Task 2); `frames_to_mp4` (extended); narration cues from `narrate_beats` (`cues[i]` ↔ `beats[i]`, each has `duration_ms`).
- Produces: `assemble_picture(data: dict, cues: list[dict], frames_dir: Path, job_dir: Path, *, pack_dir: Path, width: int, height: int) -> dict` → `{"segments": int, "picture": str, "total_s": float}` writing `job_dir/picture.mp4`; `concat_segments(ffmpeg: str, segs: list[Path], out: Path) -> None`.
- Contract: every capture beat must have ≥1 frame named `NN_<beat-id>.png|jpg` in `frames_dir` (playwright/chrome naming, Task 3); segment duration = cue `duration_ms/1000` (min 0.5 s).

- [ ] **Step 1: Extend `frames_to_mp4`** — signature gains `frames: list[Path] | None = None`; when provided, use it instead of the glob (`frames = frames or sorted([...glob...])`). Existing callers unaffected.

- [ ] **Step 2: Write the failing tests** — `tests/test_assemble.py`:

```python
import json
import shutil
import subprocess
import pytest
from pathlib import Path
from demo_studio.assemble import concat_segments


def test_concat_segments_argv(tmp_path, monkeypatch):
    from demo_studio import assemble
    calls = []
    monkeypatch.setattr(assemble.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd) or type("P", (), {"returncode": 0, "stderr": ""})())
    monkeypatch.setattr(shutil, "which", lambda n: "ffmpeg")
    segs = [tmp_path / "00_a.mp4", tmp_path / "01_b.mp4"]
    for s in segs:
        s.write_bytes(b"")
    concat_segments("ffmpeg", segs, tmp_path / "picture.mp4")
    cmd = " ".join(calls[0])
    assert "concat=n=2:v=1:a=1" in cmd and "-vsync" not in cmd


def test_assemble_picture_requires_frames(tmp_path):
    from demo_studio.assemble import assemble_picture
    data = {"version": 1, "product": "p", "beats": [{"id": "a", "narration": "x"}]}
    cues = [{"file": "a.wav", "duration_ms": 1000, "start_ms": 0, "end_ms": 1000}]
    with pytest.raises(RuntimeError, match="no frames for beat a"):
        assemble_picture(data, cues, tmp_path / "frames", tmp_path,
                         pack_dir=tmp_path, width=320, height=240)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_assemble_picture_still_plus_clip(tmp_path):
    from demo_studio.assemble import assemble_picture
    from demo_studio.clips import probe_video
    frames = tmp_path / "frames"
    frames.mkdir()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "color=c=red:s=320x240", "-frames:v", "1",
                    str(frames / "01_a.png")], check=True)
    clip = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=size=160x120:rate=30", "-t", "2",
                    "-c:v", "libx264", str(clip)], check=True)
    data = {"version": 1, "product": "p", "beats": [
        {"id": "a", "narration": "x"},
        {"id": "b", "narration": "y", "visual": {"kind": "clip", "file": "clip.mp4", "in_sec": 0.5, "out_sec": 1.5}},
    ]}
    cues = [{"file": "a.wav", "duration_ms": 1500, "start_ms": 0, "end_ms": 1500},
            {"file": "b.wav", "duration_ms": 2000, "start_ms": 1500, "end_ms": 3500}]
    res = assemble_picture(data, cues, frames, tmp_path, pack_dir=tmp_path, width=320, height=240)
    assert res["segments"] == 2
    info = probe_video(Path(res["picture"]))
    assert 3.0 <= info["duration_s"] <= 4.0  # 1.5s still + 2.0s clip segment
    assert info["width"] == 320
```

- [ ] **Step 3: Run → FAIL** (`No module named 'demo_studio.assemble'`).

- [ ] **Step 4: Implement `src/demo_studio/assemble.py`:**

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from demo_studio.beats import resolve_clip_path, visual_kind
from demo_studio.capture import frames_to_mp4
from demo_studio.clips import clip_segment


def concat_segments(ffmpeg: str, segs: list[Path], out: Path) -> None:
    cmd = [ffmpeg, "-y", "-v", "error"]
    for s in segs:
        cmd += ["-i", str(s)]
    labels = "".join(f"[{i}:v][{i}:a]" for i in range(len(segs)))
    cmd += [
        "-filter_complex", f"{labels}concat=n={len(segs)}:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "48000", str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"picture concat failed: {proc.stderr[-800:]}")


def assemble_picture(
    data: dict[str, Any],
    cues: list[dict[str, Any]],
    frames_dir: Path,
    job_dir: Path,
    *,
    pack_dir: Path,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Build picture.mp4 as per-beat segments aligned to narration cues."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not on PATH")
    beats = data.get("beats") or []
    if len(cues) != len(beats):
        raise RuntimeError(f"cue count {len(cues)} != beat count {len(beats)}")
    segs_dir = job_dir / "segments"
    segs_dir.mkdir(parents=True, exist_ok=True)
    segs: list[Path] = []
    total_s = 0.0
    for i, (beat, cue) in enumerate(zip(beats, cues)):
        bid = str(beat.get("id") or f"beat{i}")
        dur_s = max(0.5, float(cue.get("duration_ms") or 500) / 1000.0)
        seg = segs_dir / f"{i:02d}_{bid}.mp4"
        if visual_kind(beat) == "clip":
            src = resolve_clip_path(beat, pack_dir)
            if src is None or not src.is_file():
                raise RuntimeError(f"clip file missing for beat {bid}: {(beat.get('visual') or {}).get('file')}")
            v = beat.get("visual") or {}
            clip_segment(src, seg,
                         in_sec=float(v.get("in_sec") or 0.0),
                         out_sec=v.get("out_sec"),
                         width=width, height=height, target_dur_s=dur_s)
        else:
            beat_frames = sorted(frames_dir.glob(f"*_{bid}.png")) + sorted(frames_dir.glob(f"*_{bid}.jpg"))
            if not beat_frames:
                raise RuntimeError(f"no frames for beat {bid}")
            per = dur_s / len(beat_frames)
            frames_to_mp4(frames_dir, seg, width=width, height=height,
                          durations_sec=[per] * len(beat_frames), frames=beat_frames)
        segs.append(seg)
        total_s += dur_s
    picture = job_dir / "picture.mp4"
    concat_segments(ffmpeg, segs, picture)
    return {"segments": len(segs), "picture": str(picture), "total_s": total_s}
```

- [ ] **Step 5: Rewire `jobs.run_job`** (`src/demo_studio/jobs.py:106-148`). New order: (1) browser frame capture — keep engine dispatch but only call `frames_to_mp4` when NO clip beats exist; when clip beats exist set `meta["steps"]["capture"]["picture"] = "deferred"` and skip; (2) narrate (unchanged call, moved before assembly); (3) if deferred: `assemble_picture(data, narr["cues"], frames, job_dir, pack_dir=Path(meta["beats"]).parent, width=width, height=height)` and store result in `meta["steps"]["assemble"]`; (4) title-card polish (unchanged, runs on whichever picture.mp4 now exists); (5) studio compose only when `look_name == "studio"` AND no clip beats — when clip beats present and look was studio, record `meta["steps"]["look"] = {"look": "clean", "note": "studio look disabled for mixed packs (v1)"}` and use clean; (6) `mux_package` unchanged. `narrate_beats` already returns the full manifest — pass `narr["cues"]`.

- [ ] **Step 6: CLI parity.** In `cli.py`: `capture` handler — mirror the jobs rule (skip `frames_to_mp4` when clip beats present; print "picture assembly deferred to package --beats"). `package` parser gains `--beats PATH`; handler: if `--beats` given and `run_dir/picture.mp4` is absent, load beats + `run_dir/narration/narration.json` and call `assemble_picture(..., pack_dir=Path(beats).parent, ...)` before `mux_package`. In `scripts/run-demo.sh` change the package call to `demo-studio package "${PKG_ARGS[@]}" --beats "$BEATS"`; same flag addition in `scripts/run-demo.ps1`.

- [ ] **Step 7: Run new tests → PASS; full suite → PASS** (`python -m pytest tests -v`). Also smoke a pure-capture pack end-to-end if TTS sidecar is up: `./scripts/run-demo.sh alongfor` must behave exactly as before (its picture is built by `capture`, `--beats` path never triggers assembly because picture.mp4 exists).

- [ ] **Step 8: Commit**

```bash
git add src/demo_studio/capture.py src/demo_studio/assemble.py src/demo_studio/jobs.py src/demo_studio/cli.py scripts/run-demo.sh scripts/run-demo.ps1 tests/test_assemble.py
git commit -m "feat: per-beat picture assembly aligned to narration cues for clip packs"
```

---

### Task 5: Clip windows — contact sheets + user gate

**Files:**
- Create: `outputs/clip-review/` (artifacts, not committed)

**Interfaces:**
- Consumes: candidate clips named in `demos/ai-update-2026-11/SEGMENTS.md`; `ffmpeg` thumbnails.
- Produces: user-confirmed `(file, in_sec, out_sec)` triples per segment — the input for Task 6's beats file.

- [ ] **Step 1: Generate contact sheets** for each candidate clip in SEGMENTS.md (skip files >2 GB or probe them at coarser interval):

```bash
mkdir -p outputs/clip-review
# per clip: 1 thumbnail every ~15s, tiled, timestamped
ffmpeg -y -v error -i "$CLIP" -vf "fps=1/15,scale=480:-1,drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=24:fontcolor=yellow:box=1,tile=4x5" -frames:v 1 "outputs/clip-review/<slug>-sheet.png"
```

(For very long clips produce multiple sheets with `-ss`/segmented tiles so timestamps stay readable.)

- [ ] **Step 2: Present sheets to the user** (list of `outputs/clip-review/*.png` + the SEGMENTS.md candidate table) and ask them to confirm/adjust the window per segment. **Gate: do not proceed until windows are confirmed.**

- [ ] **Step 3: Record confirmed windows** by appending a `## Confirmed windows` table (segment, file, in_sec, out_sec, note) to `demos/ai-update-2026-11/SEGMENTS.md`. Commit: `git add demos/ai-update-2026-11/SEGMENTS.md && git commit -m "docs: confirmed clip windows for ai-update-2026-11"`.

---

### Task 6: Beats file — narration + validation

**Files:**
- Create: `demos/ai-update-2026-11/demo.beats.json`
- Reference: `demos/ai-update-2026-11/SEGMENTS.md`, `outputs/_research/github-sweep-2026-11-26.md`, `outputs/_research/x-posts-sample-2026-11-26.md`

**Interfaces:**
- Consumes: schema with `visual` (Task 1), validation (Task 1).
- Produces: the pack consumed by Task 7's run. Structure: `{"version": 1, "product": "ai-update-2026-11", "title": "...", "capture": {"width": 1920, "height": 1080}, "beats": [...]}`. Beat ids: `intro`, `<segment>-<sub>` (e.g. `ark-dayzero`, `ark-playthrough`), `outro`. Clip beats carry `visual.kind="clip"` with Task-5 windows; capture beats for segments 1, 2, 6 use actions against `ark.happymonkey.ai`, `realms.happymonkey.ai`, `alongfor.happymonkey.ai` (reuse action patterns from `demos/mrpg-realms/demo.beats.json`).

- [ ] **Step 1: Draft narration** — one paragraph per beat, 2–4 beats per segment, target ≈17 min total (TTS ≈150 wpm → ≈2,550 words; intro/outro ≈60–90 words each). Voice rules: short sentences, no filler, concrete numbers from the evidence files ("325 commits", "62 ms to 0.08 ms per frame", "5-second shots in about two minutes on an RTX 5090"). Segment 6 is the self-referential closer: state that this video's visuals were produced by demo-studio itself.

- [ ] **Step 2: Write `demo.beats.json`** with all beats (intro montage uses clip beats pointing at the confirmed windows of later segments; outro is a capture beat on alongfor or a clip, whichever Task 5 confirms).

- [ ] **Step 3: Validate** — `demo-studio validate demos/ai-update-2026-11/demo.beats.json` → clean (schema + visuals). Fix and re-run until green.

- [ ] **Step 4: Commit**

```bash
git add demos/ai-update-2026-11/demo.beats.json
git commit -m "feat: ai-update-2026-11 reel beats — 6 segments, clip + capture mix"
```

---

### Task 7: Full run, review, publish draft

**Files:**
- Generated: `outputs/ai-update-2026-11-<stamp>/` (frames, narration, segments, picture.mp4, demo.mp4, review.html)

**Interfaces:**
- Consumes: everything above; TTS sidecar (Pocket `:8000` or Piper `:8010`).
- Produces: reviewed `demo.mp4` + publication draft JSON.

- [ ] **Step 1: Preflight** — activate venv, `demo-studio doctor` (ffmpeg + TTS provider health). If no sidecar is up, start the repo's documented TTS provider (see docs/USAGE.md) before continuing.

- [ ] **Step 2: Run** — `./scripts/run-demo.sh demos/ai-update-2026-11/demo.beats.json --base-url https://ark.happymonkey.ai` (ark/realms/alongfor URLs are absolute in beat actions; base URL satisfies the runner's env check). Expect: capture visits only capture beats, narrate writes per-beat WAVs, package assembles picture via `--beats` then muxes.

- [ ] **Step 3: Review gate** — open the printed `review.html`; walk each segment against SEGMENTS.md intent. Iterate by editing beats (windows, narration, beat order) and re-running. **Do not proceed until the user signs off on review.html.**

- [ ] **Step 4: Publish draft only** — `demo-studio publish-draft <run_dir> --platform youtube` with a proposed title/description; hand the draft + `demo.mp4` path to the user. Never upload (AGENTS.md rule).

- [ ] **Step 5: Commit run notes** — append `## Run log` (run dir, duration, look, iteration count) to `demos/ai-update-2026-11/SEGMENTS.md` and commit.

---

## Self-review record

- Spec coverage: schema/validation (T1), segment builder incl. tpad + silent track (T2), engine skip (T3), per-beat assembly + concat + job/CLI/script rewiring (T4), clip inventory/contact sheets gate (T5), beats/pack (T6), run/review/publish-draft (T7). Spec's "doctor clip-path check" intentionally skipped — doctor already requires ffmpeg, no new dependency exists (YAGNI).
- Placeholders: none; every code step contains full code; Task 5's `$CLIP`/`<slug>` are loop variables defined in the step text.
- Type consistency: `visual_kind`/`resolve_clip_path` (T1) used identically in T3/T4; `clip_segment` kwargs match between T2 definition and T4 call; `assemble_picture` signature identical in T4 definition, jobs wiring, and CLI wiring; cue key `duration_ms` verified against `narrate.py`.
