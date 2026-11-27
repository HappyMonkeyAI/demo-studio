# Desktop capture artifact bridge — design

Date: 2026-11-27 · Status: proposed for review · Path: architectural

## Goal

Let development videos use screenshots and, later, short screen recordings captured in the disposable Windows lab without moving VM lifecycle or desktop actuation into `demo-studio`.

The first slice is deliberately an artifact bridge: `remote-uiqa-lab` performs and verifies the desktop work, then exports a small, hash-verified evidence bundle. `demo-studio` imports approved media as ordinary `still` or `clip` visuals and renders it through the unified visual engine.

## Non-goals

- A new `desktop` visual kind or desktop actions inside beat JSON.
- Arbitrary PowerShell, clicks, or installs authored by a beat file.
- Using RustDesk MCP for unattended control. RustDesk remains human watch/takeover only.
- Modifying `uiqa - taskreporter`, DesktopContext, recall-agent, AIQA, or the archived OpenBot lab.
- Targeting the host, a daily driver, another LAN machine, or RustDesk ID `176148465`.
- Continuous recording, audio capture, or source desktop audio in the final render.
- Automatic installation from the internet in the first slice.
- Video recording in the first slice. Screenshots prove the bridge first; recording is a separate spike.
- Automatic publication. TTS remains the final voice and human review remains mandatory.

## Current evidence and constraints

The supplied `uiqa - taskreporter` project is a local-first context recorder. Its loopback JSON API has no VM lifecycle, MCP server, autonomous actions, installer support, recording, or artifact download. Its own specification excludes autonomous desktop actions, so it is not the control plane for this work.

The real control plane is `remote-uiqa-lab` plus the original OpenBot lab record:

- The disposable target is `lab-win11`, a Windows 11 VM with 4 GB RAM, 4 vCPU, and a 64 GB disk.
- The guest runs `windows-mcp 4.2.4` over authenticated streamable HTTP.
- The observed tool surface has 21 tools: screenshot, UIA snapshot, display inventory, input, waiting, app/process/file/PowerShell control, and desktop ownership.
- The original `labrun.py` already records screenshots, `steps.jsonl`, and `summary.json`, and releases desktop control in `finish()`.
- The canonical lab RustDesk ID is `97523850`. The personal ID `176148465` is off-limits.
- The current host-to-guest file path is a read-only SMB share exposed as `Z:`. It is sufficient for staging files into the guest but cannot export artifacts.
- Screenshot bytes already return directly in MCP image content, so the first slice needs no guest-to-host file transfer.
- No video recorder exists. Current “recording” means screenshots plus structured logs.
- The recreated `remote-uiqa-lab` repository has configuration, secret handling, preflight, and tests, but still lacks bring-up, teardown, MCP client, recorder, and verification scripts.
- The windows-mcp endpoint is not mounted in the current Qoder session. The lab's own HTTP client can still be implemented and tested offline; live verification requires the endpoint to be available.
- The last real Find-dialog acceptance run passed every check except `Escape closes find bar`. That flow is not yet a trusted capture template.

## Architecture

```text
remote-uiqa-lab                         demo-studio
----------------                        -----------
capture request.json
        |
        v
validate + preflight
        |
        v
windows-mcp client ---- authenticated HTTP ----> lab-win11
        |                                            |
        |<-------------- screenshots / UIA ----------|
        v
run directory
  request.json
  steps.jsonl
  summary.json
  manifest.json
  artifacts/*.png
        |
        |  verified artifact bundle
        v
import-desktop command
        |
        v
demos/<pack>/assets/desktop/<artifact>
        |
        v
beat visual: still | clip -> unified assembler -> review.html
```

The boundary is intentional:

- `remote-uiqa-lab` owns target selection, secrets, desktop control, app state, action policy, evidence, and failure reporting.
- `demo-studio` owns media validation, beat integration, timing, rendering, TTS, review, and packaging.
- Beat JSON describes the finished visual, not the live desktop session.
- The original OpenBot lab remains read-only provenance. New runtime code belongs in the recreated repository.

## Dependencies and order

This design depends on the unified visual engine landing first. It consumes the canonical `visual.kind = "still" | "clip"` contract and does not introduce a competing media path.

Implementation order:

1. Land the unified visual engine and its schema/timing tests.
2. Finish `remote-uiqa-lab` bring-up parity, its MCP client, recorder, and smoke verification.
3. Resolve the known Escape acceptance failure before using that flow as a template.
4. Implement the screenshot capture job and `demo-studio` importer.
5. Run a live ZeroG Edit screenshot capture through the complete bridge.
6. Spike guest-side video recording and artifact transfer separately.
7. Only then consider an optional desktop acquisition adapter or MCP convenience tool.

## Capture job contract

A capture job is a JSON file stored with the run, not in beat JSON. Version 1 supports launching a pre-staged application, a bounded action sequence, screenshot capture, and explicit verification.

```json
{
  "schema_version": 1,
  "job_id": "zerog-edit-find-open",
  "target": {
    "vm": "lab-win11",
    "rustdesk_id": "97523850"
  },
  "timeout_s": 120,
  "app": {
    "name": "ZeroG Edit",
    "executable": "C:\\Lab\\zerogedit.exe",
    "args": ["C:\\Lab\\sample.txt"],
    "sha256": "59e532fe00000000000000000000000000000000000000000000000000000000"
  },
  "steps": [
    {
      "id": "launch",
      "action": "launch_app"
    },
    {
      "id": "open-find",
      "action": "shortcut",
      "shortcut": "ctrl+f",
      "verify": {
        "type": "uia_text",
        "contains": "Find"
      }
    },
    {
      "id": "type-query",
      "action": "type_text",
      "text": "needle",
      "verify": {
        "type": "uia_text",
        "contains": "needle"
      }
    },
    {
      "id": "capture",
      "action": "screenshot",
      "artifact": "find-open.png"
    }
  ],
  "expected": {
    "app_window": "ZeroG Edit",
    "screenshots": ["find-open.png"]
  }
}
```

The example hash is illustrative and must be replaced with the observed binary hash in a real request. The runner validates the actual file hash before launch.

### Allowed action types

Version 1 allows only:

- `launch_app` for an executable already staged in the guest.
- `shortcut` for a named keyboard shortcut.
- `type_text` for literal text into the active control.
- `click_uia` for a target resolved from a fresh UIA snapshot.
- `wait_for` for a UIA text, window, or element condition.
- `screenshot` for a named PNG artifact.
- `verify` as a step that asserts UIA text, window state, or screenshot presence.

Arbitrary PowerShell is not a capture-job action. Lab maintenance may still use the existing PowerShell tool, but it is outside this contract and cannot be smuggled into a render beat.

### Install policy

Version 1 does not download or execute installers. The app must already be present in the disposable guest, placed there by the lab operator through the existing staging path.

A later installer action must pin the source URL and SHA256, require an explicit runtime approval flag, and record that approval in the manifest. Approval must never be inferred from the presence of a beat or a capture request.

## Run artifacts

Each run writes to `remote-uiqa-lab/runs/<UTC timestamp>-<job_id>/`:

```text
request.json       validated request, with secrets absent
steps.jsonl        one observed record per action
summary.json       per-check verdict and completion state
manifest.json      exportable provenance and artifact hashes
artifacts/
  find-open.png
```

`steps.jsonl` records the step id, action, start/end time, tool name, sanitized arguments, observed result, verification result, and screenshot path when one was taken. It must not contain bearer keys, passwords, relay keys, clipboard contents, or personal data.

`summary.json` is authoritative for pass/fail. A run is exportable only when every required step and expected artifact passed.

### Manifest

```json
{
  "schema_version": 1,
  "job_id": "zerog-edit-find-open",
  "status": "passed",
  "target": {
    "vm": "lab-win11",
    "rustdesk_id": "97523850"
  },
  "captured_at": "2026-11-27T12:00:00Z",
  "tool": {
    "name": "windows-mcp",
    "version": "4.2.4"
  },
  "app": {
    "name": "ZeroG Edit",
    "executable": "C:\\Lab\\zerogedit.exe",
    "sha256": "59e532fe00000000000000000000000000000000000000000000000000000000"
  },
  "artifacts": [
    {
      "path": "artifacts/find-open.png",
      "kind": "image",
      "mime": "image/png",
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "width": 1920,
      "height": 1080
    }
  ],
  "steps": "steps.jsonl",
  "summary": "summary.json",
  "safety": {
    "control_released": true,
    "install_performed": false,
    "personal_data_expected": false
  }
}
```

The manifest contains provenance, not secrets. Artifact paths are relative to the run directory and must not escape it.

## Lifecycle

1. **Load and validate.** Parse the request, reject unknown fields/actions, assert the target is exactly `lab-win11` and `97523850`, and validate timeout and artifact names.
2. **Preflight.** Load `.env`, redact secrets from all output, verify the MCP endpoint answers `initialize`, discover tools with `tools/list`, and assert required capabilities exist.
3. **Acquire control.** Query `ControlStatus`; acquire AI control only when the desktop is ready. A busy or human-controlled desktop aborts the run.
4. **Prepare app.** Verify the staged executable hash, launch it, and wait for the expected window.
5. **Execute steps.** Use UIA-first grounding. For egui apps with poor UIA, use keyboard shortcuts and verify with a fresh screenshot; record that fallback explicitly.
6. **Capture.** Extract image content from the MCP response, validate MIME type and decoded bytes, and write the PNG.
7. **Verify.** Assert every expected window, text condition, and artifact. Tool success alone is not a pass; ground truth must change or be observed.
8. **Release.** Call `ControlStatus(release=true)` in `finally`, including on assertion failure and exceptions.
9. **Finalize.** Write `summary.json` and `manifest.json`. Failed or partial runs are retained for diagnosis but are not importable.
10. **Export.** The importer accepts only a passed run with a valid manifest and matching hashes.

If the runner is forcibly terminated, the control gate's idle timeout is the backstop. The next run must assert or release stale AI control before doing desktop work.

## Error handling

| Failure | Required behavior |
|---|---|
| Endpoint unreachable | Fail at preflight with a named stage; create no success manifest and claim no desktop action. |
| Auth failure | Fail without printing the key or request headers. |
| Target mismatch | Refuse to run before acquiring control. |
| Desktop busy or human takeover | Abort, release if held, preserve partial evidence, and do not retry aggressively. |
| Required MCP tool missing | Fail with the discovered tool list and required capability name. |
| App hash mismatch | Refuse to launch the binary. |
| Action timeout | Capture a diagnostic screenshot if possible, mark the run failed, and release control. |
| Verification mismatch | Mark the run failed even if the tool returned success. |
| Missing or corrupt screenshot | Mark the artifact and run failed. |
| Secret or personal data detected | Quarantine the run, redact logs, and refuse export. |
| Manifest hash mismatch | Refuse import. |
| Import path traversal or symlink escape | Refuse import before writing into the pack. |

No failure path may silently fall back to a different VM, a different RustDesk ID, an insecure remote flag, or an unverified artifact.

## `demo-studio` importer

Add a narrow `import-desktop` command. It does not contact the VM.

```text
demo-studio import-desktop RUN_DIR --pack demos/<pack> --beat <beat-id> [--apply]
```

Default behavior is a dry run that validates the bundle and prints the proposed asset path and beat fragment. `--apply` copies the artifact and updates the selected beat.

The importer must:

1. Require `manifest.status == "passed"` and `safety.control_released == true`.
2. Validate the manifest schema and relative artifact paths.
3. Verify every artifact SHA256 and image dimension.
4. Reject runs containing personal data, unresolved failures, or secret-like values.
5. Copy media only under `demos/<pack>/assets/desktop/`.
6. Preserve the source manifest as `assets/desktop/<job-id>.manifest.json` with secrets absent.
7. Set the beat visual to `still` for PNG/JPG artifacts or `clip` for validated video artifacts.
8. Run normal beat and visual validation after `--apply`.
9. Leave publishing and human review unchanged.

The importer never edits `remote-uiqa-lab`, never reads `.env`, and never needs the windows-mcp bearer key.

### Resulting beat

```json
{
  "id": "zerog-edit-find",
  "narration": "ZeroG Edit finds each occurrence and jumps between matches.",
  "visual": {
    "kind": "still",
    "file": "assets/desktop/zerog-edit-find-open.png"
  }
}
```

One capture artifact belongs to one beat. If the narration changes subject, the capture job or beat must be split rather than mounting several screenshots under one cue.

## Media and timing contract

- Screenshots retain their captured dimensions; the unified engine contain/letterboxes them to the canvas.
- The importer records actual width and height and warns when the aspect ratio differs materially from 16:9.
- No cropping, blurred fill, or AI upscaling is introduced by this bridge.
- Future video artifacts must be probed with `ffprobe` before import.
- Future video source audio is discarded. TTS remains the only audible source.
- Picture timing comes from narration cue duration, exactly as for other `still` and `clip` visuals.
- `review.html` must show the imported source through the unified visual provenance table.

## Security and privacy

The following rules are implementation requirements, not documentation-only guidance:

- Target only `lab-win11`; reject every other VM name or RustDesk ID.
- Never use personal RustDesk ID `176148465`.
- Use the self-hosted relay only; never public rendezvous servers.
- Never pass `--allow-insecure-remote`.
- Keep bearer keys, relay keys, and passwords in gitignored `.env` or lab secret files only.
- Never print secrets in CLI output, logs, manifests, screenshots, commits, or chat.
- No personal accounts or credentials on the guest screen.
- No sends, deletes, payments, or installs without explicit approval.
- Release desktop control on every handled exit; use idle-timeout recovery after forced termination.
- Treat screenshots as potentially sensitive; refuse export when personal data is expected or detected.
- Keep `runs/` gitignored. Only sanitized, approved artifacts are copied into a demo pack.

## Testing strategy

### Offline and fake-server tests

- Request schema validation, unknown action rejection, target pinning, timeout bounds, and artifact-name safety.
- Manifest validation, status gating, hash verification, dimension checks, and path containment.
- Secret redaction and secret-like artifact rejection.
- Importer dry run, `--apply`, beat update, and rollback on validation failure.
- Fake MCP server returning screenshot content and simulated UIA results.
- Failure injection for unreachable endpoint, auth failure, missing tool, busy control, timeout, verification mismatch, corrupt image, and hash mismatch.
- Proof that failed runs cannot be imported.
- Proof that source desktop audio is absent from future clip segments.

### Live lab acceptance

The first live acceptance run must:

1. Start from a ready `lab-win11` desktop.
2. Launch a pre-staged portable app with a verified hash.
3. Perform a small UIA-grounded or keyboard-grounded action sequence.
4. Capture at least one screenshot.
5. Verify the expected state from UIA or a fresh screenshot.
6. Release control and assert `state == "ready"`.
7. Produce a passed manifest with valid hashes and no secrets.
8. Import the screenshot into a demo pack as a still.
9. Validate and render the beat through the unified engine.
10. Show the result in `review.html` for human approval.

The known ZeroG Find flow is the preferred end-to-end case only after its Escape failure is fixed. Until then, a simpler app flow must prove the bridge, and the Find flow remains a failing regression case rather than a success template.

### Video spike

Video is not part of first-slice acceptance. A later spike must prove:

- Guest-side recording starts and stops reliably.
- The recorded file is transferred to the host through an explicit writable artifact channel.
- The transferred file matches the guest SHA256.
- `ffprobe` reports the expected duration, dimensions, frame rate, and streams.
- The unified clip path strips source audio and aligns the clip to narration.
- A short recorded clip survives import, render, and human review.

The current read-only `Z:` share is not assumed to support export. The spike must select and verify a writable drop share or another transfer mechanism before video is promised.

## Rollout and acceptance criteria

### Phase 1: screenshot bridge

- `remote-uiqa-lab` can run a bounded screenshot capture job against `lab-win11` only.
- Every run has complete evidence, a pass/fail summary, a sanitized manifest, and control release on every handled exit, with idle-timeout recovery for forced termination.
- `demo-studio import-desktop` accepts passed bundles and rejects every failed or tampered case.
- A screenshot can be imported as a first-class still without generated card MP4s.
- No beat schema desktop actions, RustDesk MCP, or VM credentials enter `demo-studio`.
- Existing tests pass; offline/fake-server tests prove failure paths; one live run proves the real path.
- The final render passes the existing human review gate before any draft publication.

### Phase 2: approved installs and video

- Installer actions are pinned, hash-verified, explicitly approved, and recorded.
- Video recording and transfer pass the spike criteria.
- Imported clips use the unified clip path and contain no source audio.
- An optional convenience adapter may call the lab capture job, but only after the artifact contract is stable.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Desktop control code leaks into the renderer | Keep all actuation in `remote-uiqa-lab`; `demo-studio` imports files only. |
| A failed desktop run is mistaken for a usable visual | Require passed summary, released control, valid manifest, and matching hashes. |
| Secrets or personal data enter screenshots or commits | Guest policy, redaction, secret scan, gitignored runs, and export refusal. |
| The wrong machine is targeted | Hard-pin `lab-win11` and `97523850`; reject all other targets before control. |
| The lab endpoint changes tool schemas | Discover tools at runtime and fail on missing capabilities; record observed version. |
| Screenshot resolution or framing is poor | Preserve dimensions, probe on import, warn on aspect mismatch, and leave framing to the unified engine. |
| Video export is assumed before it exists | Keep video out of phase 1 and require a transfer/hash/probe spike. |
| The recreated lab is incomplete | Land bring-up, client, recorder, and smoke verification before capture jobs. |
| The known Escape failure produces false confidence | Keep it as a failing regression until fixed; do not use it as the first success template. |
| Automation expands into auto-publication | Preserve TTS-only final audio, `review.html`, and the explicit human approval gate. |

## Explicitly deferred

- Desktop actions in beat JSON.
- A `desktop` visual kind.
- Arbitrary remote PowerShell from capture requests.
- RustDesk MCP control.
- Continuous or long-running recording.
- Desktop audio capture.
- Automatic installer downloads in phase 1.
- Guest-to-host video transfer until the spike selects a verified mechanism.
- Automatic publication.
