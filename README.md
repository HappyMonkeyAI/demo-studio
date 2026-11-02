# demo-studio

Re-runnable **product walkthrough → MP4** for YouTube/X.

Drive a real app (BrowserOS NEO + Playwright capture), narrate with Pocket TTS, mux with ffmpeg. Packaging conventions follow `qwen-video-studio`. Picture comes from the live product — not Wan/ComfyUI.

**Home host:** DevHost `192.168.5.215` (`/home/stephen/projects/demo-studio`).

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,capture]"
playwright install chromium   # for capture --engine playwright
```

## CLI

```bash
demo-studio doctor
demo-studio validate demos/astro-cms/demo.beats.json
export DEMO_BASE_URL=http://127.0.0.1:4335   # throwaway only — never client pilot data
demo-studio dry-run demos/astro-cms/demo.beats.json --execute-neo
demo-studio capture demos/astro-cms/demo.beats.json --run-dir outputs/my-run --engine playwright
demo-studio narrate demos/astro-cms/demo.beats.json outputs/my-run
demo-studio package outputs/my-run --title-card "astro-cms" --subtitle "migrate · go-live · agents"
```

Open `outputs/my-run/review.html`.

Re-run gate (twice): `DEMO_BASE_URL=… bash scripts/rerun-gate.sh`

## Layout

| Path | Role |
|---|---|
| `schema/beat.schema.json` | Beat contract |
| `demos/<product>/` | Product beat packs |
| `src/demo_studio/` | CLI + TTS + capture + package |
| `outputs/` | Run artifacts (gitignored media) |
| `docs/plans/2026-11-02-demo-studio-roadmap.md` | Full roadmap |

## Non-goals (v0)

Recordly runtime · AIQA desktop · sandbox VM · generative fake UI · auto-publish

See [CONTEXT.md](CONTEXT.md) and [adr/0001-demo-studio-scope.md](adr/0001-demo-studio-scope.md).
