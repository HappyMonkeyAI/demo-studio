# Demo pack: alongfor

Public product: [AlongFor](https://alongfor.happymonkey.ai) (Happy Monkey — Devon event companion).

```bash
export DEMO_BASE_URL=https://alongfor.happymonkey.ai
demo-studio validate demos/alongfor/demo.beats.json
demo-studio capture demos/alongfor/demo.beats.json --run-dir outputs/alongfor-run --engine playwright
demo-studio narrate demos/alongfor/demo.beats.json outputs/alongfor-run --provider piper   # or pocket
demo-studio package outputs/alongfor-run --title-card "AlongFor" --subtitle "event companion · Devon"
```

Beats stay on public surfaces (feed, map toggle, create form, about). Sign-in / publish is shown but not completed in this pack.
