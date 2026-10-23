# Tasks

## 1. The command

- [x] 1.1 `src/agentmarshal/cli.py`: `accept` gains a second mutually
  exclusive group — `--pause <extension>` and `--operational` — beside
  the required `--commit`/`--accepted-finding` binding group; the help
  names the three forms. `_run_accept` refuses `--accepted-finding`
  and `--finding` with either new flag, naming the flags, before
  placement resolves — verify: pytest.
- [x] 1.2 `src/agentmarshal/journal/acceptance.py`: a recording path
  beside `accept_findings` that loads the task through
  `load_task_for_record`, resolves `--commit` with
  `git rev-parse --verify <rev>^{commit}` in the journal's repository,
  checks `--pause`'s extension through `read_extension_manifest` on
  the journal repository's working tree, and writes through
  `create_acceptance_record`'s `accepted_pause`/`operational`
  parameters — every refusal before `write_record` — verify: pytest.

## 2. Tests

- [x] 2.1 `tests/test_pause_and_operational_acceptance.py`: a test per
  delta-spec scenario, each docstring naming the scenario — the pause
  acceptance written for a declared extension at the resolved commit
  in both manifest forms, the resolution and refusal cases, the
  operational acceptance needing no review, the flag refusals naming
  the flags, and the findings form pinned unchanged — verify: pytest.

## 3. Change and archive

- [x] 3.1 `openspec/changes/accept-pause-operational/`: proposal.md,
  design.md, tasks.md, and the delta spec under
  `specs/operator-acceptance/` — the ADDED requirements for the two
  forms and their exclusivity, and the MODIFIED readers requirement
  whose "nothing else SHALL act on the new forms" tail is now stale.
- [x] 3.2 `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2
  archive accept-pause-operational --yes`, once implementation and
  tests are complete.
