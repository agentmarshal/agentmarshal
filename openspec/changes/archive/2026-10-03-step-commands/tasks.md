## 1. The writer's failures

- [x] 1.1 `write_event` refuses with `ProcessLogError` an event that cannot
  be encoded as strict JSON — a non-finite number or a value whose type
  JSON cannot carry — before any line lands — verify: refusal tests for
  NaN and an unsupported type, and the file holds no new line.
- [x] 1.2 An `OSError` appending reaches the caller as a `ProcessLogError`
  naming the log file and what to do — verify: the test asserts the
  writer's path is named in the message.

## 2. `step start`

- [x] 2.1 `steps.py` registers the `step` group; `step start` takes
  `--task` (validated as a task id), `--activity` (the session activity
  vocabulary) and `--deadline` (required: an ISO-8601 time or a `<n><unit>`
  duration, units `s`/`m`/`h`/`d`), plus optional `--pid`, `--actor` and
  `--run-dir` — verify: the refusal tests and the help listing.
- [x] 2.2 `step start` writes one `step-started` event — a ULID `step`, the
  activity, `pid` (the command's parent by default), `pid_started_at`, the
  deadline normalized to a UTC ISO-8601 timestamp, and `actor`/`run_dir`
  only when given — and prints the step id — verify: the event-field
  tests and the printed id.
- [x] 2.3 `pid_started_at` reads `/proc/<pid>/stat` field 22 plus
  `/proc/stat`'s `btime` on Linux, `ps -o etime=` on other POSIX systems,
  and carries `unknown` where neither works — verify: a real read on
  Linux, and `unknown` for a pid that cannot be read.

## 3. `step end`

- [x] 3.1 `step end` takes `--task` (validated), `--step` and an optional
  `--outcome` — a non-empty word that cannot forge rendered text — and
  writes one `step-ended` event carrying `step` and, when given,
  `outcome` — verify: the event test and the outcome refusals.

## 4. Placement and the hook

- [x] 4.1 `cli.py` registers the group and dispatches `step` — the hook
  only — verify: `agentmarshal step --help` lists both subcommands.
- [x] 4.2 Neither command writes the journal; in a sidecar the event lands
  in the journal repository's process log — verify: the untouched-journal
  test and the sidecar test.
