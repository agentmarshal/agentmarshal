## 1. The command group

- [x] 1.1 `stages.py` registers `stage` with a `run` subcommand taking
  `--phase`, `--task`, `--commit` and `--base`, and dispatches through
  `run` the way `steps.py` does — verify: parser test.
- [x] 1.2 `cli.py` registers the group and dispatches `stage` —
  verify: parser and help tests.

## 2. Discovery at the base

- [x] 2.1 `--commit` and `--base` resolve with the gate's
  `_resolve_commit`; the merge base names the tree every trusted input
  is read from — verify: tests.
- [x] 2.2 `_base_manifests` enumerates the tree's
  `.agentmarshal/extensions/` — tree entries are directory-form
  extensions, `<name>.toml` the file form, a link at `.agentmarshal`,
  `extensions/` or a `<name>` refused — and reads each through
  `_manifest_from_tree` — verify: tests.
- [x] 2.3 `--phase` selects `pre-gate-warn` + `pre-gate-stop` or
  `post-gate`; extensions run in sorted-name order, matching stages in
  manifest order — verify: tests.
- [x] 2.4 An unreadable manifest fails the command naming the
  extension; a sidecar refuses — verify: tests.

## 3. Materialization and invocation

- [x] 3.1 The extension directory is materialized from the base tree
  blob by blob via `git show` — a link entry recreated, a gitlink
  refused — into the command's temporary directory — verify: tests.
- [x] 3.2 Each stage's working directory is a fresh `git archive`
  snapshot of the candidate commit; nothing reads the working tree;
  temporary directories are cleaned — verify: tests.
- [x] 3.3 The command runs as `[sys.executable, <command>]` — no shell,
  no `PATH` lookup — with the minimal-`PATH` + declared-variables +
  five `AGENTMARSHAL_*` environment — verify: tests.
- [x] 3.4 A missing or symlinked command is `not run` naming why; exit
  0 is `checked`, otherwise `failed (exit <n>)` — verify: tests.
- [x] 3.5 `min(timeout_seconds, 600)` bounds a stage and a breach kills
  the process group — `did not finish (timeout)` — verify: tests.

## 4. The grant gate

- [x] 4.1 `CI == "true"` needs no grant; otherwise `_read_grants` —
  malformed `trust.toml` fails the command — and `_hash_directory` over
  the materialized directory decide — verify: tests.
- [x] 4.2 No grant is `not run (not granted)`; a difference is
  `not run (changed after approval: <file>)` naming the first differing
  path — verify: tests.

## 5. Results, events and the exit status

- [x] 5.1 One result line per stage of the four outcome shapes, output
  framed as `<name> | <line>` escaped — verify: tests.
- [x] 5.2 One `extension-event` per stage — extension, `scope`
  `shared`, phase, decision, reason, commit, plus `result` for
  post-gate; a lost log is a warning — verify: tests.
- [x] 5.3 A non-checked `pre-gate-stop` stage prints the pause and
  exits 3; `pre-gate-warn` warns and exits 0; `post-gate` never pauses;
  the journal is untouched — verify: tests.

## 6. The change itself

- [x] 6.1 proposal.md, design.md, tasks.md and the extension-stages
  delta spec are written — verify: openspec validate.
- [x] 6.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 6.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-stages/spec.md` exists and the change lives
  under `openspec/changes/archive/`.
