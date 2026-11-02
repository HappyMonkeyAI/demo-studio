# demo-studio

Re-runnable **product walkthrough → MP4** for YouTube/X.

Drive a real app (Playwright capture; optional BrowserOS NEO), narrate with Pocket TTS or Piper, mux with ffmpeg. Packaging conventions follow `qwen-video-studio`. Picture comes from the live product — not generative UI.

**License:** [MIT](LICENSE)

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,capture]"
playwright install chromium   # for capture --engine playwright
```

Needs `ffmpeg` on PATH, plus a TTS sidecar: Pocket TTS (`POCKET_TTS_URL`, default `:8000`) or Piper (`DEMO_TTS_PROVIDER=piper`, `PIPER_TTS_URL`, default `:8010`).

## CLI

```bash
demo-studio doctor
# Public product pack (AlongFor)
export DEMO_BASE_URL=https://alongfor.happymonkey.ai
demo-studio validate demos/alongfor/demo.beats.json
demo-studio capture demos/alongfor/demo.beats.json --run-dir outputs/alongfor-run --engine playwright
demo-studio narrate demos/alongfor/demo.beats.json outputs/alongfor-run   # add --provider piper if configured
demo-studio package outputs/alongfor-run --title-card "AlongFor" --subtitle "event companion"

# Self-hosted CMS pack (throwaway EmDash only — never confidential pilot data)
export DEMO_BASE_URL=http://127.0.0.1:4335
demo-studio validate demos/astro-cms/demo.beats.json
demo-studio capture demos/astro-cms/demo.beats.json --run-dir outputs/my-run --engine playwright
```

Open `outputs/<run>/review.html`.

Re-run gate (twice): `DEMO_BASE_URL=… bash scripts/rerun-gate.sh`

## Layout

| Path | Role |
|---|---|
| `schema/beat.schema.json` | Beat contract |
| `demos/alongfor/` | Public AlongFor walkthrough |
| `demos/mrpg-realms/` | MRPG Realms join screen + player wiki |
| `demos/astro-cms/` | Throwaway EmDash / migrate walkthrough |
| `demos/<product>/` | Other product beat packs |
| `src/demo_studio/` | CLI + TTS + capture + package |
| `outputs/` | Run artifacts (gitignored media) |
| `docs/plans/2026-11-02-demo-studio-roadmap.md` | Full roadmap |

## Non-goals (v0)

Recordly runtime · AIQA desktop · sandbox VM · generative fake UI · auto-publish

See [CONTEXT.md](CONTEXT.md) and [adr/0001-demo-studio-scope.md](adr/0001-demo-studio-scope.md).
