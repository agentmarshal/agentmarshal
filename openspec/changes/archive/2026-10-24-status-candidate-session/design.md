## Context

`status_view.py` ends `print_task_detail` with a family of derived
lines — the agreement line, the drift line, the deferrals and the
`changes_required` count — each a `str | None` or `list[str]` helper
whose output the dispatch escapes once through `escape_for_display`
(ADR-0015 decision 5), each appended after the additions before it. The
session record has carried `commit` since CR-160 and `report_ready`
with it; a review binds the commit it judged in `reviewed_commit`, or a
finding in `reviewed_finding` — exactly one, by the binding rule.

## Goals

- One line naming the implementer session that produced the commit the
  task's latest review judged — its id, actor, outcome and report-ready
  flag — saying plainly when that run did not end `implemented`.
- A candidate no implementer session claims stays exactly the view it
  is today.

## Non-Goals

- The refusal in `review` and the gate — a later task, under record
  schema 8, with the operator's override.
- Showing sessions for commits other than the latest reviewed one.
- `report` and the `status` list form.

## Decisions

- **The commit is the latest review's `reviewed_commit`.** The task's
  last `review` record wins — the same rule the gate holds an
  acceptance to, never searching backward for an older record that
  would justify a line. A review bound to a finding
  (`reviewed_finding`) judges no commit, so it produces no line; nor
  does a task holding no review at all.
- **Only implementer sessions name a producer.** The match is a session
  record whose `role` is `implementer` and whose `commit` equals the
  reviewed commit — exact equality over the whole 40-hex id, the way
  the gate's range check compares session commits. A session of another
  role naming the commit — a reviewer's, a coordinating run's —
  produces no line and does not count toward the earlier-sessions
  count.
- **The latest naming session is shown; the earlier ones are counted.**
  Stored order decides "latest"; the line gives the count of the
  others as `+N earlier implementer session(s)`. When no implementer
  session names the commit the line is absent and the view is byte for
  byte what it prints today — proposal 036's disposition keeps a
  candidate produced by a runner that wrote no session judged as it is
  now.
- **The line's shape.** `Reviewed commit <short>: implementer session
  <id> actor=<actor> outcome=<outcome>` — `report_ready=<true|false>`
  appended when the record carries the field, `(did not end
  'implemented')` appended when the outcome is not `implemented`, and
  the earlier-sessions count when several name it. `actor` and
  `outcome` render through `_shown_value`, so a record lacking either
  shows `(absent)` rather than failing — the same honesty the ran
  lines buy with it. The whole line goes through `escape_for_display`
  once — the same dispatch every derived line takes.
- **Placement is last of the derived lines.** The line appends after
  the `changes_required` count, as each derived line before it
  appended after the one before — so the bytes every existing pin
  checks do not move.

## Risks

- [A record carrying a forgeable value reaches the line] → the
  dispatch escapes the whole line once, as it does every derived line;
  the escaping scenario's test pins it.
- [The line could be read as a refusal] → it is a report like the
  count and agreement lines: nothing is refused, blocked or projected;
  a task whose producing session ended badly shows the fact, the
  refusal itself being a later task's work.
- [Sessions of other roles could inflate the count] → the match is
  `role == "implementer"` only; other roles neither show nor count.
