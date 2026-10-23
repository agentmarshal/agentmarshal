## Context

ADR-0021 decision 3 settled the surfaces an acknowledgement prints
on: the command, the gate and `status` — every hit stays printed, an
acknowledged one marked with who acknowledged it and the reason, and
the gate shows the mark on the hits its line shows, within the bound
that line already has — at most twenty, then "and N more not shown" —
the bound neither widened nor narrowed by an acknowledgement.
Decision 2 fixed the binding: the record's `commit` equal to the
candidate's, its `file` equal to the hit's file exactly as the scan
prints it, and its identification equal to the hit's — a signature id
or `private-marker #<n>` — with no other matching. CR-190 landed the
mark on the standalone command: `render_leak_hits` gained the
optional per-hit `marks`, and `cli.py` gained the helpers that read
the journal's `acknowledgement` records and build each mark —
`_acknowledgement_identification`, which maps a record to the hit
identification it binds, and `_acknowledgement_mark`, which finds the
earliest record naming the hit and renders `acknowledged by
<recorded_by>: <reason>` through `mask_leaks` and
`escape_for_display`.

What reaches the gate today is already shaped for the read:
`load_task_status` hands `run_gate` the task's records in journal
order, the advisory block holds the scan's `leak_hits`, the trusted
`markers` and the `resolved_commit` — every input the match needs —
and `render_leak_hits` already knows how to carry a per-hit mark.

## Goals

- The gate's advisory leak-scan line marks each hit it shows that an
  `acknowledgement` record of the task acknowledges — same commit,
  same file as printed, same identification — with the same mark
  `leak-scan` prints, masked and escaped the same way.
- The bound is the line's own, unchanged: twenty shown, then "and N
  more not shown"; a hit beyond it takes no mark; nothing is removed
  or reordered.
- The mark code is shared, not forked: the gate builds marks through
  the same function the command prints them with.
- A run with no acknowledgement bound to the candidate is byte for
  byte today's line; the warning blocks nothing.

## Non-Goals

- Turning the warning into anything that blocks — the scan stays
  advisory (ADR-0005); a marked hit adds no violation.
- Self-acknowledgement marking on the gate's line — `status` carries
  that mark (ADR-0021 decision 5).
- Any change to the scan, to `leak-scan`'s output or exit status, to
  `acknowledge`, or to the record.
- Reading acknowledgements beyond the task's own records — the gate's
  surface is the task it runs on.
- Protection beyond the published threat model: a record authored
  under any identity is the stated boundary, not a defect this change
  fixes.

## Decisions

- **The records are `task.records`, filtered to the candidate's
  commit.** The gate already loads the task's records through
  `load_task_status` — in journal order, validated, in every lane —
  so the read adds no second lookup: `record_type ==
  "acknowledgement"` and `commit == resolved_commit`. The gate runs
  on one task, so the task's records are the whole surface: an
  acknowledgement on another task marks nothing here, the way a
  `--task`-scoped `leak-scan` reads only the named task's. A record
  bound to another commit marks nothing — the acknowledgement lives
  and dies with the exact commit it was given on.
- **The mark-building moves to `capture.py`, verbatim.** The two
  helpers are pure functions over record mappings, hits and markers —
  the scanner's module, beside `render_leak_hits` whose `marks`
  parameter exists for exactly this. The gate imports
  `_acknowledgement_mark` from there, so the mark's wording, masking
  and escaping cannot drift from the command's. One adaptation the
  move forces: `escape_for_display` is imported where the function
  runs — display.py stands on this module through records.py, so a
  module-level import back would cycle, the same resolution
  records.py's `ext` rule took for `extensions.py`. `cli.py` is
  outside this task's scope, so its private copies of the two helpers
  remain until the one-line switch to the shared ones lands — an
  identical text in both places, not a second implementation.
- **The marks ride `render_leak_hits`'s existing parameter.** Marks
  are computed one per hit over the same list the renderer bounds,
  and the renderer applies them to the shown entries only — a hit
  past twenty is never rendered, so its mark can appear nowhere, and
  the count it joins is computed on the same hits in the same order
  as today. With no matching record every entry is `None` and the
  rendered text is byte for byte the unmarked line.
- **No acknowledgement is not a failure.** An empty filtered list
  marks nothing — the line is today's, byte for byte — and no new
  failure mode is introduced: `load_task_status` already validated
  the records the filter reads, so a record too broken to load fails
  the run where it always has, not here.

## Risks

- [A second matcher drifting from the scan's naming] → the gate calls
  the very function `leak-scan` calls — the same equality the command
  applies, over `hit.path` and `hit.identification`, the same values
  the renderer prints.
- [The mark widening or narrowing the bound] → `render_leak_hits`
  computes `shown` from `hits` and `limit` exactly as before; marks
  only annotate shown entries. The bound tests pin twenty shown and
  "and N more not shown" with a marked hit on each side of the line.
- [A stale acknowledgement silently following the work] → the filter
  requires `commit == resolved_commit` and the match requires the
  printed file and identification: a new commit, a differently-spelled
  file or a renumbered marker shows the hit unacknowledged again —
  fail visible, never silent.
- [`recorded_by` or `reason` forging a transcript line] → both pass
  `mask_leaks` and `escape_for_display` inside the shared helper, and
  `say` escapes the finished line a second time — an idempotent pass
  that changes nothing.
- [The pinned transcript drifting] → a run with no acknowledgement
  bound to the candidate produces an all-`None` marks list and the
  unmarked rendering, byte for byte — the pinned fixtures stand.

## Open Questions

- None — ADR-0021 decided the binding, the mark's content and the
  surfaces; ADR-0022 section 3 fixed the record's fields.
