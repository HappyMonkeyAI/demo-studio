# demo-studio

Re-runnable **product walkthrough → MP4** for YouTube/X demos.

Drive a real app (BrowserOS NEO), capture the UI, narrate with Pocket TTS, mux with ffmpeg. Packaging conventions follow [`qwen-video-studio`](../qwen-video-studio) (beats, review package). Picture comes from the live product — not Wan/ComfyUI.

**Home host:** DevHost `192.168.5.215` (`/home/stephen/projects/demo-studio`).

## Non-goals (v0)

- Recordly as runtime (polish inspiration only)
- AIQA / full desktop MCP
- Sandbox VM
- Generative fake UI
- Auto-publish to X/YouTube

## Quick start

```bash
cd /home/stephen/projects/demo-studio   # or local clone
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
demo-studio doctor
demo-studio validate demos/astro-cms/demo.beats.json
demo-studio dry-run demos/astro-cms/demo.beats.json
```

Phases: validate → dry-run (NEO acts, no capture) → capture → TTS+mux → review package.

## Layout

| Path | Role |
|---|---|
| `schema/beat.schema.json` | Beat file contract |
| `demos/<product>/` | Product fixtures + beat lists |
| `src/demo_studio/` | CLI + loaders + Pocket TTS client |
| `outputs/` | Run artifacts (gitignored content) |

See [CONTEXT.md](CONTEXT.md) and [adr/0001-demo-studio-scope.md](adr/0001-demo-studio-scope.md).
