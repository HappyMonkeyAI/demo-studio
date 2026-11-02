#!/usr/bin/env bash
# demo-studio local setup: check deps, offer installs, create venv + package.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

YES=0
SKIP_FFMPEG=0
SKIP_PLAYWRIGHT=0

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

  -y, --yes              Accept install prompts without asking
  --skip-ffmpeg          Do not install ffmpeg if missing
  --skip-playwright      Skip Playwright Chromium browser download
  -h, --help             Show this help
EOF
}

while (($#)); do
  case "$1" in
    -y|--yes) YES=1; shift ;;
    --skip-ffmpeg) SKIP_FFMPEG=1; shift ;;
    --skip-playwright) SKIP_PLAYWRIGHT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

ok()   { printf '  [ok]   %s\n' "$*"; }
warn() { printf '  [warn] %s\n' "$*"; }
fail() { printf '  [fail] %s\n' "$*"; }
info() { printf '  [..]   %s\n' "$*"; }

ask() {
  local prompt="$1"
  if (( YES )); then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    return 1
  fi
  local reply
  read -r -p "  Install? ${prompt} [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
}

have() { command -v "$1" >/dev/null 2>&1; }

python_major_minor() {
  "$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null
}

python_ok() {
  local ver
  ver="$(python_major_minor "$1" || true)"
  [[ -n "$ver" ]] || return 1
  local major="${ver%%.*}"
  local minor="${ver#*.}"
  (( major > 3 || (major == 3 && minor >= 11) ))
}

pick_python() {
  local cand
  for cand in python3.13 python3.12 python3.11 python3 python; do
    if have "$cand" && python_ok "$cand"; then
      echo "$cand"
      return 0
    fi
  done
  return 1
}

offer_python() {
  fail "Python >= 3.11 not found on PATH"
  if have brew; then
    if ask "brew install python@3.12"; then
      brew install python@3.12
      return 0
    fi
  elif have apt-get; then
    if ask "sudo apt-get install -y python3 python3-venv python3-pip"; then
      sudo apt-get update
      sudo apt-get install -y python3 python3-venv python3-pip
      return 0
    fi
  elif have dnf; then
    if ask "sudo dnf install -y python3 python3-pip"; then
      sudo dnf install -y python3 python3-pip
      return 0
    fi
  elif have pacman; then
    if ask "sudo pacman -S --needed python python-pip"; then
      sudo pacman -S --needed python python-pip
      return 0
    fi
  fi
  warn "Install Python 3.11+ from https://www.python.org/downloads/ then re-run."
  return 1
}

offer_ffmpeg() {
  fail "ffmpeg not on PATH (needed for mux / package)"
  if (( SKIP_FFMPEG )); then
    warn "Skipping ffmpeg (--skip-ffmpeg)"
    return 0
  fi
  if have brew; then
    if ask "brew install ffmpeg"; then
      brew install ffmpeg
      return 0
    fi
  elif have apt-get; then
    if ask "sudo apt-get install -y ffmpeg"; then
      sudo apt-get update
      sudo apt-get install -y ffmpeg
      return 0
    fi
  elif have dnf; then
    if ask "sudo dnf install -y ffmpeg"; then
      sudo dnf install -y ffmpeg
      return 0
    fi
  elif have pacman; then
    if ask "sudo pacman -S --needed ffmpeg"; then
      sudo pacman -S --needed ffmpeg
      return 0
    fi
  fi
  warn "Install ffmpeg manually: https://ffmpeg.org/download.html"
  return 1
}

echo "=== demo-studio install ==="
echo "Root: $ROOT"
echo

echo "1) Python"
PY=""
if PY="$(pick_python)"; then
  ok "$PY $(python_major_minor "$PY")"
else
  offer_python || exit 1
  PY="$(pick_python)" || { fail "Still no Python >= 3.11"; exit 1; }
  ok "$PY $(python_major_minor "$PY")"
fi

echo
echo "2) Virtualenv (.venv)"
if [[ -x .venv/bin/python ]]; then
  ok ".venv already present"
else
  info "Creating .venv"
  "$PY" -m venv .venv
  ok "Created .venv"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
ok "Using $(command -v python) ($(python_major_minor python))"

echo
echo "3) Package (editable + capture extras)"
info "pip install -e \".[dev,capture]\""
python -m pip install --upgrade pip
python -m pip install -e ".[dev,capture]"
ok "demo-studio installed in venv"

echo
echo "4) Playwright Chromium"
if (( SKIP_PLAYWRIGHT )); then
  warn "Skipping Playwright Chromium (--skip-playwright)"
else
  if ask "playwright install chromium (required for --engine playwright)"; then
    python -m playwright install chromium
    ok "Chromium ready"
  else
    warn "Skipped — run later: python -m playwright install chromium"
  fi
fi

echo
echo "5) ffmpeg"
if have ffmpeg; then
  ok "$(ffmpeg -version 2>&1 | head -n1)"
else
  offer_ffmpeg || true
  if have ffmpeg; then
    ok "$(ffmpeg -version 2>&1 | head -n1)"
  else
    warn "ffmpeg still missing — packaging will fail until it is on PATH"
  fi
fi

echo
echo "6) TTS sidecars (optional; not auto-installed)"
info "Pocket TTS  → POCKET_TTS_URL  (default http://127.0.0.1:8000)"
info "Piper TTS   → PIPER_TTS_URL   (default http://127.0.0.1:8010) + DEMO_TTS_PROVIDER=piper"
warn "Start a TTS sidecar separately before narrate."

echo
echo "7) Doctor"
if have demo-studio; then
  demo-studio doctor || true
else
  python -m demo_studio.cli doctor || true
fi

echo
echo "=== Done ==="
echo "Activate:  source .venv/bin/activate"
echo "Smoke:     demo-studio doctor"
echo "Capture:   DEMO_BASE_URL=https://alongfor.happymonkey.ai \\"
echo "           demo-studio capture demos/alongfor/demo.beats.json --run-dir outputs/alongfor-run --engine playwright"
