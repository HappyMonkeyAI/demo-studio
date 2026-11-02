# AIQA / UIQA desktop beats — deferred (Phase 5 shelf)

**Status:** Explicitly deferred. Not required for the v0 product-walkthrough pipeline.

## Why deferred

astro-cms (and similar website-app) demos stay inside the browser. BrowserOS NEO + Playwright cover actuation and capture. AIQA/UIQA matter when a beat must leave the browser (native installer, OS dialogs, non-web IDE).

## When to pull off the shelf

1. A beat file needs `type: desktop_*` actions (click OS window, type into native app).
2. Linux AIQA remote MCP is healthy on the demo host.
3. Add an adapter next to `neo_script.py` without changing the beat schema version unless necessary.

## Non-goal reminder

Do not block shipping browser-only demos on AIQA.
