# Quick start

Goal: turn a live product URL into a narrated `demo.mp4` you can review in a browser.

```text
beats JSON  →  capture (screens)  →  narrate (TTS)  →  package (mux)  →  review.html + demo.mp4
```

The **beat file** is the source of truth. Edit beats; re-run the pipeline. Do not hand-edit recording scripts.

## 1. Install

```bash
./install.sh          # macOS / Linux
.\install.ps1         # Windows PowerShell
```

Activate the venv, then confirm:

```bash
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
demo-studio doctor
```

You need **ffmpeg** on PATH and a **TTS sidecar** before `narrate` (Pocket on `:8000` or Piper on `:8010`).

## 2. First video (public AlongFor — no local site)

```bash
./scripts/run-demo.sh alongfor
# Windows: .\scripts\run-demo.ps1 alongfor
```

That sets `DEMO_BASE_URL`, validates, captures with Playwright, narrates, and packages.

Open the printed `review.html`. The MP4 is `demo.mp4` next to it.

## 3. Other built-in packs

| Pack | URL | Command |
|---|---|---|
| `alongfor` | https://alongfor.happymonkey.ai | `./scripts/run-demo.sh alongfor` |
| `mrpg-realms` | https://realms.happymonkey.ai | `./scripts/run-demo.sh mrpg-realms` |
| `astro-cms` | your throwaway EmDash | `DEMO_BASE_URL=http://127.0.0.1:4335 ./scripts/run-demo.sh astro-cms` |

Never point packs at confidential pilot / `client-data` trees.

## 4. Your own product

1. Copy `demos/alongfor/` → `demos/<product>/`
2. Edit `demo.beats.json` (narration + actions + asserts)
3. `demo-studio validate demos/<product>/demo.beats.json`
4. `./scripts/run-demo.sh <product> --base-url https://your.app`

See [docs/USAGE.md](docs/USAGE.md) for beat anatomy, env vars, and agent checklist.
