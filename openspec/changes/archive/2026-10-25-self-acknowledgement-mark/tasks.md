## 1. The shared derivation

- [x] 1.1 `report.py` holds
  `acknowledging_party_is_declared_writer(record, writers,
  journal_root)` — the record's actor git identities through
  `_actor_git_identities` plus the recorded name, each against
  `accepting_party_is_declared_writer`; `writers` of `None` yields
  `None` — verify: pytest.
- [x] 1.2 `status_view`'s `_is_self_acknowledged` is the shared
  derivation applied to the record's commit — same output —
  verify: pytest.

## 2. The mark and its callers

- [x] 2.1 `capture._acknowledgement_mark` takes the check as a
  `self_acknowledged` predicate and prints `self-acknowledged` in
  place of `acknowledged` only where it answers `True` — masking and
  escaping untouched — verify: pytest.
- [x] 2.2 `leak-scan` compares over the scanned commit's declared
  writers read through `declared_commit_writers`; a lookup git cannot
  answer leaves the mark as for any other acknowledgement —
  verify: pytest.
- [x] 2.3 The gate's advisory compares over the candidate range's
  writer identities — the verdict block's lookup reused where it ran,
  read beside the advisory where it did not, a lookup failure leaving
  the mark unmarked — verify: pytest.

## 3. Scenarios and pins

- [x] 3.1 Every delta scenario has a test whose docstring names it —
  verify: `uv run pytest -q`.
- [x] 3.2 The existing leak-scan, gate and status tests and the
  transcript fixtures pass unchanged — a non-self acknowledgement
  prints byte-for-byte today — verify: `uv run pytest -q`.

## 4. Checks and archive

- [x] 4.1 Full check sequence passes: `uv run agentmarshal validate`,
  `uv run pytest -q`, `uv run ruff check`, `uv run ruff format
  --check`, `uv run mypy` — verify: run them.
- [x] 4.2 Archive with `OPENSPEC_TELEMETRY=0 npx -y
  @fission-ai/openspec@1.15.0 archive self-acknowledgement-mark
  --yes` — verify: the delta lands in
  `openspec/specs/leak-scan/spec.md` and the change moves under
  `openspec/changes/archive/`.
