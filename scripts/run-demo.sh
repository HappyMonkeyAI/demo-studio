#!/usr/bin/env bash
# One-shot: validate → capture → narrate → package for a built-in pack or beats file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PACK=""
BASE_URL=""
PROVIDER="${DEMO_TTS_PROVIDER:-pocket}"
ENGINE="playwright"
LOOK="clean"
TITLE=""
SUBTITLE=""
RUN_DIR=""
BEATS=""

usage() {
  cat <<'EOF'
Usage: ./scripts/run-demo.sh <pack|beats.json> [options]

  Packs: alongfor | mrpg-realms | astro-cms | example-static
  Or pass a path to demo.beats.json

Options:
  --base-url URL       Override DEMO_BASE_URL
  --provider NAME      pocket (default) | piper
  --engine NAME        playwright (default) | chrome | auto
  --look NAME          clean (default) | product-zoom | studio
  --title TEXT         Title card text
  --subtitle TEXT      Title card subtitle
  --run-dir PATH       Output directory (default: outputs/<pack>-<stamp>)
  -h, --help           Show help

Examples:
  ./scripts/run-demo.sh alongfor
  ./scripts/run-demo.sh alongfor --look product-zoom
  ./scripts/run-demo.sh mrpg-realms --provider piper
  DEMO_BASE_URL=http://127.0.0.1:4335 ./scripts/run-demo.sh astro-cms
EOF
}

if (($# < 1)); then
  usage >&2
  exit 1
fi

PACK="$1"
shift

while (($#)); do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --engine) ENGINE="$2"; shift 2 ;;
    --look) LOOK="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --subtitle) SUBTITLE="$2"; shift 2 ;;
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# Activate venv if present
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if ! command -v demo-studio >/dev/null 2>&1; then
  echo "error: demo-studio not on PATH. Run ./install.sh and activate .venv" >&2
  exit 1
fi

resolve_pack() {
  local name="$1"
  case "$name" in
    alongfor)
      BEATS="demos/alongfor/demo.beats.json"
      BASE_URL="${BASE_URL:-${DEMO_BASE_URL:-https://alongfor.happymonkey.ai}}"
      TITLE="${TITLE:-AlongFor}"
      SUBTITLE="${SUBTITLE:-event companion}"
      ;;
    mrpg-realms|realms)
      BEATS="demos/mrpg-realms/demo.beats.json"
      BASE_URL="${BASE_URL:-${DEMO_BASE_URL:-https://realms.happymonkey.ai}}"
      TITLE="${TITLE:-MRPG Realms}"
      SUBTITLE="${SUBTITLE:-voxel multiplayer · wiki}"
      name="mrpg-realms"
      PACK="$name"
      ;;
    astro-cms)
      BEATS="demos/astro-cms/demo.beats.json"
      BASE_URL="${BASE_URL:-${DEMO_BASE_URL:-}}"
      TITLE="${TITLE:-Astro CMS}"
      SUBTITLE="${SUBTITLE:-throwaway EmDash walkthrough}"
      if [[ -z "$BASE_URL" ]]; then
        echo "error: astro-cms needs DEMO_BASE_URL or --base-url (throwaway EmDash only)" >&2
        exit 1
      fi
      ;;
    example-static)
      BEATS="demos/example-static/demo.beats.json"
      BASE_URL="${BASE_URL:-${DEMO_BASE_URL:-}}"
      TITLE="${TITLE:-Example}"
      SUBTITLE="${SUBTITLE:-static fixture}"
      if [[ -z "$BASE_URL" ]]; then
        echo "error: example-static needs DEMO_BASE_URL or --base-url" >&2
        exit 1
      fi
      ;;
    *)
      if [[ -f "$name" ]]; then
        BEATS="$name"
        PACK="$(basename "$(dirname "$name")")"
        BASE_URL="${BASE_URL:-${DEMO_BASE_URL:-}}"
        if [[ -z "$BASE_URL" ]]; then
          echo "error: set DEMO_BASE_URL or pass --base-url" >&2
          exit 1
        fi
      elif [[ -f "demos/$name/demo.beats.json" ]]; then
        BEATS="demos/$name/demo.beats.json"
        BASE_URL="${BASE_URL:-${DEMO_BASE_URL:-}}"
        if [[ -z "$BASE_URL" ]]; then
          echo "error: set DEMO_BASE_URL or pass --base-url for pack '$name'" >&2
          exit 1
        fi
      else
        echo "error: unknown pack or beats file: $name" >&2
        exit 1
      fi
      ;;
  esac
}

resolve_pack "$PACK"
export DEMO_BASE_URL="$BASE_URL"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${RUN_DIR:-outputs/${PACK}-${STAMP}}"

echo "=== demo-studio run-demo ==="
echo "beats:    $BEATS"
echo "base_url: $DEMO_BASE_URL"
echo "provider: $PROVIDER"
echo "engine:   $ENGINE"
echo "look:     $LOOK"
echo "run_dir:  $RUN_DIR"
echo

demo-studio validate "$BEATS"
mkdir -p "$RUN_DIR"
demo-studio capture "$BEATS" --run-dir "$RUN_DIR" --engine "$ENGINE"
demo-studio narrate "$BEATS" "$RUN_DIR" --provider "$PROVIDER"

PKG_ARGS=("$RUN_DIR" --look "$LOOK")
if [[ -n "$TITLE" ]]; then
  PKG_ARGS+=(--title-card "$TITLE")
fi
if [[ -n "$SUBTITLE" ]]; then
  PKG_ARGS+=(--subtitle "$SUBTITLE")
fi
demo-studio package "${PKG_ARGS[@]}"

echo
echo "=== Done ==="
echo "Review:  $RUN_DIR/review.html"
echo "Video:   $RUN_DIR/demo.mp4"
