# Unified visual engine for capture, clip and still beats — design

Date: 2026-11-27 · Status: proposed for review · Path: architectural

## Goal

Make a beat file capable of mixing live browser captures, trimmed video clips and still images in one deterministic pipeline, then use that model to remove the generated card-MP4 workaround from the AI development update reel.

The integration also carries forward the useful parts of `origin/feature/stills-engine`: first-class stills, voice selection, TTS-only pronunciation fixes, title-card voice offset and a hard package-duration cap.

## Non-goals

- Auto-publishing. `publish-draft` remains a dry-run and a human uploads.
- A general-purpose video editor or transition library.
- Cropping or blurred-fill framing. All sources remain contain/letterboxed by default.
- Multiple clips or images inside one beat. Multi-source montages must be split into beats.
- Desktop capture, generative UI, or changes to the TTS providers.
- Applying the `studio` cursor/zoom look to clip or still beats in this integration.

## Evidence from the AI update render

The 47-beat reel exposed a small set of repeatable failures:

1. Long montage beats put several images under one narration cue. The picture advanced before the voice named the next app or repository.
2. Screenshots were converted into 14 generated MP4 cards merely to reuse the clip path.
3. `pause_ms` affected capture pacing only; it did not create narration pauses.
4. `min_narration_ms` changed cue metadata but did not append audio, so metadata could describe a longer beat than the concatenated voice.
5. Packaged MP4s ran about two seconds longer than narration because `-stream_loop -1 -shortest` overshot.
6. Voice and pronunciation choices were not reproducible from the run manifest.
7. The two copies of `beat.schema.json` drifted: `gap_ms` was added only to the packaged copy.

`origin/feature/stills-engine` is healthy and directly relevant. Its two commits (`a061d16`, `992dd05`) add 11 files and 583 insertions; all 22 tests passed in an isolated worktree. It should be integrated conceptually rather than cherry-picked because both branches modify the schema, CLI, narration and packaging files.

## Decisions

1. **One visual model.** A beat resolves to exactly one visual unit: a capture sequence, one clip window, or one still image.
2. **Canonical still syntax.** Stills use `visual: { "kind": "still", "file": "..." }`.
3. **Compatibility alias.** The branch's top-level `still` property is accepted as a deprecated alias for one release. Supplying both forms is an error.
4. **One assembler.** `assemble_picture` dispatches all visual kinds through a shared per-beat segment pipeline.
5. **`stills` remains a convenience command.** It becomes a thin wrapper that requires every beat to be a still and calls the same assembler.
6. **Timing is audio-backed.** Any duration promised by cue metadata must exist in the cue WAV.
7. **Schema parity is tested.** The root and packaged schema copies must remain byte-identical.
8. **Human review remains mandatory.** No render is published automatically.

## Beat contract

Schema `version` stays `1`; all changes are additive. `additionalProperties: false` remains in force.

### Visual kinds

```json
{
  "id": "mesh-qwenr",
  "narration": "Qwen image editing and video generation run through one repository.",
  "gap_ms": 650,
  "visual": {
    "kind": "still",
    "file": "assets/qwenr-repo.png",
    "motion": "push",
    "fade_s": 0.2
  }
}
```

| Kind | Required | Optional | Rules |
|---|---|---|---|
| `capture` | none | none | Default when `visual` is absent. Browser actions are allowed. |
| `clip` | `file` | `in_sec`, `out_sec` | No browser actions. One contiguous window. Short windows freeze on the last frame. |
| `still` | `file` | `motion`, `fade_s` | No browser actions. One image held for the full cue duration. |

- `file` resolves relative to the beat file, expands `~`, or accepts an absolute path.
- `motion` is `none` or `push`; default `none` for deterministic cards.
- `fade_s` defaults to `0`; the all-still CLI may default it to `0.3` for a softer slide feel.
- All sources use contain/letterbox framing. No crop or blur fill in this integration.
- The deprecated top-level `still` string is normalized to `visual.kind=still`. It may not coexist with another `visual`.

### Narration timing fields

| Field | Meaning |
|---|---|
| `pause_ms` | Capture-only hold after browser actions. Never changes audio timing. |
| `gap_ms` | Extra silence appended after synthesized speech. Included in cue and picture duration. |
| `min_narration_ms` | Minimum total cue duration. If speech plus gap is shorter, append silence to the WAV. |
| `pronunciations` | Top-level written-to-spoken map applied only to TTS input. Captions keep the written text. |

The narration manifest will record `speech_ms`, `gap_ms`, `pad_ms`, `duration_ms`, `text`, and `spoken` when it differs from `text`. `duration_ms` must equal `end_ms - start_ms`.

## Architecture

### Current flow

```text
beats.json
  -> validate
  -> capture frames for every non-clip beat
  -> narrate one WAV per beat
  -> package --beats
       -> assemble_picture only when clip beats are present
       -> optional title card / studio compose
       -> mux picture + voice
  -> review.html
```

The stills branch has a separate `stills -> picture.mp4` path. Keeping both paths would preserve the card-MP4 workaround and duplicate timing logic.

### Proposed flow

```text
beats.json
  -> validate
  -> preflight (schema + files + media probes + visual plan)
  -> capture frames for capture beats only
  -> narrate one WAV per beat
  -> assemble_picture for every pack
       -> resolve one visual unit per beat
       -> capture segment | clip segment | still segment
       -> concat common-profile segments
       -> strip segment audio from shipped picture.mp4
  -> optional title card / studio compose
  -> mux picture + voice with hard audio-duration cap
  -> review.html + visuals.json
```

`assemble_picture` runs for capture-only packs too when `package --beats` is used. This makes timing consistent and removes the current split where capture-only packs use a whole-directory frame heuristic while clip packs use cue-aligned segments. The `capture` command retains its provisional capture-only `picture.mp4` for backward compatibility, but packaging with `--beats` rebuilds it from narration cues.

### Module responsibilities

- `beats.py`: JSON loading and schema validation only.
- `visuals.py` (new): visual-kind resolution, path resolution, static validation, media probing, cue-duration helper, and visual-plan construction. Existing visual helpers move here from `beats.py`.
- `capture.py`: ordered capture-frame sequence to a common-profile segment.
- `clips.py`: existing trim/scale-pad/freeze/silent-AAC segment builder.
- `stills.py`: still segment builder adapted from the remote branch, plus the all-still manifest view.
- `assemble.py`: per-beat dispatch, concat, audio strip, and `visuals.json`.
- `narrate.py`: voice/lexicon selection and audio-backed gap/minimum timing.
- `package_run.py`: caption offset, voice lead-in, explicit stream maps and duration cap.
- `cli.py` / `jobs.py`: command and job wiring for both entry paths.
- `scripts/run-demo.sh` / `run-demo.ps1`: pass through voice, lexicon and title-timing options; packs without a title card keep their existing behavior.

## Visual planning and preflight

Add `demo-studio preflight <beats> [--run-dir DIR]`.

It performs no browser or TTS work. It:

1. Runs schema and static visual validation.
2. Probes every clip and image with `ffprobe` for dimensions, duration and stream metadata.
3. Resolves each beat to a visual unit and records source path, source dimensions, effective clip window, target canvas, motion and fade.
4. Emits warnings for large aspect-ratio changes, non-unity SAR, out-of-range clip windows and capture beats with multiple frames.
5. Prints a compact per-beat table and, when `--run-dir` is supplied, writes `visual-plan.json` there.

`validate` remains the fast schema/static check. `preflight` is the media-aware gate used before an expensive render.

The plan is provenance: a reviewer can tell which file supplied each beat without reverse-engineering `picture.mp4`.

## Assembly contract

Every segment uses the same profile:

- Canvas from `capture.width` / `capture.height`, default 1920×1080.
- 30 fps, H.264, `yuv420p`, square SAR.
- Contain/letterbox scaling with `setsar=1`.
- Silent AAC 48 kHz stereo while segments are concatenated.
- Final `picture.mp4` is video-only, preserving the existing mux invariant that voice is the only audible source.

### Capture beats

The capture engines continue to skip clip and still beats. A capture beat may produce an ordered frame sequence from its actions. The assembler holds those frames across the cue duration using the existing equal-distribution fallback.

The one-cue/one-visual rule is enforced for still and clip beats. Capture sequences are the deliberate exception because they are generated by one action script; narration that changes subject should be split into another beat.

### Clip beats

Behavior stays as implemented on `clip-source-beats`:

- Trim `[in_sec, out_sec)`.
- Scale-pad to the canvas.
- Freeze the last frame with `tpad` when the window is shorter than the cue.
- Trim with `-t` when the clip is longer than the cue.
- Discard source audio and attach silent AAC explicitly.

### Still beats

The stills branch's renderer is adapted to the common segment profile:

- Loop one image for the exact cue duration.
- Optional centre push-in.
- Optional fade in/out, clamped so fades cannot consume the whole beat.
- Add the same silent AAC track as clip segments before concat.

### Manifest

`assemble_picture` writes `visuals.json` with one row per beat:

```json
{
  "beat": "mesh-qwenr",
  "kind": "still",
  "source": "assets/qwenr-repo.png",
  "source_width": 1280,
  "source_height": 720,
  "start_ms": 0,
  "duration_ms": 4200,
  "segment": "segments/00_mesh-qwenr.mp4",
  "motion": "push",
  "fade_s": 0.2
}
```

The all-still command also writes `stills.json` as a backward-compatible view of the same data.

## Narration changes

Port from `feature/stills-engine`:

- `narrate --voice`.
- `narrate --lexicon`.
- Top-level `pronunciations`.
- Whole-word, case-insensitive, longest-phrase-first replacement.
- Captions retain written text; the manifest records spoken text when different.
- Provider and voice are recorded in `narration.json`.

Fix the timing defect:

- Synthesize speech and measure `speech_ms`.
- Append `gap_ms`.
- If still shorter than `min_narration_ms`, append the remaining silence.
- Set `duration_ms` to the measured final WAV duration.
- Use `end_ms - start_ms` as the authoritative picture duration.

This makes `gap_ms` and `min_narration_ms` real audio rather than metadata-only promises.

## Packaging changes

Port and harden the remote branch's packaging work:

- When a title card is prepended, voice and captions are delayed by the title-card duration by default so beat visuals stay aligned. `--voice-over-title` is an explicit opt-out.
- `lead_in_s` is recorded in `package.json`.
- `write_vtt(..., offset_ms=...)` keeps captions aligned.
- Add `-t <audio_duration>` to both picture and audio-only mux branches.
- Map video and voice explicitly (`-map 0:v:0 -map 1:a:0`) instead of relying on ffmpeg's implicit lowest-index selection.
- Keep `-shortest` as a secondary guard, not the primary duration contract.

The title card remains packaging polish rather than a beat. Its duration defaults to 2.5 seconds. Voice starts after the title card by default; `--voice-over-title` preserves the old overlap behavior for packs that intentionally narrate over the card.

The `studio` look remains capture-only. Mixed capture/clip/still packs fall back to `clean` with a visible warning, as they do today.

## CLI and job behavior

- `validate`: schema, paths, allowed field combinations.
- `preflight`: media probes and `visual-plan.json`.
- `capture`: capture beats only; retain the provisional picture for capture-only packs, skip all-still and all-clip packs without launching a browser, and defer mixed-pack assembly.
- `narrate`: provider, voice, lexicon, gap/minimum timing.
- `stills`: require all beats to resolve to stills, then call the unified assembler.
- `package --beats`: rebuild from the beat plan when `picture.mp4` is absent or stale.
- `job-run`: accept and record `voice`, `lexicon`, and `voice_over_title`; use the same assembler and packager as the standalone CLI.
- `run-demo.sh` / `run-demo.ps1`: expose the new options; packs without a title card keep their existing behavior.
- MCP: `demo_validate` uses the same static visual validation as the CLI, and `demo_run_job` accepts the new voice/lexicon/title-timing options.
- Docs: update `README.md`, `docs/USAGE.md` and `QUICKSTART.md` with the unified visual model and the new timing semantics.

A stale `picture.mp4` must not silently ship. When `--beats` is supplied, packaging compares the beat/narration manifest identity and rebuilds if the picture is missing or predates the inputs.

## Review surface

`review.html` keeps the video and captions, and adds a compact beat/visual table from `visuals.json`: start time, beat id, visual kind and source filename. This makes “what should be on screen during this sentence?” directly inspectable.

The existing human gate is unchanged: nothing is published until the user approves the exact `review.html` render.

## AI update migration

After the engine is integrated:

1. Replace every generated `*-card.mp4` visual with `visual.kind=still` pointing at the underlying PNG/JPG.
2. Keep the per-app and per-repository beat splits.
3. Keep `gap_ms: 650` on the seven cinema repository beats.
4. Add `pronunciations` for names or numerals that TTS misreads.
5. Record the selected Piper voice in the run manifest.
6. Re-render and verify cue midpoints against the named app/repository.
7. Remove generated card MP4s only after the new render passes review.

The current render remains the review baseline until the user signs off on it.

## Merge and rollout strategy

Do not cherry-pick the stills branch. Both branches touch the same files and the stills branch is based on `main` at `e2be543`, while `clip-source-beats` contains the clip pipeline and AI update work.

1. Land the current `clip-source-beats` work through its existing human review gate.
2. Create an integration branch from `clip-source-beats`.
3. Port the stills, voice, lexicon and packaging changes into the unified design.
4. Add schema-parity and timing tests before changing behavior.
5. Migrate the AI update beats from card MP4s to stills.
6. Run the full suite and a mixed-pack integration render.
7. Re-render the AI update and repeat the human review gate.

## Testing strategy

- Schema: capture/clip/still accepted; unknown kinds, missing files, invalid ranges, conflicting `still` aliases and non-capture actions rejected.
- Schema parity: root and packaged schemas compare byte-for-byte.
- Visual planning: relative/absolute/`~` paths, media probes, aspect warnings and cue/beat identity.
- Assembly: mixed capture+clip+still pack, exact cue-aligned durations, square SAR, silent intermediate audio and video-only final picture.
- Stills: `none` and `push`, fade clamping, missing image and cue mismatch failures.
- Narration: real `gap_ms`, real `min_narration_ms` padding, lexicon precedence, caption text preservation and voice manifest.
- Packaging: `-t` cap, explicit maps, title lead-in, caption offset and audio/picture duration parity.
- CLI/jobs: all-still, all-clip and mixed packs through both standalone and job entry points.
- Regression: existing AlongFor, Realms and astro-cms beats still validate and package.

ffmpeg-dependent tests remain skipped only when ffmpeg is absent; they must assert measured stream durations rather than echoed metadata.

## Acceptance criteria

- One beat file can mix capture, clip and still visuals in any order.
- Every beat's picture duration equals its narration cue duration.
- `gap_ms` and `min_narration_ms` are audible silence in the final voice track.
- Packaged duration matches voice duration plus the title-card lead-in when used within 0.1 seconds.
- The AI update pack contains no generated card MP4s.
- Both schema copies are identical and covered by a test.
- Voice, lexicon and visual provenance are recorded in run manifests.
- Existing tests pass, new mixed-pack integration passes, and the AI update passes human review before any draft publication.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Merge conflicts in schema/CLI/narration/package | Port by responsibility into the unified design; do not cherry-pick. |
| Schema copies drift again | Byte-parity test and update both in every schema change. |
| Cue metadata diverges from audio | Measure final WAV and derive picture duration from `end_ms - start_ms`. |
| Title card desynchronises stills | Delay voice and captions by the title duration by default; keep overlap as an explicit opt-out. |
| `studio` look rebuilds the wrong picture | Keep it capture-only and fail over to `clean` for mixed packs. |
| Asset migration changes the approved render | Keep the current render as baseline; remove cards only after the replacement passes review. |

## Deferred

- Blurred-fill or cover-crop framing.
- Multiple clips or images in one beat.
- Crossfades between beats.
- Studio zoom/pointer composition on clip or still beats.
- Desktop capture.
- Automatic publication.
