# demo-studio

Re-runnable **product walkthrough → MP4** for YouTube/X.

Drive a real app (Playwright capture; optional BrowserOS NEO), narrate with Pocket TTS or Piper, mux with ffmpeg. Packaging conventions follow `qwen-video-studio`. Picture comes from the live product — not generative UI.

**Start here:** [QUICKSTART.md](QUICKSTART.md) · [docs/USAGE.md](docs/USAGE.md) · [ROADMAP.md](ROADMAP.md) (incl. Recordly-style polish + AIQA) · [SPEC.md](SPEC.md) · [TASKS.md](TASKS.md) · [MCP.md](MCP.md) · [LINKS.md](LINKS.md)

```bash
./install.sh && source .venv/bin/activate
./scripts/run-demo.sh alongfor    # → outputs/.../review.html + demo.mp4
```

**License:** [MIT](LICENSE)

## Install

```bash
# macOS / Linux
./install.sh          # checks Python/ffmpeg, creates .venv, installs package + offers Chromium
# Windows (PowerShell)
.\install.ps1
```

Both scripts accept `-y` / `-Yes` to auto-accept prompts, plus `--skip-ffmpeg` / `-SkipFfmpeg` and `--skip-playwright` / `-SkipPlaywright`.

Manual equivalent:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev,capture]"
playwright install chromium   # for capture --engine playwright
```

Needs `ffmpeg` on PATH, plus a TTS sidecar: Pocket TTS (`POCKET_TTS_URL`, default `:8000`) or Piper (`DEMO_TTS_PROVIDER=piper`, `PIPER_TTS_URL`, default `:8010`). TTS is not auto-installed — start a sidecar before `narrate`.

## CLI

One-shot (recommended):

```bash
./scripts/run-demo.sh alongfor              # or: .\scripts\run-demo.ps1 alongfor
./scripts/run-demo.sh mrpg-realms --provider piper
```

Step by step:

```bash
demo-studio doctor
export DEMO_BASE_URL=https://alongfor.happymonkey.ai
demo-studio validate demos/alongfor/demo.beats.json
demo-studio capture demos/alongfor/demo.beats.json --run-dir outputs/alongfor-run --engine playwright
demo-studio narrate demos/alongfor/demo.beats.json outputs/alongfor-run   # add --provider piper if configured
demo-studio package outputs/alongfor-run --title-card "AlongFor" --subtitle "event companion"
```

Open `outputs/<run>/review.html`. Self-hosted CMS: set `DEMO_BASE_URL` to a **throwaway** EmDash only — never confidential pilot data.

Re-run gate (twice): `DEMO_BASE_URL=… bash scripts/rerun-gate.sh`

## Layout

| Path | Role |
|---|---|
| `QUICKSTART.md` | 5-minute first video |
| `docs/USAGE.md` | Beat anatomy, env, agent checklist |
| `SPEC.md` / `TASKS.md` / `ROADMAP.md` | Acceptance, board, phased plan |
| `LINKS.md` / `MCP.md` | URLs + tool routing |
| `schema/beat.schema.json` | Beat contract |
| `scripts/run-demo.sh` / `.ps1` | One-shot pipeline |

| `demos/alongfor/` | Public AlongFor walkthrough |
| `demos/mrpg-realms/` | MRPG Realms join screen + player wiki |
| `demos/astro-cms/` | Throwaway EmDash / migrate walkthrough |
| `demos/<product>/` | Other product beat packs |
| `src/demo_studio/` | CLI + TTS + capture + package |
| `outputs/` | Run artifacts (gitignored media) |
| `docs/plans/2026-11-02-demo-studio-roadmap.md` | Full roadmap |

## Non-goals (v0)

Recordly **runtime** (GUI/AGPL) · AIQA desktop before a real desktop beat · sandbox VM · generative fake UI · auto-publish

Post-MVP (planned): Recordly-**inspired** zooms/transitions in our ffmpeg pipeline, then AIQA/UIQA when a demo leaves the browser — see [ROADMAP.md](ROADMAP.md) v1.0–v1.1 and SPEC S7–S8.

See [CONTEXT.md](CONTEXT.md) and [adr/0001-demo-studio-scope.md](adr/0001-demo-studio-scope.md).
