## 1. Contained creation

- [x] 1.1 `ensure_directory` becomes a `LocalState` method refusing — with
  `LocalStateError` — a location that is not the root or under it, `..` and
  symlinks resolved before the check — verify: containment tests, and the
  existing creation tests calling it as `state.ensure_directory(…)`.
- [x] 1.2 `ensure_directory` returns the caller's own spelling of the
  location — resolution serves the check only — verify: the creation test
  asserts the returned path equals the one passed in.

## 2. The writer

- [x] 2.1 `open_writer(state)` creates `log/` through
  `state.ensure_directory` and claims a file named by UTC start time, pid and
  a random suffix — verify: two writers in one process get different files;
  the file sits under `state.log`.
- [x] 2.2 `write_event` appends `{"format": 1, "at", "event", "task"?, …}` as
  one JSON line, the file opened in append mode per call — verify: line-per-
  event test; task present only when given; extra fields carried.
- [x] 2.3 Two subprocesses appending at once lose and tear nothing — verify:
  the concurrent test reads every line of both files back.
- [x] 2.4 `write_event` refuses — with `ProcessLogError` — an event field
  naming an envelope key (`format`, `at`, `event`, `task`) — verify: the
  refusal test and no line landing.

## 3. Rotation

- [x] 3.1 At `ROTATE_AT_BYTES` (10 MiB) the current file is renamed `.1`,
  earlier suffixes shift up, `.5` is deleted — `ROTATED_KEEP` (5) rotated
  files at most — verify: rotation and retention tests at a patched-down
  constant; events after rotation land in the fresh file.
- [x] 3.2 A rotation whose renames fail — a reader holding the file — leaves
  the file and fails nothing; the next write retries — verify: the patched-
  rename test.

## 4. The directory bound

- [x] 4.1 `open_writer` deletes oldest-first by mtime while the directory
  totals more than `DIRECTORY_CAP_BYTES` (50 MiB): rotated files are
  candidates at any age, a current file only once quiet for
  `ABANDONED_AFTER_SECONDS` (24 h); skips are silent and never fail the
  open — verify: the bound tests at patched-down constants.

## 5. The reader

- [x] 5.1 `read_events(state)` returns every file's events ordered by `at`,
  rotated files included; a missing `log/` reads as empty — verify: ordering
  and rotated-file tests.
- [x] 5.2 An unterminated last line is skipped (parseable or not), a line
  that is not a JSON object is skipped, unknown kinds are returned unchanged,
  an unreadable `at` sorts first — verify: one test per case.

## 6. The boundary

- [x] 6.1 A subprocess test asserts importing `agentmarshal.journal.gate`
  does not import `agentmarshal.process_log` — verify: the test; grep that
  nothing under `src/` outside the module imports it.
