---
kind: checkpoint
created: 2026-11-02T10:08:05Z
agent: cursor
sha: 6a43216
branch: main
paths: [README.md, src/demo_studio, demos/astro-cms, docs/plans/2026-11-02-demo-studio-roadmap.md]
verification: {V0: pass, V1: pass, V2: pass, V3: skip, V4: skip}
id: 2026-11-02T1008Z-goal-in-progress-phases-0-3-working-doctor-valid
---
# Checkpoint: Goal in progress: Phases 0–3 working (doctor/validate, NEO dry-run, Playwright…

## Summary

Goal in progress: Phases 0–3 working (doctor/validate, NEO dry-run, Playwright picture.mp4, Pocket TTS demo.mp4 ~44s on .215). Phase 4/5 scaffolding landed; human review + full re-run gate + real MCP still open.

## Done

- Phase 0–3 pipeline implemented and exercised
- Throwaway demostudio :4335; NEO smoke via tunnel
- First package on peer outputs/run-playwright-capture/
- Committed 6a43216 on main

## Next

- Human review demo.mp4 / review.html
- Run scripts/rerun-gate.sh on capture host
- Optional: implement real MCP server from mcp_stub; LAN-bind throwaway; fix peer Chrome

## Blockers

- Phase 4 exit needs human approval of the draft video
- Peer google-chrome --screenshot hangs

## Decisions

- (none)
