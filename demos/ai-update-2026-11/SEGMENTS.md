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
| 2 | MRPG | ~/Videos/2026-10-20 18-42-42.mp4 | 35 | 75 |
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
| Out | Music | ~/Videos/Screen Recordings/Screen Recording 2026-11-22 123742.mp4 | 0 | 30 |

Fresh captures unchanged: ark.happymonkey.ai (1), realms.happymonkey.ai (2),
gitdash.happymonkey.ai (merged 3+4), alongfor.happymonkey.ai + this run's review.html (closer).
Intro montage reuses the strongest windows above (Ark 840–890, cinema 20–30, MRPG 310–360).

## Run log

### 2026-11-27 — second-pass visual audit and revised render

- Re-ran the local Gemma 4 E2B coverage audit as triage, then manually verified all 24 beats against sampled frames. E2B produced usable verdicts for 22 beats; indices 7 and 20 repeatedly returned malformed JSON, so those two were verified manually rather than treated as clean.
- Replaced confirmed mismatches with verified visuals: ThreeGameForge repository capture, real ZeroG app stills, HUD/HTML advisor repositories, vibes-desktop mission control, swarm and cinema infrastructure repositories, demo-studio artifacts, AlongFor screens, the correct “Until The Ticking Stops” title card, and a linked end card.
- Kept the beat schema stable by referencing ten pre-rendered montages plus the music and end-card clips as ordinary `clip` visuals. Removed narration that named footage or repositories not shown.
- Restored Piper `en_GB-alba-medium` on DevHost `192.168.5.215` through the existing `demo-studio-piper` container and SSH tunnel.
- Command: `./scripts/run-demo.sh demos/ai-update-2026-11/demo.beats.json --base-url https://ark.happymonkey.ai --provider piper --look clean --run-dir outputs/ai-update-2026-11-20261126T221254Z`
- Result: 24 segments; 782.247 s narration; 784.633 s MP4 container; H.264 1920×1080 yuv420p; AAC 22.05 kHz mono; 90,632,299 bytes.
- Verification: schema validation passed; all replacement assets exist; montage durations and midpoint frames checked; final spot checks covered Ark, HUD, MRPG, ZeroG, swarm, cinema, studio, music and end card; no black intervals ≥0.5 s; audio mean −17.6 dB.
- YouTube description with final chapters and project/sponsor/X links: `YOUTUBE_DESCRIPTION.md`. Four private repositories were verified with `gh api` and removed from the public link list; MRPG Realms uses the live site and Resource Sentinel uses the public write-up.
- Final targeted E2B re-audit: 16 beats returned usable verdicts, one returned `not_shown` (vibes-desktop, confidence 0.15), one returned `shown`, and one failed to parse. The low-confidence `not_shown` result and all partial/missing-label results were treated as triage leads, not authoritative defects; the replacement montages had already been manually checked against the revised frames.
- Human review gate: awaiting user sign-off on `outputs/ai-update-2026-11-20261126T221254Z/review.html`. Nothing has been published.

### 2026-11-27 — MRPG clip correction and final re-render

- User review identified the 3:50 frame as Transport (3JS TTD), not MRPG Realms. Replaced the `mrpg-outposts` source with verified MRPG settlement footage from `~/Videos/2026-10-20 18-42-42.mp4`, window 35–75 s.
- Verified the corrected render at 3:50: MRPG Realms settlement/outpost gameplay is shown, with the MRPG HUD and realm URL visible.
- Command: `./scripts/run-demo.sh demos/ai-update-2026-11/demo.beats.json --base-url https://ark.happymonkey.ai --provider piper --look clean --run-dir outputs/ai-update-2026-11-20261127T102021Z`
- Result: 24 segments; 784.299 s narration; 786.367 s MP4 container; H.264 1920×1080 yuv420p; AAC 22.05 kHz mono; 107,345,358 bytes.
- Verification: schema validation passed; corrected 3:50 frame checked; final media probe passed; no black intervals ≥0.5 s.
- Human review gate: awaiting user sign-off on `outputs/ai-update-2026-11-20261127T102021Z/review.html`. Nothing has been published.

### 2026-11-27 — ZeroGTerm widescreen framing correction

- User review identified the first ZeroG suite frame as a vertical mobile crop. Replaced `zerogterm.jpg` with the full desktop ZeroGTerm screenshot from `happymonkey.ai/images/projects/zerogterm.png`.
- Rebuilt both `zerog-suite-montage.mp4` and `zerog-apps-montage.mp4` with the landscape source while preserving their 60 s and 55 s durations and segment order.
- Verified the corrected render at 5:19 and 6:01: the ZeroGTerm window now fills the 16:9 frame without the vertical crop.
- Command: `./scripts/run-demo.sh demos/ai-update-2026-11/demo.beats.json --base-url https://ark.happymonkey.ai --provider piper --look clean --run-dir outputs/ai-update-2026-11-20261127T120859Z`
- Result: 24 segments; 782.026 s narration; 784.333 s MP4 container; H.264 1920×1080 yuv420p; AAC 22.05 kHz mono; 106,462,186 bytes.
- Verification: schema validation passed; corrected ZeroG frames checked; final media probe passed; no black intervals ≥0.5 s.
- YouTube description chapters updated to the final narration timings.
- Human review gate: awaiting user sign-off on `outputs/ai-update-2026-11-20261127T120859Z/review.html`. Nothing has been published.

### 2026-11-27 — Narration/visual sync, repo pacing, vibes framing, subway edit

- User review: ZeroG montage images ran out of sync with the spoken app names (SFTP never shown; FileMan shown under Play/Edit lines); the 7:07 vibes frame was a vertical half-crop; cinema repo images switched before the voice finished and repo narrations blurred together; the 10:22 subway source had artefacts.
- Fix (schema-stable): split `desktop-suite` into 14 per-app/per-tool beats and `desktop-zerogterm` into 6, each with its own static card clip (`zerogterm/fileman/sftp/play/edit-card.mp4`, `auditscan-card.mp4`, `project-atlas-card.mp4`). Split `cinema-mesh` into 4 and `cinema-shots` into 3 per-repo beats with repo-homepage cards. Every visual now owns exactly one narration cue, so sync is guaranteed by construction.
- New optional beat field `gap_ms` (schema + `narrate.py`): appends real silence to the cue WAV after synthesis; set to 650 ms on all seven cinema repo beats so each repo narration ends with a natural pause before the next. Measured 0.79 s trailing silence on `mesh-qwenr`.
- Maintenance-tools line now shows AuditScan (verified 34 commits in window via `gh api`) and project-atlas repo homepages; both added to the description link list (HTTP 200).
- vibes montage rebuilt full-width: mission-control app screenshot (0–15 s), vibes-desktop repo homepage (15–30 s), app screenshot (30–45 s). The happymonkey.ai `vibes-desktop.jpg` project image turned out to be a repo screenshot itself and was dropped as redundant.
- Subway: replaced `~/Videos/subway-scene-full.mp4` with the user's cleaned edit `C:\Users\steph\Downloads\subway.mp4` (copied to `assets/subway-scene-edit.mp4`, 22.87 s, 1280×720); narration updated to "twenty-three seconds".
- Commands: run `20261127T134710Z` (first pass, caught the double repo-page in vibes), then final `./scripts/run-demo.sh demos/ai-update-2026-11/demo.beats.json --base-url https://ark.happymonkey.ai --provider piper --look clean --run-dir outputs/ai-update-2026-11-20261127T135840Z`.
- Result: 47 segments; 794.050 s narration; 796.333 s MP4 container; H.264 1920×1080 yuv420p; AAC 22.05 kHz mono; 106,668,715 bytes.
- Verification: schema validation passed (47 beats); 24-frame contact sheet confirmed every app/repo cue shows its named subject (commit roll-call, app roll-call, scanner/atlas, all seven cinema repos); vibes app→repo→app confirmed at 7:01/7:19/7:32; subway edit confirmed at 10:40; no black intervals ≥0.5 s.
- YouTube description chapters updated: 00:31 / 03:05 / 05:19 / 06:57 / 08:34 / 10:53 / 12:47.
- Human review gate: awaiting user sign-off on `outputs/ai-update-2026-11-20261127T135840Z/review.html`. Nothing has been published.
