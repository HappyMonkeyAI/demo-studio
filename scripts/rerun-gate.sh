#!/usr/bin/env bash
# Phase 4 re-run gate: same beats twice → two packages each with demo.mp4.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
: "${DEMO_BASE_URL:?set DEMO_BASE_URL to throwaway site}"

demo-studio validate demos/astro-cms/demo.beats.json

run_once() {
  local dir=$1
  rm -rf "$dir"
  mkdir -p "$dir"
  demo-studio dry-run demos/astro-cms/demo.beats.json --out "$dir"
  demo-studio capture demos/astro-cms/demo.beats.json --run-dir "$dir" --engine playwright
  demo-studio narrate demos/astro-cms/demo.beats.json "$dir"
  demo-studio package "$dir"
  test -f "$dir/demo.mp4"
}

A="$ROOT/outputs/rerun-gate-a"
B="$ROOT/outputs/rerun-gate-b"
run_once "$A"
run_once "$B"
echo "re-run gate PASS: $A and $B"
