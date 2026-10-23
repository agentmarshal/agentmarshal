# Tasks

## 1. Command

- [x] 1.1 Create `src/agentmarshal/record_ext.py` with
  `register(subparsers)` and `run(args, stderr)`: argparse for
  `--task`, `--commit`, `--kind` and `--payload-file`; `run` resolves
  placement, admits the task through `load_task_for_record(..., "ext")`,
  resolves the commit to its full 40-hex id under
  `placement.project_root`, checks the kind's form and its declaration
  in `<name>`'s manifest through `read_extension_manifest`, reads the
  payload file as JSON, masks every string — object keys included —
  through `mask_leaks` with `markers_from_config`, rescanning the
  masked canonical form and bounding it at 64 KiB, resolves the
  recorder, builds through `create_ext_record`, preflights through
  `validate_record_for_write` and writes once; the masked-categories
  note and the undeclared-actor note go to stderr; every refusal prints
  its reason and writes nothing.
- [x] 1.2 Register the command in `cli.py`: one `from agentmarshal
  import record_ext` import, one `record_ext.register(subparsers)` line,
  one `if args.command == "record-ext"` dispatch.

## 2. Tests

- [x] 2.1 `tests/test_record_ext.py`: a test per delta-spec scenario,
  each docstring naming the scenario — the write and its output, the
  short/symbolic commit, the commit that does not resolve, the unknown
  and the terminal task, the malformed kind, the missing manifest, the
  undeclared kind, the unreadable manifest, the directory form, the
  masked value and the masked key with their categories named and the
  matched text nowhere, the hash over the masked payload, the colliding
  keys, the still-tripping masked form, the unreadable and the non-JSON
  payload file, the payload past 64 KiB, the non-finite number, no
  resolvable recorder, the undeclared recorder named, the declared
  actor quiet, the escaped recorder, and the journal untouched by a
  refused run — plus a `--help` test listing the flags.
- [x] 2.2 A sidecar test: the commit resolves in the sidecar's own
  repository, not the host's.

## 3. Change and archive

- [x] 3.1 `openspec/changes/record-ext-command/`: proposal.md,
  design.md, tasks.md, and the delta spec under
  `specs/extension-records/` — the ADDED requirements and the MODIFIED
  requirement whose "no command writes the record yet" tail is now
  stale.
- [x] 3.2 `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2
  archive record-ext-command --yes`, once implementation and tests are
  complete.
