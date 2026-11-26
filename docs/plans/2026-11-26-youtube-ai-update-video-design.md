# AI development update video via demo-studio — design

Date: 2026-11-26 · Status: approved for planning · Path: architectural

## Goal

Replace the manual "agent reads my Twitter/GitHub → I write a script → I record" process
for YouTube AI-development update videos with a demo-studio run: one beats file produces a
10–20 minute narrated reel (`demo.mp4` + `captions.vtt` + `review.html`) that mixes

- fresh Playwright captures of live web projects, and
- trimmed segments from already-recorded clips (`~/Videos`, `~/Videos/Screen Recordings`,
  `~/Downloads`).

TTS (Pocket/Piper) is the final voice — no human re-record step. Reference style:
youtu.be/kO7sQV84elo (66-min self-narrated update); this format is the tighter, automated
descendant. Publishing stays manual (SPEC: never auto-publish).

## Non-goals

- Talking-head/webcam capture.
- YouTube upload automation (`publish.py` remains a dry-run draft).
- General-purpose video editing (transitions library, filters, color grading).
- Editing the source clips on disk; clips are read-only inputs, trims live in the beats file.

## Decisions already made (with user)

1. Narration: TTS is the final voice.
2. Length: medium demo reel, ~10–20 min, 4–6 project segments + intro/outro.
3. Footage: mix of existing clips + fresh captures.
4. Content selection: agent-curated from X posts + GitHub pushes, user-approved shortlist.
5. Build approach: first-class clip source in the beat schema (A), de-risked by a
   throwaway pre-seed probe (C) on one real clip before schema work lands.

## Workflow (per video)

1. **Research** — agent collects recent work: X posts (BrowserOS, user logged in) and
   GitHub pushes (`gh`) since the previous video. Output:
   `demos/<video-slug>/SEGMENTS.md` — 4–6 segments, each with project, story hook,
   visual plan (`clip:<file>` + rough in/out window, or URL for fresh capture), est. runtime.
   **Gate: user approves SEGMENTS.md before anything renders.**
2. **Clip inventory** — `ffprobe` every referenced clip; contact sheets (thumbnails) into
   `outputs/clip-review/` so chosen windows are eyeball-verifiable.
3. **Script** — narration written into the beats file in the user's update-video voice,
   TTS-friendly (short sentences). Intro beat (title card via existing
   `burn_title_card`) + per-segment beats + outro beat.
4. **Build** — `demo-studio` job run (validate → capture → narrate → package), then
   `review.html`. Fixes are beats-file edits and re-runs, never hand-edits of media.
5. **Publish draft** — `publish.py` dry-run output for a human to upload.

## Pack

`demos/ai-update-2026-11/demo.beats.json` is the first instance. Clip inputs are copied or
referenced by absolute path; packs must not point at confidential `client-data` trees
(existing rule holds — personal screen recordings are fine, client work is not).

## Schema change (additive, `version` stays 1)

Optional `visual` object on a beat:

```json
"visual": {
  "kind": "clip",
  "file": "clips/foo.mp4",
  "in_sec": 42.0,
  "out_sec": 97.0
}
```

- `kind`: `"capture"` (default when absent) or `"clip"`.
- `file`: relative to the pack directory, or absolute. Resolved at validate/capture time.
- `in_sec` / `out_sec`: optional; default whole clip. Must satisfy
  `0 <= in_sec < out_sec <= probed duration`.
- A clip beat must not carry browser `actions` (assert allowed only in a later slice).
- `additionalProperties: false` retained; unknown keys remain errors.

Validation errors (in `beats.validate_beats` + file checks at job create): missing file,
bad trim range, clip beat with `actions`, non-video extension (`.mp4 .mov .mkv .webm .avi`).

## Capture & assembly change

Current: one global `frames → picture.mp4` pass (`capture.frames_to_mp4`).
New: picture assembly becomes **per-beat segments → concat**:

1. For each beat in order:
   - capture beat (no `visual` or `kind: "capture"`): today's frame path, rendered to a
     beat segment with the existing duration logic (narration-aligned holds).
   - clip beat: ffmpeg trim `[in_sec, out_sec)` → scale-pad to canvas
     (`force_original_aspect_ratio=decrease,pad=<W>x<H>`, i.e. letterbox, never crop) →
     re-encode to the common segment profile. If the window is shorter than the beat's
     narration, freeze/hold the last frame for the remainder (pad with `tpad`). Looping is
     out of scope for v1.
2. Concat all segments (re-encode concat, same defensive pattern as
   `package_run.concat_wavs`) → `picture.mp4` (artifact name unchanged so
   `polish`/`studio_compose`/`mux_package`/`review.html` keep working).
3. Look handling: when `look: studio` + `cursor.json` exist, studio compose applies to
   capture beats as today; clip beats pass through unzoomed (v1). If that looks choppy in
   review, a later slice can apply the same xfade framing to clips.

Common segment encode profile (fixed for concat safety): canvas size from
`capture.width/height` (default 1920×1080), 30 fps, `h264` + `yuv420p`, silent AAC track
so concat never mixes audio-less and audio segments.

Existing single-engine behavior otherwise unchanged; `skip_capture` still skips to an
operator-provided `picture.mp4`.

## C-probe (throwaway, precedes implementation)

Script (not committed) on one real clip: trim → scale-pad 1080p → concat after an existing
job's `picture.mp4` → `mux_package` against real narration WAVs. Confirms letterboxing,
fps/timebase behavior, and concat cleanliness. Findings recorded in the implementation
notes; script discarded.

## Error handling

- Job create fails fast on missing clip files (before browser work starts).
- ffprobe/ffmpeg failure on a clip beat → job `failed`, `job.json` names beat id + file +
  stderr tail. No silent fallback to frames.
- Mixed-resolution inputs require no pre-normalization by the user — scale-pad handles it.
- Validation runs before any subprocess, so most operator mistakes cost nothing.

## Testing (TDD, per repo convention)

- `validate_beats` / schema: clip beat accepted; unknown `visual.kind`, bad ranges,
  clip+actions, missing file → errors.
- ffmpeg command construction for a clip segment (pure function, asserted argv; fake runner).
- Capture stage unit: clip beats are skipped by the Playwright/Chrome path (spy).
- Last-frame pad path: window shorter than narration produces `tpad` argument.
- Integration smoke (skip if ffmpeg absent): generate `testsrc` mp4 via lavfi, tiny beats
  file with one clip beat + one capture-ish beat, run job through to `demo.mp4` with stubbed
  TTS; assert durations and stream params uniform.
- `demo-studio doctor` gains a clip-path check (ffmpeg present already required).

## Rollout order

1. C-probe → record findings.
2. Schema + validation (tests first).
3. Clip segment builder + per-beat concat in `jobs.run_job` capture stage.
4. Build `demos/ai-update-2026-11`: research → SEGMENTS.md (user gate) → beats script
   (user sees it) → full run → `review.html` → user reviews; iterate beats.
5. Publish draft only.

## Inputs still to gather at execution time (not design gaps)

- User's X handle to browse; GitHub repos/period for the sweep.
- Final project list + approved clip windows (gates in workflow steps 1–2).
- TTS provider/voice choice (Pocket `:8000` vs Piper `:8010`) — doctor output decides.
