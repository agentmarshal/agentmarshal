## Context

ADR-0014's map of places puts the process log in `log/` under the clone's local
state — `.git/agentmarshal/log/` in an ordinary clone, the journal repository's
git directory in a sidecar — and `localstate.py` already resolves that
directory and the five sibling locations. What is missing is the module that
appends to it and reads it back. The events written later — step events, review
prose, check output, extension events — all take the shape ADR-0022 section 7
fixes: `{format: 1, at, event, task?, …}`.

## Goals

- One function appends an event and one function reads every event back; no
  caller formats a line or names a file itself.
- Two processes writing at once never interleave or tear each other's lines,
  without a lock.
- A file's size is bounded by rotation; retention deletes the oldest rotated
  files first, and the directory as a whole is bounded too — every process
  run is a writer, so per-writer retention alone bounds nothing.
- The reader tolerates a still-writing file, foreign lines and event kinds it
  does not know.
- Creating `log/` cannot create a directory outside the local state root.

## Non-Goals

- Any event producer (step commands, review prose, check output, extension
  events) or consumer (`status`, `doctor`) — later tasks; nothing calls the
  module yet.
- Configurable thresholds; the 10 MiB limit and the five-file retention are
  module constants.
- Atomic append semantics on a shared file — the one-file-per-writer decision
  removes the question.
- Durability or forgery protection (ADR-0014 decision 8): the log is a local
  working log, and a process running as the same user can rewrite it whole.

## Decisions

- **One file per writer, named by start time, process id and a random
  suffix.** A writer's file is
  `<UTC start>-<pid>-<random hex>.jsonl`, claimed exclusively when the writer
  opens. The alternative — one shared file relying on atomic appends — puts a
  POSIX-only guarantee under every write (`O_APPEND` and a short write are not
  promised atomic on every filesystem, and nothing like them exists to rely on
  on Windows) and still needs a lock for interleaved records. With a file of
  its own, a writer is the only process that ever appends to its file, so two
  writers at once cannot interleave or tear each other's lines by
  construction — no lock, on any platform. Start time and pid keep the name
  readable and roughly ordered; the random suffix covers two writers in one
  process and pid reuse across runs. The reader does not parse names — it
  reads every file in the directory — so the scheme can change later without
  a format change.
- **Appends open in append mode and write one line per call.** Each event is
  serialized to one JSON object (`format`, `at`, `event`, optional `task`,
  then the event kind's own fields) and written as a single line with a
  trailing newline; the handle is opened for that one write and closed, so a
  rotated file is never held under its old name and Windows file semantics
  are met with plain `pathlib`/`os` calls — no `fcntl`. The line written per
  call is the unit a reader either sees whole or not at all: a crash mid-line
  leaves an unfinished last line, which is exactly the case the reader
  tolerates.
- **The writer stamps `at` itself.** `at` is the UTC ISO-8601 timestamp taken
  at write time; the caller names the event kind, an optional task id and the
  event's own fields — never the envelope keys. Keeping the envelope in one
  place is what makes "the key is `event`, not `kind`" hold for every later
  producer. (`write_event` accepts an explicit `at` so tests and producers
  recording a past moment can pin it; it is normalized to UTC.)
- **An event field naming an envelope key is refused, not merged.** The
  alternative — applying the envelope after the fields — would let a caller
  write `format` or `at` believing it set the key while the writer silently
  rewrote it. Refusing with a `ProcessLogError` makes the envelope's
  ownership loud, and the check is cheap: only `format` can even reach
  `**fields` through the signature today, but all four keys are checked so
  the rule survives a signature change.
- **Rotation is a rename to a sequence suffix, checked after the write.** When
  the current file reaches `ROTATE_AT_BYTES` (10 MiB) it is renamed
  `<name>.1`, the previous `.1`…`.4` shift one suffix up, and `.5` is deleted —
  so at most `ROTATED_KEEP` (5) rotated files exist per writer and the oldest
  is deleted first. Shifting suffixes, rather than numbering ever upward,
  keeps the rotated set bounded and self-describing: `.1` is always the
  newest rotation. The check runs after the append, so a burst can overshoot
  the limit by one line — the bound is on files kept, not on the line that
  crosses it. Only a writer rotates its own files, so rotation needs no
  coordination either. A rename can still fail — on Windows a reader holding
  the file blocks it — so `write_event` treats any `OSError` from rotation
  as "try again at the next write": the event is already durable, the file
  keeps its name and nothing is lost.
- **The directory is bounded as a whole, at open.** Rotation bounds one
  writer's files; it cannot bound the directory, because every process run
  is a writer of its own and dead writers' current files accumulate forever.
  So `open_writer` deletes oldest-first — by modification time, not name:
  names carry the writer's start time, but the mtime says when anything last
  touched the file, and "oldest" for retention means least recently used —
  while the regular files total more than `DIRECTORY_CAP_BYTES` (50 MiB).
  The candidate rule is chosen so no lock or liveness probe is ever needed:
  a rotated file is a candidate at any age — a writer never appends to a
  `.N` file again — and a current `.jsonl` file only once it has been quiet
  for `ABANDONED_AFTER_SECONDS` (24 h), since a younger one may still belong
  to a running writer and is left alone. Anything else — foreign files,
  entries that vanished, unlinks the platform refuses — counts toward the
  cap but is skipped, so the bound is best-effort and never fails an open.
  The residual risk is a writer silent for a whole day losing its file to a
  sweep; its next append starts a fresh file, so the cost is lost events in
  a working log, never a torn line.
- **The sweep runs before the writer's own file exists.** `open_writer`
  bounds the directory before it claims a name, so even a zero abandonment
  age could not make the sweep take the file it is about to return.
- **The reader returns events, not lines.** Every regular file in `log/` —
  current and rotated — is read; the events of all files come back as one
  list ordered by `at` (events sharing an `at` keep file-then-line order).
  Three tolerances are deliberate: a file's last line is skipped unless it is
  newline-terminated — a writer may still be holding it, and an unterminated
  line is skipped even if it happens to parse, because "complete so far" is
  not "complete"; a line that does not parse to a JSON object is skipped —
  torn writes and foreign content must not fail the read; and an event kind
  the reader does not know is returned unchanged as data — new kinds written
  by later tasks or extensions must not break older readers. An event whose
  `at` is missing, not a string, or not a readable UTC timestamp is kept and
  ordered before the dated events — it is data like any other, it simply has
  no place in the ordering. A missing `log/` directory reads as empty: a
  clone that has logged nothing has no events, which is not an error.
- **Creation goes through `LocalState.ensure_directory`, which now checks
  containment.** The creation call becomes a method on `LocalState` — the
  root it checks against is then the resolved root itself, not a second
  argument a caller could get wrong, mirroring how `local_state` takes the
  `Placement` so a caller cannot ask about the wrong repository. The location
  must resolve to the root or a path under it — `..` segments and symlinks
  are resolved before the check, so a location that only *looks* under the
  root is refused with a `LocalStateError`. Resolution serves the check
  only: the call returns the caller's own spelling of the location, so a
  caller holding `state.log` gets `state.log` back and never a resolved
  alias of it. The process log creates `log/` through this call; later
  writers (extensions, deps, the plan file) get the same containment for
  free.
- **The gate never sees the module.** The module sits at
  `agentmarshal.process_log`, outside `agentmarshal.journal`, and imports
  nothing the gate imports; a subprocess test pins that importing
  `agentmarshal.journal.gate` does not put `agentmarshal.process_log` in
  `sys.modules` (ADR-0014 decision 3).

## Risks

- [A writer's file is deleted or rotated away under it] → only the owning
  writer rotates, and the directory sweep never takes a file quiet for less
  than the abandonment age; a hostile same-user process can always rewrite
  the log — ADR-0014 decision 8 accepts that.
- [A writer silent past the abandonment age loses its file to the sweep] →
  its next append creates a fresh file, so the cost is earlier events lost
  in a working log, never a torn line.
- [A burst crossing 10 MiB between checks] → the check runs after every
  append, so overshoot is bounded by one line.
- [Events clock-skewed across machines] → the log is local to one machine
  (ADR-0014 decision 8); within it, `at` ordering is as good as the system
  clock, and events with equal `at` keep a deterministic order.
- [A non-directory entry or unreadable file in `log/`] → the reader skips
  non-files and files it cannot read; `log/` is reserved for the process
  log, and foreign content degrades to skipped lines, not a failed read.
