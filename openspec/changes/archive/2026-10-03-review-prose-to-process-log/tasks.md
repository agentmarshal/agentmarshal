## 1. The payload area

- [x] 1.1 `process_log.write_payload(state, prefix, content)` creates
  `log/files/` through `state.ensure_directory` and writes the bytes through
  `mkstemp` in that directory, returning the path — verify: the file sits
  under `log/files/` with the content byte for byte, and `read_events` never
  returns it as an event.

## 2. The launcher keeps output under the local state

- [x] 2.1 `review.py` gains `_local_state_output` — resolves the local state
  of the repository holding the journal, writes the payload, appends the
  event with the task, `path` and `sha256`; deferred imports; failures wrap
  as `_LocalStateUnavailable` — verify: importing the gate still does not
  import `agentmarshal.process_log`.
- [x] 2.2 At `hash` the accepted verdict's output lands under `log/files/`
  byte for byte, a `review-prose` event carries the task, path and sha256,
  stderr names the path as today, and the journal holds nothing — verify:
  the updated default-level test.
- [x] 2.3 Successful reviewer stderr is kept the same way at every capture
  level, announced by `review-diagnostics`, including on a dry run —
  verify: the updated warning test and the every-level test.
- [x] 2.4 Local state that cannot be used falls back to a temporary file
  with the reason said; `commit`, `off` and the rejected-verdict copy are
  unchanged — verify: the fallback tests and the unchanged-level tests.
- [x] 2.5 In a sidecar the files and events land in the sidecar's local
  state and the host's is untouched — verify: the sidecar test.

## 3. The sweep and the bound's requirement

- [x] 3.1 `_bound_directory` never follows a symlink — a `files/` entry
  that is not a real directory is skipped whole, and any entry that is not
  a regular file is never unlinked — verify: the symlinked-area and
  symlinked-entry tests.
- [x] 3.2 The change's delta modifies the process-log requirement "The log
  directory is bounded as a whole" so it names payload and staging files
  as deletion candidates and the no-symlink rule — verify: `openspec
  validate review-prose-to-process-log`.
