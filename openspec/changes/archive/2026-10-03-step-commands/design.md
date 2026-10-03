## Context

CR-153 shipped the process log — one file per writer under the local state's
`log/` directory, one JSON object per line — and ADR-0022 section 7 fixed the
step events' fields: `step-started` carries `step`, `activity`, `pid`,
`pid_started_at`, `deadline` and optionally `actor` and `run_dir`;
`step-ended` carries `step` and `outcome`. The amended ADR-0014 decision 9
declined a `step` extension stage: the core records the events and starts no
background process; the watchdog and monitor are a supplied component the
harness runs. This change is the event producer. `status` and `doctor`
reading them back is a later task.

## Goals

- A harness announces a step and its deadline in one command, and closes it
  in another.
- The commands write only the process log — never the journal; in a sidecar
  they write the journal repository's log, never the host's.
- Every failure reaches the caller as a named error, never a traceback.

## Non-Goals

- Reading the events: overdue steps in `status` and `doctor` are a later
  task.
- Any watchdog, heartbeat or process control — a supplied component's job.
- A `step` extension stage — the amendment declined it.
- Correlating start and end: `step end` records what it is given; matching
  ids is the reader's work.

## Decisions

- **One module owns the group; `cli.py` gets only the hook.** `steps.py`
  exposes `register(subparsers)` and `run(args, stderr)` — the shape
  `outbox.py` sets — so `cli.py` adds the parser group and dispatches on
  `step` and holds no step logic of its own.
- **Placement resolves the journal repository; the host never enters.** The
  commands find the project and resolve the placement the way the other
  journal commands do — `find_project_root` then `resolve_placement`,
  without the host check — and open the writer against
  `local_state(placement)`. `local_state` always names the git common
  directory of the repository that holds the journal, so in a sidecar the
  event lands in the sidecar's own `agentmarshal/log/` and the host is
  never written.
- **The step id is a ULID.** `generate_ulid` is already the journal's id
  source — sortable and collision-safe across processes — so a step id
  needs no machinery of its own. `step start` prints it bare on stdout for
  a harness to capture.
- **The deadline is required and takes two spellings.** An ISO-8601 time —
  a naive one reads as UTC, the way the writer reads a naive `at` — or a
  duration `<n><unit>` with units `s`, `m`, `h` and `d`, measured from the
  command's run: `90m` is the deadline of a step allowed an hour and a
  half, which is how a harness says "judge me late after this". Both land
  in the event normalized to a UTC ISO-8601 timestamp, so a reader never
  parses two shapes.
- **Without `--pid` the parent process is recorded.** A harness runs
  `agentmarshal step start` as its child, so `os.getppid()` names the
  process the step belongs to; `--pid` overrides it for a caller announcing
  a step on another process's behalf.
- **`pid_started_at` is read where the platform allows and names itself
  unknown where it cannot.** On Linux it is field 22 of
  `/proc/<pid>/stat` — clock ticks since boot — added to the boot time
  `btime` in `/proc/stat`, at `SC_CLK_TCK` ticks a second. On other POSIX
  systems the portable fallback is `ps -o etime= -p <pid>`: its
  elapsed-time format `[[dd-]hh:]mm:ss` is numeric rather than
  locale-dependent, and the start time is now minus the elapsed span.
  Everywhere else — Windows, a missing `ps`, a dead or unreadable pid,
  output that does not parse — the field carries the string `unknown`
  rather than a guess: a wrong start time defeats the field's purpose,
  which is disambiguating pid reuse, and the command still works.
- **The outcome is a word that cannot forge rendered text.** `step end`'s
  optional outcome will be printed by `status` and `doctor`; like the
  session outcome vocabulary it is any non-empty word — no whitespace —
  and it must pass `forges_rendered_text`, the same predicate the journal
  applies to text it renders.
- **The writer refuses what strict JSON cannot carry, before the line
  lands.** `json.dumps` with `allow_nan=False` raises on NaN, infinity and
  types JSON cannot carry; `write_event` wraps that in a `ProcessLogError`
  rather than appending a `NaN` literal a strict reader would skip
  silently.
- **An `OSError` appending is an error that names the file.** The open and
  write happen inside the `try`; a failure — permissions, a full
  filesystem, a directory where the file was — becomes a `ProcessLogError`
  naming `writer.path` and what to do, so the CLI prints a sentence, never
  a traceback (carried from the CR-153 review).

## Risks

- [The parent pid is reused between start and end] → `pid_started_at`
  exists for exactly that: a reader correlating a step compares both, and
  an unresolvable start time reads `unknown` rather than corroborating the
  wrong process.
- [`ps` output differs across platforms] → only `etime=` is parsed, whose
  format POSIX spells out; anything that does not parse returns `unknown`.
- [A step is never ended] → by design: a step past its deadline shows from
  its start event alone; `step end` is the optional close for a step that
  ends with no record, or to record an outcome.
- [A clock correction between the `ps` read and the subtraction] → the
  elapsed span is one process's own measure; a skewed result is a degraded
  field in a local working log, and `unknown` stays the honest answer when
  the read cannot be made at all.
