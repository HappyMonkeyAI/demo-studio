from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from demo_studio.beats import load_beats, summarize, validate_beats
from demo_studio.capture import frames_to_mp4
from demo_studio.chrome_capture import capture_beat_frames
from demo_studio.doctor import run_doctor
from demo_studio.narrate import narrate_beats
from demo_studio.neo_script import compile_neo_run_js
from demo_studio.package_run import mux_package
from demo_studio.playwright_capture import capture_beat_frames_playwright
from demo_studio.polish import burn_title_card
from demo_studio.preflight import resolve_base, run_python_asserts, write_run_log


def _cmd_doctor(_: argparse.Namespace) -> int:
    report = run_doctor()
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.beats)
    data = load_beats(path)
    errors = validate_beats(data)
    if errors:
        print(f"INVALID {path}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"OK {path}")
    print(summarize(data))
    return 0


def _new_run_dir(root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = root / "outputs" / f"run-{stamp}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cmd_dry_run(args: argparse.Namespace) -> int:
    path = Path(args.beats)
    data = load_beats(path)
    errors = validate_beats(data)
    if errors:
        print(f"INVALID {path}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    base = resolve_base(data, dict(os.environ))
    run_dir = Path(args.out) if args.out else _new_run_dir(Path.cwd())
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"run_dir={run_dir}")
    print(summarize(data))
    print(f"base_url={'set:' + base if base else 'UNSET'}")

    neo_js = compile_neo_run_js(data, base_url=base or "http://127.0.0.1:0")
    neo_path = run_dir / "neo-run.js"
    neo_path.write_text(neo_js, encoding="utf-8")
    print(f"wrote {neo_path}")

    http_results: list[dict] = []
    http_ok = True
    if base:
        http_results = run_python_asserts(data, base)
        for r in http_results:
            status = "PASS" if r.get("ok") else "FAIL"
            print(f"http_ok {status} beat={r.get('beat')} url={r.get('url')} status={r.get('status')}")
            if not r.get("ok"):
                http_ok = False
    else:
        print("warning: DEMO_BASE_URL unset — skipped http_ok asserts", file=sys.stderr)

    log = {
        "command": "dry-run",
        "beats": str(path),
        "base_url": base,
        "neo_script": str(neo_path),
        "http_asserts": http_results,
        "execute_neo": bool(args.execute_neo),
        "neo_status": "not_run",
    }

    if args.execute_neo:
        if not base:
            print("error: --execute-neo requires DEMO_BASE_URL", file=sys.stderr)
            log["neo_status"] = "aborted_no_base"
            write_run_log(run_dir / "run-log.json", log)
            return 2
        if not http_ok:
            print("error: http_ok asserts failed; refusing NEO run", file=sys.stderr)
            log["neo_status"] = "aborted_http_assert"
            write_run_log(run_dir / "run-log.json", log)
            return 1
        print(
            "NEO: invoke BrowserOS neo MCP `run` with the script at:\n"
            f"  {neo_path}\n"
            f"  inputs: {{ \"baseUrl\": {base!r} }}\n"
            "Keep total waitForTime under ~25s or split the run (neo hard cap 30s)."
        )
        log["neo_status"] = "script_ready"
        (run_dir / "NEO_EXECUTE.md").write_text(
            f"# Execute with BrowserOS neo\n\n"
            f"Source: `{neo_path.name}` · inputs `baseUrl={base}`\n",
            encoding="utf-8",
        )

    write_run_log(run_dir / "run-log.json", log)
    if base and not http_ok:
        return 1
    print("\ndry-run complete.")
    return 0


def _cmd_capture(args: argparse.Namespace) -> int:
    data = load_beats(Path(args.beats))
    errors = validate_beats(data)
    if errors:
        print("INVALID", file=sys.stderr)
        return 1
    base = resolve_base(data, dict(os.environ))
    if not base:
        print("error: DEMO_BASE_URL required for capture", file=sys.stderr)
        return 2
    run_dir = Path(args.run_dir) if args.run_dir else _new_run_dir(Path.cwd())
    frames = run_dir / "frames"
    cap = data.get("capture") or {}
    width = int(cap.get("width") or 1920)
    height = int(cap.get("height") or 1080)
    engine = args.engine
    try:
        if engine == "auto":
            try:
                written = capture_beat_frames_playwright(data, base, frames, width=width, height=height)
                engine = "playwright"
            except Exception as playwright_exc:  # noqa: BLE001
                print(f"playwright capture failed ({playwright_exc}); trying chrome…", file=sys.stderr)
                written = capture_beat_frames(data, base, frames, width=width, height=height)
                engine = "chrome"
        elif engine == "playwright":
            written = capture_beat_frames_playwright(data, base, frames, width=width, height=height)
        else:
            written = capture_beat_frames(data, base, frames, width=width, height=height)
        picture = frames_to_mp4(
            frames,
            run_dir / "picture.mp4",
            fps=int(args.fps),
            width=width,
            height=height,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"engine": engine, "frames": [str(p) for p in written], "picture": picture}, indent=2))
    return 0


def _cmd_frames_to_mp4(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    frames = Path(args.frames) if args.frames else run_dir / "frames"
    out = Path(args.out) if args.out else run_dir / "picture.mp4"
    try:
        result = frames_to_mp4(frames, out, fps=args.fps, width=args.width, height=args.height)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_narrate(args: argparse.Namespace) -> int:
    data = load_beats(Path(args.beats))
    errors = validate_beats(data)
    if errors:
        print(f"INVALID", file=sys.stderr)
        return 1
    run_dir = Path(args.run_dir)
    narr_dir = run_dir / "narration"
    try:
        manifest = narrate_beats(data, narr_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2)[:2000])
    print(f"wrote {narr_dir / 'narration.json'}")
    return 0


def _cmd_package(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    try:
        if args.title_card:
            picture = run_dir / "picture.mp4"
            if picture.is_file():
                polished = run_dir / "picture.polished.mp4"
                burn_title_card(picture, polished, title=args.title_card, subtitle=args.subtitle or "")
                polished.replace(picture)
        manifest = mux_package(run_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="demo-studio", description="Product demo video orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_doctor = sub.add_parser("doctor", help="Check ffmpeg + Pocket TTS")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_validate = sub.add_parser("validate", help="Validate beat file")
    p_validate.add_argument("beats")
    p_validate.set_defaults(func=_cmd_validate)

    p_dry = sub.add_parser("dry-run", help="Plan beats, emit neo-run.js, http_ok checks")
    p_dry.add_argument("beats")
    p_dry.add_argument("--execute-neo", action="store_true")
    p_dry.add_argument("--out", help="Existing or new run directory")
    p_dry.set_defaults(func=_cmd_dry_run)

    p_cap = sub.add_parser("capture", help="Screenshot frames + silent picture.mp4")
    p_cap.add_argument("beats")
    p_cap.add_argument("--run-dir", dest="run_dir")
    p_cap.add_argument("--fps", type=int, default=2)
    p_cap.add_argument(
        "--engine",
        choices=("auto", "playwright", "chrome"),
        default="auto",
        help="auto tries Playwright then Chrome",
    )
    p_cap.set_defaults(func=_cmd_capture)

    p_frames = sub.add_parser("frames-to-mp4", help="Assemble frames/ into silent picture.mp4")
    p_frames.add_argument("run_dir")
    p_frames.add_argument("--frames", help="Frames directory (default: <run_dir>/frames)")
    p_frames.add_argument("--out", help="Output mp4 (default: <run_dir>/picture.mp4)")
    p_frames.add_argument("--fps", type=int, default=2)
    p_frames.add_argument("--width", type=int, default=1920)
    p_frames.add_argument("--height", type=int, default=1080)
    p_frames.set_defaults(func=_cmd_frames_to_mp4)

    p_narr = sub.add_parser("narrate", help="Pocket TTS per beat into <run_dir>/narration")
    p_narr.add_argument("beats")
    p_narr.add_argument("run_dir")
    p_narr.set_defaults(func=_cmd_narrate)

    p_pkg = sub.add_parser("package", help="Mux picture+voice → demo.mp4 + review.html")
    p_pkg.add_argument("run_dir")
    p_pkg.add_argument("--title-card", dest="title_card", help="Optional opening title text")
    p_pkg.add_argument("--subtitle", default="", help="Optional title-card subtitle")
    p_pkg.set_defaults(func=_cmd_package)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
