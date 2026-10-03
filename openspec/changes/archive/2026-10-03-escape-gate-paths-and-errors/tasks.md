## 1. Errors and refusals escape what they carry

- [x] 1.1 `GateError` escapes its message at construction through
  `escape_for_display`, so every value carried into an error or refusal —
  a ref echoed in a failed git command, an exception's text, git's own
  error output — prints escaped, including messages raised by the gate
  context and ones a lifecycle or review wrapper re-quotes — verify: a
  run whose `--commit` carries a newline prints the ref escaped on
  stderr and raises the escaped message.
- [x] 1.2 `_placement` in `cli.py` escapes a `PlacementError`'s text
  where the CLI prints it — the message can carry the sidecar host from
  `project.json` or git's own error text — verify:
  `test_a_placement_refusal_names_a_forgeable_host_in_escaped_form`.

## 2. Candidate paths are named in escaped form

- [x] 2.1 A test commits a file whose name carries a newline and shows
  the scope line naming it escaped, with `gate: passed` printed nowhere
  it was not — verify: `test_a_candidate_path_that_would_forge_a_line_is_named_in_escaped_form`.
- [x] 2.2 A test commits a file whose name carries a right-to-left
  override and shows it named escaped — verify:
  `test_a_path_carrying_a_refused_character_is_named_in_escaped_form`.
- [x] 2.3 A test renames a newline-named file into scope and shows the
  scope line naming the source escaped — verify:
  `test_a_rename_source_carrying_a_refused_character_is_named_in_escaped_form`.
- [x] 2.4 Each test skips with a reason where the filesystem refuses
  such names — verify: read `_write_or_skip` and `_write_bytes_or_skip`.
- [x] 2.5 The base tree's `git ls-tree -r --name-only` and the journal
  history's `git log --name-only` read `-z` like the gate's other
  listings, so a name git C-quotes is matched by the path itself —
  verify: `test_a_record_collision_names_a_path_carrying_a_refused_character_in_escaped_form`,
  `test_a_tampered_evidence_path_carrying_a_refused_character_is_named_in_escaped_form`
  and `test_an_unusual_file_name_is_matched_by_its_real_path_not_gits_quoted_form`.
- [x] 2.6 Every `-z` listing decodes `surrogateescape` through
  `_run_git_lossy`: a name whose bytes are not UTF-8 keeps its bytes for
  matching and never refuses the run, printing escaped where the gate
  names it — verify:
  `test_a_path_whose_bytes_are_not_utf8_is_named_in_escaped_form` and
  `test_a_base_tree_path_whose_bytes_are_not_utf8_is_named_in_escaped_form`;
  the strict decode stays for `git show`, so
  `test_gate_refuses_non_utf8_git_output` still pins the refusal.

## 3. Specs

- [x] 3.1 An ADDED delta gives record-text-safety the requirement that
  the gate escapes every value it did not write itself, each scenario
  demonstrated by a test whose docstring names it — verify: `openspec
  validate escape-gate-paths-and-errors --strict`.
- [x] 3.2 A MODIFIED delta restates scope-enforcement's "A candidate's
  change set names every path it touches" with paths matched raw and
  named in escaped form, keeping every existing scenario and adding one
  for a name matched by its real path rather than git's quoted form —
  verify: the same.

## 4. Nothing that worked changed

- [x] 4.1 A candidate whose values carry no refused character renders
  byte-identically: the pinned gate fixtures and every existing gate
  test pass unchanged — verify: `uv run pytest -q` and the
  byte-identical delegate test.
- [x] 4.2 The full CI sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv run
  ruff format --check`, `uv run mypy` — verify: run them.
