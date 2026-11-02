# Usage

## Mental model

| Piece | Role |
|---|---|
| `demos/<product>/demo.beats.json` | Script: narration, clicks, waits, asserts |
| `DEMO_BASE_URL` | Live product under demo (required) |
| `capture` | Drive the site (Playwright) → frames + silent `picture.mp4` |
| `narrate` | TTS each beat → `narration/*.wav` |
| `package` | Mux → `demo.mp4` + captions + `review.html` |
| Human | Watch `review.html` before publishing |

Success = the **same beat file** yields a recognisably similar video on a second run.

## Pipeline (manual)

```bash
export DEMO_BASE_URL=https://alongfor.happymonkey.ai
demo-studio validate demos/alongfor/demo.beats.json
demo-studio capture demos/alongfor/demo.beats.json --run-dir outputs/alongfor-run --engine playwright
demo-studio narrate demos/alongfor/demo.beats.json outputs/alongfor-run   # --provider piper
demo-studio package outputs/alongfor-run --title-card "AlongFor" --subtitle "event companion"
# Optional Recordly-inspired motion (ffmpeg only):
demo-studio package outputs/alongfor-run --look product-zoom --title-card "AlongFor"
```

Or one shot: `./scripts/run-demo.sh alongfor --look product-zoom`

Looks: `clean` (default) · `product-zoom` (~8% center push-in). See [recordly-polish-notes.md](recordly-polish-notes.md).

Job API (same steps, tracked under `outputs/job-*`):

```bash
demo-studio job-create demos/alongfor/demo.beats.json --base-url https://alongfor.happymonkey.ai
demo-studio job-run <job_id> --engine playwright --title-card "AlongFor"
```

## Beat file (minimal)

```json
{
  "version": 1,
  "product": "my-app",
  "title": "My app walkthrough",
  "base_url_env": "DEMO_BASE_URL",
  "capture": { "width": 1280, "height": 900, "fps": 30 },
  "beats": [
    {
      "id": "hook",
      "narration": "Say what the product is in one breath.",
      "actions": [
        { "type": "navigate", "path": "/" },
        { "type": "wait_text", "text": "Visible heading" },
        { "type": "wait_ms", "ms": 1000 }
      ],
      "assert": [
        { "type": "http_ok", "path": "/" },
        { "type": "page_has_text", "value": "Visible heading" }
      ],
      "pause_ms": 600,
      "min_narration_ms": 5000
    }
  ]
}
```

Common actions: `navigate`, `wait_text`, `wait_ms`, `click_text` (`optional: true` for cookie banners), `fill` (value from `env`), `scroll`, `press`.

Contract: `schema/beat.schema.json`. Prefer editing beats over writing one-off recorder scripts.

## Environment

| Var | Default | Purpose |
|---|---|---|
| `DEMO_BASE_URL` | (required) | Subject site |
| `POCKET_TTS_URL` | `http://127.0.0.1:8000` | Pocket TTS |
| `PIPER_TTS_URL` | `http://127.0.0.1:8010` | Piper TTS |
| `DEMO_TTS_PROVIDER` | `pocket` | `pocket` or `piper` |
| `ADMIN_PASSWORD` etc. | — | Fill actions with `"env": "…"` (load via `.local/*.env`) |

Secrets stay in env / `.local/` — never in beat JSON committed to git.

## Outputs

```text
outputs/<run>/
  frames/          # screenshots per beat
  picture.mp4      # silent capture
  narration/       # per-beat audio
  demo.mp4         # final mux
  review.html      # human gate
  captions.vtt
```

## Agent checklist

1. Read [QUICKSTART.md](../QUICKSTART.md) and this file before inventing a new flow.
2. Prefer `./scripts/run-demo.sh <pack>` or `job-create` / `job-run`.
3. Change behaviour by editing `demos/<product>/demo.beats.json`, then re-validate.
4. Never target confidential pilot / `client-data` URLs.
5. Fail closed on assert failures — do not “force” a ship with wrong clicks.
6. After packaging, point a human at `review.html` (do not auto-publish).

## Troubleshooting

| Symptom | Check |
|---|---|
| `doctor` not ok | ffmpeg on PATH; Pocket TTS up (or use `--provider piper`) |
| capture timeout on click | make action `optional: true`, or fix visible `wait_text` |
| empty / wrong screen | `DEMO_BASE_URL` wrong; cookie banner blocking; assert text hidden |
| narrate fails | TTS sidecar down; try the other provider |
| package fails | missing `picture.mp4` or narration wavs; re-run capture/narrate |
