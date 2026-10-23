## Context

`build_report` already loads each task's validated records through
`load_task_status` (one task for `--task`, `list_task_statuses`
otherwise) and `format_report` renders the tab-separated lines —
`include_summary=False` marks the `--task` view. The records carry what
the decisions read: a session's `cost` is an object of exactly `amount`
(a non-negative decimal written as a string), `currency` (three
uppercase ASCII letters) and `source` (`reported` or `estimated`) —
the schema-7 field CR-176 landed and CR-188's flags write; a `check`
record carries `commit`, `name` and `result` (`passed`, `failed`,
`error`, `skipped`); a review's `classes` maps finding id to class; a
`completed` record's `advisory_dispositions` maps each advisory finding
id of the review the gate passed on to `disposition`, `reason` and, on
`deferred` only, `follow_up`.

## Goals

- `report --task` prints, after the round lines it prints today, the
  task's cost per currency — `reported` and `estimated` summed apart,
  nothing converted — the count of sessions carrying no cost, and the
  count of distinct commits a `check` record marked `failed` or
  `error`, next to the review rounds.
- `report` prints the same cost sums, no-cost count and rejected-commit
  count in aggregate, after the `Lead` line it prints today.
- `report --findings` prints the finding classes recorded on reviews
  across the tasks in scope — each with a count and up to three example
  finding ids — and the deferred advisory dispositions of their
  `completed` records still open, each with task, finding id, reason
  and follow-up.
- What `report` and `report --task` print today stays first and
  unchanged; every value the new lines take from a record is escaped on
  display; no other command changes.

## Non-Goals

- Currency conversion, price lists, or estimating a cost from tokens —
  the contract's own non-goals.
- Review-by dates on deferrals.
- Resolution-mode reviews (the mode is not implemented).
- Per-task cost or check figures inside the aggregate view's task
  lines: those lines print today and stay byte for byte.

## Decisions

- **Amounts sum as `decimal.Decimal`, never floats, and print in plain
  decimal notation.** The record carries `amount` as a string
  (`"0.42"`) so a sum is exact; `Decimal` keeps it exact — a float
  would print `3.3000000000000003` for what the journal holds as
  `1.10` + `2.20` — and `format(amount, "f")` keeps a small sum a
  decimal (`0.000000001`, never `1E-9`). The figure the line prints is
  the sum the journal holds, carried in the same decimal spelling the
  records use.
- **One line per currency, `reported` and `estimated` apart.** A sum in
  one currency is a figure the journal holds; a conversion would assert
  an exchange rate it does not (ADR-0019 decision 4). `Cost	USD
  reported=12.34	estimated=0.50` prints each source present on the
  line, currencies sort by code, and `Cost
  sessions_without_cost=N` names the sessions carrying no `cost` — a
  count, printed whenever the scope holds a session, so "no cost" is a
  count rather than a zero sum: a task or a journal with no cost
  recorded shows no currency line at all (ADR-0019 decision 4's "none
  rather than zero").
- **The refused count is of distinct commits, not records** — the
  candidates the pipeline rejected (ADR-0017 decision 3): two `check`
  records marked `failed` or `error` on one commit are one rejected
  candidate, and `passed` and `skipped` do not count — the same two
  results `brief`'s last-failing-check section reads. In `--task` the
  `Checks	rejected_commits=N` line sits next to the review rounds —
  after the `Cost` lines, as the ADR's "next to rounds and cost" says —
  and in aggregate the same line follows the `Cost` block. A check
  record is the observer's declaration of what the pipeline found on
  the commit, not proof of it (ADR-0017 decision 2), and the report
  says so once, in one line after the `Checks` line — the sentence the
  brief's last-failing-check section already uses.
- **`report --findings` is a different listing, not extra lines.** The
  flag prints the findings view instead of the economics report — a
  `Classes` line per finding class and a `Deferrals` line per still-open
  deferral — so it composes with `--task` the way `--task` composes
  today: `--task` scopes the journal the view reads. `Classes	(none)`
  and `Deferrals	(none)` mark an empty section rather than printing
  nothing.
- **A deferral is open while its follow-up is unmet.** The `deferred`
  entries of `advisory_dispositions` on `completed` records are open
  while `follow_up` names no task or names a task the journal does not
  hold as completed — `load_task_status` answers that, and its failure
  is the "not held" answer, not an error (the same reading
  `status`'s deferral section makes). A follow-up held as `done`
  closes the deferral; `open`, `abandoned` and every other projection
  leave it open, and the line names which. `fixed` and `rejected`
  entries are not deferrals and are not listed.
- **The new lines append after today's.** The task line, the `Phases`,
  `Durations` and `Round` lines, the per-task lines, `Summary` and
  `Lead` all print byte for byte first — a test pins the prefix — and
  every value the new lines take from a record (a currency, a class
  name, a finding or task id, a reason, a follow-up) is escaped where
  it is interpolated, the same rule the view already follows
  (ADR-0015 decision 5).
