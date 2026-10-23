## 1. The gate

- [x] 1.1 `run_gate` reads `contract.require_agreement` through
  `agentmarshal.settings.require_agreement` from
  `journal_root.parents[1]` — the journal repository's `project.json`,
  the same working-tree read the `changes_required` threshold makes —
  on the implementation lane only, and an unreadable setting prints the
  WARN line, adding no violation — verify: the tests whose docstrings
  name the unreadable-setting and deterministic-lane scenarios
  (pytest).
- [x] 1.2 When the setting is true the gate computes the judged hash
  with `contract_sha256` over the contract it judges against — the
  merge-base `contract_text` in the embedded placement, the sidecar
  journal repository's `contract.md` in the other — and prints one
  PASS or FAIL line naming the short hash: PASS when the task's records
  hold an `agreement` whose `contract` equals it, FAIL saying agreement
  is recorded with `agentmarshal agree` otherwise, naming the latest
  `agreement` record's hash beside the judged one when the task carries
  agreements at another hash — verify: the tests whose docstrings name
  the pass, the two fail, the latest-names, the any-satisfies and the
  any-recorder scenarios (pytest).
- [x] 1.3 The check runs however `review_required` was asked and is not
  a review-bound check — verify: the test whose docstring names the
  not-review-bound scenario (pytest).
- [x] 1.4 With the setting absent or false the gate prints no agreement
  line and the transcript is today's byte for byte — verify: the test
  whose docstring names the absent-or-false scenario and the pinned
  fixtures, unchanged (pytest).

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the contract-governance
  delta are written — verify: `openspec validate
  gate-requires-agreement --strict`.
- [x] 2.2 Every scenario in the delta is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the
  spec's scenario headings.
- [x] 2.3 The change is archived with the archive command — verify: the
  delta's requirements land in
  `openspec/specs/contract-governance/spec.md` and the change lives
  under `openspec/changes/archive/`.
- [x] 2.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`, and the suite again
  under CI conditions — no actor override, no git identity — verify:
  run them.
