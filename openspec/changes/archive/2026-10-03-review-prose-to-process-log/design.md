## Context

ADR-0014 decision 1 puts review prose at `hash` and reviewer diagnostics at
any level in the process log, and ADR-0022 section 7 fixes the events that
announce them: `review-prose` — the path to the prose file and its sha256 —
and `review-diagnostics`. The launcher today keeps both in `tempfile.mkstemp`
files (`_preserve_accepted_output`, `_preserve_reviewer_diagnostics` in
`journal/review.py`), because the local state and the log did not exist when
that was written. CR-148's `localstate.py` resolves the clone's local state
in every placement and CR-153's `process_log.py` appends and reads events;
the step commands (CR-157) show how a command opens a writer and reports a
log that cannot be opened with a remedy. What remains is pointing the review
launcher's two preservation paths at that place.

## Goals

- At `hash` the accepted verdict's output is written byte for byte under the
  local state's process-log area and a `review-prose` event names the file —
  its path and its sha256 — and the task; the journal holds nothing.
- A successful reviewer command's stderr is kept the same way at every
  capture level, announced by a `review-diagnostics` event.
- Local state that cannot be used falls back to a temporary file, and stderr
  says why.
- In a sidecar the files and events go to the journal repository's local
  state, never the host's.

## Non-Goals

- Retention of kept files beyond the log's existing bound (CR-153).
- Reading the prose or the diagnostics back in any command.
- Any change at levels `commit` or `off`, or to the rejected-verdict copy.

## Decisions

- **Payload files live in `log/files/` under the local state, beside the
  writer files rather than among them.** `read_events` reads every regular
  file directly under `log/`, so a payload sitting there would have any
  line that happens to be a JSON object surface as a phantom event; a
  subdirectory is skipped by the reader and by the directory sweep alike —
  the sweep counts only regular files directly under `log/`, so payloads
  are neither swept nor counted. Retention for them beyond that bound is a
  declared non-goal. The event carries the file's absolute path, so the
  layout can move later without a format change.
- **`write_payload(state, prefix, content)` joins the process-log module.**
  It creates `log/files/` through `LocalState.ensure_directory` — the same
  contained creation the writer uses — and writes the bytes through
  `mkstemp` in that directory, returning the path. Keeping it in
  `process_log.py` puts the area's layout where the `log/` layout already
  lives and gives the later producers that name files in events —
  `check-output`, `provider-export` — the same primitive.
- **One helper in the launcher does resolve → payload → event.**
  `_local_state_output` resolves the local state of the repository that
  holds the journal — `local_state(resolve_placement(...))`, which asks git
  about `placement.project_root`, the journal's repository in both
  placements — writes the payload, opens a writer and appends the event
  with `path` and `sha256` fields and the task when there is one. In a
  sidecar that repository is the sidecar's, so the host never enters the
  call (ADR-0014 decision 5). Any failure on that path — a git that cannot
  name the common directory, a directory that cannot be created, an event
  that cannot be appended — is wrapped in a launcher-private
  `_LocalStateUnavailable` carrying the reason, so the caller's fallback
  catch stays one clause.
- **The imports are deferred into the helper.** `agentmarshal.journal`'s
  package init imports `review.py`, and a subprocess test pins that
  importing the gate never imports `agentmarshal.process_log`; a top-level
  import of `process_log` or `localstate` here would break that pin.
- **Fallback is per keep, and the note says why.** When
  `_local_state_output` raises, the caller writes the bytes to a temporary
  file exactly as today — same `mkstemp` prefixes — and the stderr note
  names the temporary path plus the reason the local state could not be
  used. Preservation stays best effort: a verdict the reviewer produced is
  never discarded because neither place could keep the bytes; the note
  degrades to carrying them, as today.
- **stderr keeps today's shapes.** `reviewer output kept at <path>
  (capture level: hash)` and `reviewer diagnostics kept at <path>` read the
  same whether the path is under `log/files/` or the temporary directory;
  the fallback appends the reason.
- **The diagnostics event carries the task and rides every outcome.**
  `_keep_diagnostics` still runs before the verdict is judged, so the file
  and the `review-diagnostics` event exist even when the verdict is later
  refused — the run succeeded and its diagnostics survive it, which is what
  the requirement promises. A dry run resolves the local state of the
  project it runs in — `find_project_root` of the working directory, the
  same project the command resolved — so its diagnostics land in the
  journal repository's log too, with no task on the event.
- **Levels `commit` and `off`, and the rejected-verdict copy, are
  untouched.** `commit` still pins the prose as a journal artifact; `off`
  keeps nothing; a rejected verdict's output still goes to a temporary
  file through `_preserve_output`.

## Risks

- [A payload file orphaned by an event-append failure] → the bytes are
  already under `log/files/` when the event fails; the note falls back to a
  temporary copy and says why, and the orphan is local working state under
  no retention promise — the same standing an abandoned writer file has.
- [Payloads grow `log/files/` without bound] → declared non-goal: retention
  beyond the log's existing bound is a later task, and the directory map's
  rule that nothing local is evidence means nothing depends on the files.
- [A sidecar resolves the wrong repository] → `local_state` asks git about
  `placement.project_root` — the journal's repository — by construction, so
  the host can only appear as a resolution failure, never as a write.
- [The gate imports the process log through the launcher] → the deferred
  imports keep `sys.modules` clean on a gate import, and the existing pin
  test demonstrates it.
