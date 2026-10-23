## Context

ADR-0013 section A fixes the shape of the problem: decisions 1 and 2
declare the stages an extension may carry — `pre-gate-warn`,
`pre-gate-stop`, `post-gate`; decisions 4 and 5 make the extension a
separate step before the gate whose output the gate never reads;
decision 6 places the manifests and the code of shared extensions at
the base commit; decision 7 gives every extension a result line and its
output a frame. Section D's decision 14 makes the workstation run
conditional on a local grant over the extension directory's hash — the
grants `extension_trust.py` keeps in `trust.toml` — and decision 15
bounds the trust as local state, no defence against a same-user
process. ADR-0014's map puts the grants file and the process log in
the clone's local state; ADR-0022 section 7 names `extension-event`
the event kind a stage result leaves. The pieces already exist:
`journal/extensions.py` parses and validates the manifest including
its `[[stage]]` entries; `journal/gate.py`'s `_manifest_from_tree`
reads a manifest from a base tree with the link and form refusals the
filesystem reader applies; `journal/review.py`'s `_extract_snapshot`
materializes a commit as a clean directory via `git archive`;
`extension_trust.py` holds `_hash_directory`, `_read_grants` and
`_changed_after_approval`; `process_log.py` writes the events; and
`steps.py` shows the command-group shape `cli.py` registers.

## Goals

- `stage run` invokes each shared extension's declared stages at the
  two lifecycle points — the modes a `--phase` value selects — with
  everything trusted taken from the base commit and everything the
  stage sees a snapshot of the candidate.
- Each stage runs as an argv process under the core's interpreter,
  bounded in time, its result a single line and a single event.
- The workstation gate is the grant check the ADR wrote: recompute the
  hash over the materialized directory and run only on a match.
- Fail visibly everywhere: a manifest that cannot be read fails the
  command, a stage that cannot run gets `not run` with the reason, a
  `pre-gate-stop` stage that did not check pauses the process.

## Non-Goals

- Network isolation and write isolation: the manifest's
  `isolation.network`/`writes` declarations are read and unused here;
  the ADR stages them for later work and this change does not pretend
  them.
- Pause records: pausing is an exit status and a message, not a journal
  artifact — nothing is written to the journal at all.
- Personal and user-scope extensions, `doctor` reporting, and the
  gate's own extension handling.
- ADR-0013 decision 8 beyond the floor this change does keep: the
  declared `timeout_seconds` capped by the core's limit is implemented;
  the rest of the isolation contract is deferred with it.

## Decisions

- **The group is `stage`, the module `stages`, the one subcommand
  `run`.** `register` adds `stage` with `run` under
  `dest="stage_command"`, taking `--phase`, `--task`, `--commit` and
  `--base`, all required; `run` dispatches — the shape `steps.py` and
  `extension_trust.py` established, so `cli.py` grows one register call
  and one dispatch line.
- **"The base" is the merge base of `--base` and `--commit`, resolved
  as the gate resolves.** Both arguments are resolved to full SHAs with
  the gate's `_resolve_commit`, then `git merge-base` gives the tree
  every trusted input is read from — the same "base side of the history
  the candidate belongs to" the gate uses, so a stage's manifest and an
  extension's code are exactly what the gate's own extension handling
  would have read.
- **Manifests come from the gate's base-tree reader; enumeration is the
  tree counterpart of the filesystem rule.** `ls-tree` of
  `.agentmarshal/extensions/` at the merge base gives the names: a
  `tree` entry is a directory-form extension, a `<name>.toml` blob is
  the file form (no directory, no stage), a link entry at
  `.agentmarshal`, at `extensions/` or at a `<name>` is refused as a
  link — the same order the gate's reader applies: refusal before
  absence. Each name's manifest then comes from `_manifest_from_tree`,
  whose both-forms, link and schema refusals apply unchanged; one
  extension's unreadable manifest fails the command naming it, rather
  than silently dropping its stages.
- **The extension's directory is materialized blob by blob with `git
  show`, not `git archive`.** `git archive` honours `export-ignore` and
  `export-subst`, and the grant check must hash the tree's own bytes —
  so each entry under `.agentmarshal/extensions/<name>/` at the base is
  listed with `ls-tree -r` and written to a fresh temporary directory
  with `git show`: a blob byte for byte, a symbolic-link entry
  recreated as a link (the grant hash refuses it as the filesystem
  walk would, and a linked `command` is refused at invocation), a
  gitlink refused as not materializable. The directory lands under the
  command's `TemporaryDirectory`, removed with everything else.
- **The working directory is a fresh snapshot of the candidate
  commit.** `journal/review.py`'s `_extract_snapshot` — `git archive`
  into a tar extracted with the `data` filter — is reused; its
  `ReviewLaunchError` is caught and turned into the stage's `not run`
  reason. A fresh snapshot per stage: no stage inherits what another
  wrote.
- **The invocation is `[sys.executable, <command>]` with no shell and
  no `PATH` lookup.** The manifest already guarantees `command` is a
  relative path under `bin/` carrying no whitespace or metacharacter;
  the runner adds the checks the materialized directory owes — the
  path exists, is a file and is not a link — and hands the argv list to
  `Popen` with `start_new_session`, so a timeout can kill the group.
  Running under `sys.executable` rather than the file's own shebang
  keeps the interpreter the core's regardless of what the file asks
  for, and needs no execute bit.
- **The environment is minimal `PATH`, the declared names, then the
  protocol.** `PATH` starts as `os.defpath`; each `isolation.env` name
  the caller holds is copied — a manifest naming `PATH` receives the
  caller's, which is what the declaration exists to pass; then the five
  protocol variables are written: `AGENTMARSHAL_PHASE` (the `--phase`
  value), `AGENTMARSHAL_TASK`, `AGENTMARSHAL_COMMIT` (the resolved
  candidate), `AGENTMARSHAL_BASE` (the merge base everything was
  materialized from) and `AGENTMARSHAL_SNAPSHOT` (the working
  directory). Written last, a declared name colliding with one cannot
  override the run's own values.
- **The limit is `min(timeout_seconds, 600)`.** The manifest declares
  `timeout_seconds`; the core's limit is a module-level constant of 600
  seconds — the cap the contract fixes — and on expiry the process
  group is killed (`killpg` with `SIGKILL`, `Popen.kill` where a group
  does not exist), the captured output printed, and the result is
  `did not finish (timeout)`. A manifest declaring no isolation gets
  the core's limit.
- **The grant check compares per file over the materialized
  directory.** `CI` equal to `true` skips the check entirely — CI needs
  no grant (ADR-0013 decision 14's own split). Else `_read_grants`
  reads `trust.toml` — a malformed file fails the command — and
  `_hash_directory` computes over the base-materialized contents: a
  link or a non-regular file inside is the `not run` reason, verbatim
  from `extension_trust`. No grant is `not granted`; a difference is
  `changed after approval: <file> (<kind>)` naming the first differing
  path, the same refusal `extension list` reports.
- **One result line and one event per stage, output framed.**
  `<name>: checked` / `failed (exit <n>)` / `did not finish (timeout)`
  / `not run (<reason>)` on stdout; captured output reprinted line by
  line as `<name> | <line>` with `escape_for_display` applied, so a
  line the extension printed cannot read as a result or as another
  extension's. The `extension-event` carries `extension`, `scope`
  `shared`, the stage's own `phase`, `decision`, `reason` and
  `commit`, plus `result` for a `post-gate` stage. A log that cannot
  be opened or written is a stderr warning — the result line and the
  exit status are the verdict and never change for it.
- **A `pre-gate-stop` stage that did not check pauses; nothing else
  does.** `decision != "checked"` on a `pre-gate-stop` stage prints
  `the process is paused before the gate` naming the stage and the
  command exits 3; on a `pre-gate-warn` stage it prints a `WARNING`
  line and the exit stays 0; `post-gate` is a notification whatever it
  did.
- **A sidecar runs no stages.** The base a stage's code is taken from
  is a property of the embedded placement; `resolve_placement`
  reporting a sidecar refuses before anything is resolved.

## Risks

- [A stage writes into its own snapshot and a later stage sees it] → a
  fresh snapshot per stage removes the channel.
- [A stage's environment misses something an operator's shell had] →
  `isolation.env` is the declared channel; an undeclared variable not
  passing is the point of the minimal environment, and the reason is in
  the manifest the adopters approved.
- [A child of the stage outlives the timeout kill] → the group is
  killed, not just the direct child; a stray daemonized process is the
  same bound every local runner has.
- [`git show` materializing a large directory] → bounded by the
  repository's own objects; the temporary directory is always cleaned.
- [A same-user process racing the grant check] → ADR-0013 decision 15
  bounds this out of the model: `trust.toml` is local state, and the
  check recomputes at run time, which is all the ADR asks.
- [A symlinked `command` recreated faithfully] → refused at invocation
  with `is a symbolic link`, and on a workstation the grant hash refuses
  the directory first — both named, neither followed.
