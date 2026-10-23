## Context

ADR-0021 decision 2 bound an acknowledgement to the candidate's
commit, the file exactly as the scan prints it and the hit's
identification — a signature id or `private-marker #N`, never the
matched text — and decision 3 decided the surfaces: every hit stays
printed, an acknowledged one marked with who acknowledged it and the
reason, and what changes is the command's exit status — an
acknowledged hit no longer makes `leak-scan` exit 1, a hit nobody
acknowledged still does. ADR-0022 section 3 gave the record its
schema-7 shape — `commit`, `file`, `signature` xor `marker`, `reason`,
`recorded_by`/`recorded_by_source` — and CR-170 landed the record,
CR-184 the `status` line, CR-187 the `acknowledge` command that checks
a hit against the scan before writing it.

What reaches the command today is already shaped for the read:
`LeakHit` carries `path` (masked through `safe_path`, exactly as the
hit prints) and `identification` (the signature id or
`private-marker #N`); `read_records` validates a task's records;
`list_task_statuses`/`load_task_status` are how the other commands
enumerate and load them; and `_run_leak_scan` already resolves the
placement whose `journal_root` is where the gate reads records — the
calling checkout's working tree in the embedded placement, the journal
repository's working tree under a sidecar (ADR-0014).

The scan takes no task today, and none needs guessing: an
acknowledgement binds a commit, so reading every task's
acknowledgements for the resolved commit finds the right ones without
deriving a task from a branch name. `--task` narrows that read for the
caller that already knows which task the verification belongs to.

## Goals

- `agentmarshal leak-scan --base <ref> --commit <rev> [--task <id>]`
  marks an acknowledged hit — acknowledged, by whom, and the reason —
  and exits 1 only on a hit nobody acknowledged.
- The match is ADR-0021 decision 2's exactly: the record's `commit`
  equals the resolved candidate commit, its `file` equals the hit's
  printed file, and its identification equals the hit's — no other
  matching.
- A journal or a task that cannot be read acknowledges nothing and is
  said on stderr; a repository with no journal behaves exactly as
  today.
- The gate's line, its bound and every pinned transcript are byte for
  byte unchanged.

## Non-Goals

- The gate printing the mark on its leak-scan line, or any change to
  its bound — a later task.
- Self-acknowledgement marking in the command's output — `status`
  carries that mark (ADR-0021 decision 5) since CR-184.
- Any change to what the scan matches, to the record, or to
  `acknowledge`.
- Protection beyond the published threat model: a record authored
  under any identity is the stated boundary, not a defect this change
  fixes.

## Decisions

- **The read lives in `_run_leak_scan`, over the status loaders.**
  The command resolves the candidate with `git rev-parse --verify
  <rev>^{commit}` in `scan_root` — the host under a sidecar, where the
  candidate's commits live and where `acknowledge` resolved the same
  ref — then reads `acknowledgement` records through
  `load_task_status` for a `--task` and `list_task_statuses`
  otherwise, the loaders `status` itself uses, over
  `placement.journal_root`. A record counts when its `commit` equals
  the resolved id. Reading through the status loaders means a task
  whose records cannot be projected is a task whose records cannot be
  read — the failure direction the contract names.
- **Any read failure acknowledges nothing.** The whole lookup sits
  under one guard — commit resolution included: a task `--task` names
  that is unknown, a record that fails validation, a journal that
  cannot be listed each print `leak-scan: cannot read
  acknowledgements: <why>` on stderr, escaped the way every
  tool-uncontrolled value is, and every hit counts as unacknowledged.
  That is the safe direction: a lost acknowledgement costs the
  operator an exit 1 they already had today, while a wrongly-counted
  one would silence a hit. A repository carrying no project at all
  skips the read outright — no journal is no failure — except a
  `--task` there, which names records that cannot be read and is said
  so.
- **The match is the record's fields against `LeakHit`'s.** A record
  acknowledges a hit when `record["file"] == hit.path` — the masked
  path exactly as the scan prints it — and the record's
  identification equals `hit.identification`: `signature` where the
  record carries one, `private-marker #<n>` for its `marker` — the
  same equality `acknowledge` applies when it checks a hit against the
  scan. No normalisation, no case folding: a spelling the scan never
  printed acknowledges nothing, and a marker renumbered since the
  record wrote shows the hit unacknowledged again, the fail-visible
  ADR-0021 decision 2 requires. Where several records match one hit,
  the earliest in journal order marks it — tasks in canonical order,
  records in their stored order.
- **The mark rides the shared renderer as an option, not a fork.**
  `render_leak_hits` gains an optional `marks` — one entry per hit;
  the gate calls it without one and renders byte for byte as today,
  and the command passes `acknowledged by <recorded_by>: <reason>`
  for the hits its records name, wrapped by the renderer in
  parentheses on the hit's own entry. `recorded_by` and `reason` go
  through `escape_for_display` before they reach the renderer — a
  `recorded_by` the write rules never constrained can still carry a
  line-forging character on read, and it can neither add a line nor
  reorder one. The matched text is in neither the record nor the hit,
  so it can be in neither mark nor output.
- **The exit status follows only what nobody acknowledged.** `0`
  when the scan reports hits and every one is acknowledged, `1` when
  any is unacknowledged — including the every-read-failed case — and
  today's behaviour untouched on a clean scan. The hits line, the
  best-effort note and the undecodable-file caveat keep their wording
  and their streams.

## Risks

- [A second matcher drifting from the scan's naming] → the record's
  fields are compared to `hit.path` and `hit.identification` — the
  very values the renderer prints — the same comparison
  `acknowledge` ran at write time, so what `leak-scan` honours is
  what `acknowledge` verified.
- [An acknowledgement read weakening a refusal into silence] → the
  read is one guarded block that can only ever turn hits *off* the
  acknowledged side: on any failure the command degrades to today's
  exit 1 on hits, never to a quieter result than today gives.
- [`recorded_by` or `reason` forging a transcript line] → both pass
  `escape_for_display` before the mark is built, the same escaping
  every displayed record value gets; a `\n` or a bidi control prints
  as its escape.
- [The gate's transcript drifting] → `render_leak_hits`'s new
  parameter defaults to the old rendering — the gate's call is
  untouched and its fixtures and pinned transcripts stay green.

## Open Questions

- None — ADR-0021 decided the binding, the mark's content and the
  surfaces; ADR-0022 section 3 fixed the record's fields.

Correction 2026-10-23 (CR-195): this design is wrong where it says the
matched text is in neither the record nor the hit, so in neither mark
nor output — `recorded_by` and `reason` are the operator's own text
and can carry the very string the scan matches. The mark in fact
passes `mask_leaks` before `escape_for_display`, and that masking —
not the absence this design claims — is what keeps the value out of
the output.
