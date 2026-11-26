# SEGMENTS — AI dev update reel (draft 2026-11-26)

Target: 10–20 min TTS-narrated reel, one segment per project. Sources: GitHub sweep
(`outputs/_research/github-sweep-2026-11-26.md`, HappyMonkeyAI org, 57 repos since 2026-08-29),
X sample (`outputs/_research/x-posts-sample-2026-11-26.md`), clip inventory
(`outputs/_research/clip-inventory-2026-11-26.md`). Clip assignments are candidates —
confirmed by contact sheets before beats are written.

## 0 · Intro (~45 s)
Title card ("Another AI dev update — Aug → Nov 2026") + fast montage hooks from later segments.
Visual: montage of the best 3–5s windows already chosen below.

## 1 · Ark Providence — game built from scratch in a week with AI (~3 min)
Story: Dev Day 0→7, sci-fi survival/colony sim in ThreeJS, full 1-hour playthrough published;
"the game may look rough but the HUD needn't be" ties into the HUD UI Advisor MCP.
Visual: fresh capture of ark.happymonkey.ai (browser game — demo-studio can drive menus/planets)
+ clip candidate `~/Videos/2026-11-23 21-24-56.mp4` (playthrough session).
Evidence: X 2026-11-26 (GFowD68HX3s), ThreeDeeCity repo.

## 2 · MRPGRealms — from small start to RTS in days (~3 min)
Story: 325 commits (highest in org); settlement outposts, country map mockups, gesture-to-order
commanders, Blender animation pass.
Visual: fresh capture of realms.happymonkey.ai + clip candidates `~/Videos/2026-10-12 16-23-56.mp4`,
`2026-10-20 18-42-42.mp4` (X before/after videos match these dates).

## 3 · ZeroG desktop suite — AI-first terminal & file tools (~3 min)
Story: ZeroGTerm v0.7→v1.1.0 (screen-session discovery, SFTP, voice), ZeroGFileMan voice-enabled,
ZeroGEdit 62 ms→0.08 ms/frame perf story.
Visual: clips only (desktop apps) — candidates: `Screen Recording 2026-11-22 *` (2),
`~/Videos/2026-11-12 16-43-40.mp4`, `2026-11-16 21-49-13.mp4`; needs confirmation.

## 4 · Agent swarm infrastructure (~3 min)
Story: vibes-desktop per-role MCP tool allowlists/budgets + mission control, MonkeySwarm,
DynamicMCPProxy, Resource-Sentinel — "multiple agents on one machine without stepping on each other".
Visual: clips (terminal/desktop) — candidates: `2026-10-21 20-43-17.mp4`, `2026-11-17 21-08-31.mp4`,
`2026-11-19 20-22-17.mp4`; gitdash.happymonkey.ai could be fresh-captured as the org dashboard.

## 5 · Local GPU cinema — ComfyUI + 5090 (~2.5 min)
Story: OpenSwarmLayer P2P model sharing, chimp VRAM router, then the fun part: ComfyUI-Ref2VA-VSA
making a 1-minute cinematic from the "Filtered" story, 5s shots in ~120s each on a 5090.
Visual: clips — `~/Videos/filtered_rain_1min.mp4` (Nov 25 — likely the cinematic itself),
`subway-scene-full.mp4`, `untitled.mp4`; `GeminiAIMusic-*.mp4` for the AI-music thread.

## 6 · Closer — demo-studio made this video (~2 min, self-referential)
Story: the pipeline that produced this reel — beats → capture → TTS → package; Playwright cursor
timeline, aspect-safe studio zooms; "next update is just a new beats file".
Visual: fresh capture: alongfor.happymonkey.ai + review.html of this very run.

## Outro (~20 s)
CTA + sponsor mention (GitHub sponsors / multi-GPU bench goal from pinned post).

---
Total est.: ~17 min + intro/outro. Cuts available if it runs long: drop 4 or merge 4 into 3.
Open questions for the user:
- Which 5 of the 6 segments? (I'd keep all if runtime lands ≤20 min.)
- Any must-include not in this list (e.g. spine-mcp/AgentsProtocol, voice-for-agents, DirtBikeVR)?

## Confirmed windows — user gate 2026-11-26

User chose cut **B**: segments 3+4 merge into one "AI-first desktop tools & agent swarm"
segment (~4 min); ZeroG apps are told via title-card stills + narration (no desktop footage
exists in ~/Videos), swarm story rides a fresh capture of gitdash.happymonkey.ai.
Other proposed windows confirmed as-is. Sheet verification reclassified several clips
(11-16/-17/-19 = Ark; 10-21/-12 = MRPG; 11-22b = YouTube Music; untitled = builder sandbox).

| # | Segment | Source | in_sec | out_sec |
|---|---------|--------|-------:|--------:|
| 1 | Ark | ~/Videos/2026-11-23 21-24-56.mp4 | 600 | 650 |
| 1 | Ark | ~/Videos/2026-11-23 21-24-56.mp4 | 840 | 890 |
| 1 | Ark | ~/Videos/2026-11-19 20-22-17.mp4 | 180 | 230 |
| 1 | Ark | ~/Videos/2026-11-19 20-22-17.mp4 | 480 | 525 |
| 1 | Ark | ~/Videos/2026-11-17 21-08-31.mp4 | 180 | 230 |
| 2 | MRPG | ~/Videos/2026-10-12 16-23-56.mp4 | 0 | 50 |
| 2 | MRPG | ~/Videos/2026-10-12 16-23-56.mp4 | 180 | 205 |
| 2 | MRPG | ~/Videos/2026-10-21 20-43-17.mp4 | 260 | 310 |
| 2 | MRPG | ~/Videos/2026-10-21 20-43-17.mp4 | 310 | 360 |
| 2 | MRPG | ~/Videos/2026-11-12 16-43-40.mp4 | 10 | 60 |
| 2 | MRPG | ~/Videos/2026-11-12 16-43-40.mp4 | 60 | 110 |
| 2 | MRPG | ~/Videos/2026-10-20 18-42-42.mp4 | 90 | 135 |
| 5 | Cinema | ~/Videos/filtered_rain_1min.mp4 | 0 | 60 |
| 5 | Cinema | ~/Videos/untitled.mp4 | 80 | 130 |
| 5 | Cinema | ~/Videos/untitled.mp4 | 170 | 220 |
| 5 | Cinema | ~/Videos/subway-scene-full.mp4 | 0 | 31 |
| Out | Music | ~/Videos/Screen Recording 2026-11-22 …b (verify exact name) | 0 | 30 |

Fresh captures unchanged: ark.happymonkey.ai (1), realms.happymonkey.ai (2),
gitdash.happymonkey.ai (merged 3+4), alongfor.happymonkey.ai + this run's review.html (closer).
Intro montage reuses the strongest windows above (Ark 840–890, cinema 20–30, MRPG 310–360).
