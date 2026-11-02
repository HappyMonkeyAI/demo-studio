#!/usr/bin/env bash
# Probe OpenScreen CLI on Linux Mint (DevHost). Run on the Mint host.
set -euo pipefail
DIR="${HOME}/tools/openscreen-probe"
APP="${DIR}/Openscreen-Linux-2.1.2.AppImage"
cd "$DIR"

echo "=== host ==="
uname -a
head -3 /etc/os-release
echo "DISPLAY=${DISPLAY:-<empty>} XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-<empty>}"

echo
echo "=== CLI help (already verified path) ==="
"$APP" --no-sandbox help >/dev/null
echo "help: ok"

echo
echo "=== sources under xvfb ==="
rm -f sources.json
set +e
xvfb-run -a "$APP" --no-sandbox sources -o sources.json
SRC_EXIT=$?
set -e
echo "sources_exit=$SRC_EXIT"
if [[ -f sources.json ]]; then
  python3 -c 'import json; d=json.load(open("sources.json")); print("keys", sorted(d.keys())); print("displays", d.get("displays"))'
else
  echo "sources.json missing"
fi

echo
echo "=== minimal export under xvfb ==="
ffmpeg -y -f lavfi -i color=c=0x336699:s=1280x720:d=2 -c:v libx264 -pix_fmt yuv420p clip.mp4 >/dev/null 2>&1
python3 - <<'PY'
from pathlib import Path
import json
p = Path(".").resolve() / "clip.mp4"
Path("tiny.openscreen").write_text(
    json.dumps({"version": 2, "media": {"screenVideoPath": str(p)}, "editor": {}}, indent=2),
    encoding="utf-8",
)
print("wrote tiny.openscreen ->", p)
PY
rm -f tiny-out.mp4 export.out export.err
set +e
xvfb-run -a "$APP" --no-sandbox export tiny.openscreen -o tiny-out.mp4 --quality medium --fps 30 --json >export.out 2>export.err
EXP_EXIT=$?
set -e
echo "export_exit=$EXP_EXIT"
tail -n 5 export.out || true
tail -n 8 export.err || true
ls -lh tiny-out.mp4 2>/dev/null || echo "tiny-out.mp4 missing"

echo
echo "=== record note ==="
echo "Linux record needs a real desktop session + ScreenCast portal picker (not unattended over SSH)."
echo "Done."
