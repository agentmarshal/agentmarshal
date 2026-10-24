## 1. The gate's line

- [x] 1.1 `gate.py` computes the candidate's writer identities — the
  range's declared author and committer names and emails, read by its
  own range lookup `_range_writer_identities` and decoded by the
  shared `report.decode_writer_field` — ahead of the verdict block,
  beside the emails-only set the reviewer-independence check keeps —
  verify: pytest.
- [x] 1.2 The acceptance PASS line appends ` (self-accepted: accepting
  party is a declared author or committer)` after the party when the
  shared comparison `report.accepting_party_is_declared_writer`
  matches `accepted_by` to the range's names and emails —
  byte-for-byte today for any other party — verify: pytest.

## 2. The report's line

- [x] 2.1 `report.py` derives a completed task's `decision` from the
  latest review and the latest findings-carrying acceptance bound to
  the `completed` record's own `completed_commit`/`completed_finding` —
  `approved` on an approving latest review, else
  `accepted-over-findings` — and keeps today's rule for a task with no
  `completed` record — verify: pytest.
- [x] 2.2 `report.py` derives `self_accepted` from the decisive
  acceptance's `accepted_by` against the accepted commit's declared
  writers in the placement's host repository, and `format_report`
  appends ` self-accepted` after the decision field — verify: pytest.
- [x] 2.3 `report.py` applies the shared comparison —
  `accepting_party_is_declared_writer` — to the accepted commit's
  declared writers looked up through `declared_commit_writers`, the
  same two functions `status_view` calls for its check — the gate
  reads writers through its own range lookup instead, so a writer of
  an earlier commit of the range earns the mark at the gate alone;
  the line carries the mark only where the self-acceptance is
  confirmed — where git cannot answer it prints as for any other
  acceptance and `status` alone says the check could not run —
  verify: pytest.

## 3. Scenarios and pins

- [x] 3.1 Every delta scenario has a test whose docstring names it —
  verify: `uv run pytest -q`.
- [x] 3.2 The existing gate, report and status tests and the transcript
  fixtures pass unchanged — a journal with no self-acceptance and no
  earlier-commit acceptance prints byte-for-byte today — verify:
  `uv run pytest -q`.

## 4. Checks and archive

- [x] 4.1 Full check sequence passes: `uv run agentmarshal validate`,
  `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`,
  `uv run mypy` — verify: run them.
- [x] 4.2 Archive with `OPENSPEC_TELEMETRY=0 npx -y
  @fission-ai/openspec@1.15.0 archive self-acceptance-on-every-surface
  --yes` — verify: the delta lands in
  `openspec/specs/operator-acceptance/spec.md` and the change moves
  under `openspec/changes/archive/`.
