## Context

`escape_for_display` in `journal/display.py` renders every character
`forges_rendered_text` refuses as a visible escape — `\n`, `\r` and `\t`
by name, `\uXXXX` (`\UXXXXXXXX` past the Basic Multilingual Plane) for
the rest. CR-155 routed `status` and `report` through it; CR-161 routed
the gate's transcript, the brief and the reviewer prompt, escaping each
finished transcript line at `say` so a line added later cannot forget.

Two surfaces were left. A candidate's file names are not record text —
they are legal in git and no writer refuses them. The listings the gate
matches a name against mostly read raw (`git diff --name-status -z`,
`git status -z`, the candidate tree's `git ls-tree -z`), but two did
not — the base tree's `git ls-tree -r --name-only` and the journal
history's `git log --name-only` — and a name git C-quotes never equals
the raw name the diff returns, so a record-path collision or a
committed tamper could hide from a matcher. When the gate names a path —
the scope line, the record-collision and append-only lines, an
extension's removal — the escaped line keeps it safe, but nothing
pinned that until now. And a `GateError`'s text is printed by the CLI
as it stands: messages like `git <arguments> failed: <detail>` echo a
caller-supplied ref or git's own error output raw, so a ref carrying a
newline prints a line the gate never said. The placement refusal has
the same shape: a `PlacementError` carries the sidecar host path from
`project.json` — configuration the candidate's tree supplies — or git's
own error text into a message the CLI prints as it stands.

## Goals

- Nothing a candidate controls — its paths, a rename's source or target,
  a ref, a value inside an exception's text, git's own error output —
  can add a line to the gate's output or reorder what is read.
- Every error or refusal message the gate produces escapes the values it
  carries, at a point a later raise cannot forget.
- A candidate whose paths and values carry no refused character produces
  byte-identical output: the pinned fixtures stay untouched.

## Non-Goals

- Refusing such file names. They are legal in git; naming them escaped
  is enough — a refusal would be a new rule, not a display fix.
- Output of commands other than the gate.
- The leak scan's own naming forms: a masked path (`safe_path`'s
  `<private marker #n>` / signature descriptions), git's C-quoted form in
  diff headers, and the `backslashreplace` `\xNN` form for a path whose
  bytes are not UTF-8 all stay as they are — see Decisions.

## Decisions

- **`GateError` escapes its message at construction.** A `GateError` is
  refusal text: the CLI prints it, `complete` re-quotes it inside a
  `LifecycleError`, the review launcher re-quotes it inside a
  `ReviewLaunchError`. Escaping where the message is born — rather than
  at each interpolation or each print — is the same choice the transcript
  made at `say`: a raise added later cannot forget the escape, callers
  outside this file (the gate context's own `GateError`s included) need
  no change, and a wrapper that embeds the text carries the escaped form.
  The tool's fixed text holds no refused character, so escaping the
  finished message changes only what a value put there.
- **Every listing the gate matches a name against reads NUL-separated
  and decodes `surrogateescape`.** The candidate diff
  (`git diff --name-status -z`), the sidecar's working-tree status
  (`git status -z`) and the candidate tree (`git ls-tree -z`) already
  read `-z`; the base tree's `git ls-tree -r --name-only` and the
  sidecar history's `git log --name-only` did not, so a name git
  C-quotes could hide from a matcher — a record-path collision or a
  committed tamper the check never saw. Both now read `-z`, which is
  what makes every matcher see a name by the path itself. But `-z`
  output is raw bytes, and git permits name bytes that are not UTF-8:
  strict-decoding those listings moved a refusal — the base tree read
  C-quoted ASCII before, so one undecodable name anywhere in it now
  refused every run. Every `-z` listing therefore decodes through
  `_run_git_lossy` with `surrogateescape`: the name keeps its bytes for
  matching (a low surrogate round-trips through `os` and back to git),
  the run is never refused on a name's account, and where the gate
  names it the surrogate is a character the forgeable-text rule
  refuses, so `say` and `GateError` print it as its `\udcXX` escape.
  What stays strict is deliberate: `git show` of a record, manifest or
  contract, `rev-parse`, `merge-base` and the email listing still
  refuse non-UTF-8 output as `GateError`, because undecodable content —
  unlike an undecodable name — is a thing read, not a thing compared.
- **The leak-scan's own naming forms compose with this.** A `WARN` line
  interpolates `render_leak_hits` or `render_undecodable_files`, whose
  names arrive already masked (`safe_path` replaces any secret a path
  carries) or in the scan's own escaped form — the `backslashreplace`
  `\xNN` the leak-scan spec pins for a path whose bytes are not UTF-8.
  That form stays: the WARN line's `\xNN` is printable ASCII, so `say`'s
  escape leaves it untouched, while the surrogate form a `-z` name
  carries prints `\udcXX` wherever a transcript line names the same
  file. Two forms for the same byte, each fixed by its own layer — the
  scan's rule decides *what* may print (never a secret), the line
  escape decides that nothing forges a line — and a path that is valid
  UTF-8 yet carries a refused character, which is no secret and passes
  `safe_path` unmolested, prints with each refused character escaped.
- **The placement refusal is escaped where the CLI prints it, not at
  `PlacementError` construction.** The gate — like every `cli.py`
  command but `leak-scan`, which calls `resolve_placement` directly and
  prints its own refusal — resolves placement through `_placement`,
  and the helper prints the error as it stands; escaping at that print
  point keeps the display rule in the layer that prints —
  `placement.py` resolves roots and knows nothing of transcripts.
  `leak-scan`'s and `step`'s own `PlacementError` prints are outside
  this change: output of commands other than the gate is a non-goal.
  The parallel with `GateError` is the difference, not a
  contradiction: a `GateError` escapes at birth because callers
  re-quote its text into other exceptions (`LifecycleError`,
  `ReviewLaunchError`), while a `PlacementError`'s text is only ever
  printed. Escaping the finished message — as `say` does a line —
  changes only what a value put there.
- **Every exception type the gate's CLI prints carries escaped text.**
  Enumerated, not assumed:
  - `GateError` — from `run_gate`, `run_findings_gate` and
    `derive_gate_context` — escapes its message at construction; every
    raise site hands it one string, and re-wrapping sites
    (`GateError(str(error))`, `GateError(f"... {error}")`) pass the
    text back through the same escape.
  - `PlacementError` — from `resolve_placement` inside `_placement` —
    is escaped at the helper's print point; its text can carry the
    host path from `project.json`, a project file path, an `OSError` or
    `ValueError`'s text and `GitNotAvailableError`'s.
  - `report.lines` are not exceptions but carry the same values —
    `ExtensionManifestError`'s and `ExtensionManifestMissing`'s text
    inside the named-extension lines, `CaptureError`'s and
    `ValueError`'s inside the leak-scan `WARN`, `JournalRecordError`'s
    inside the invalid-records line — and every line goes through
    `say`'s escape.
  - `LifecycleError` and `ReviewLaunchError` are printed by `complete`
    and `review`, not `gate`, but both re-quote `str(GateError)`, which
    arrived escaped.
  - `placement.evidence_line` and `placement.advisory_notice` are fixed
    text — no value to escape.
  Nothing else is printed: `_run_gate` catches only `GateError` and a
  `PlacementError` never reaches it — anything else that could escape
  `run_gate` (a `JournalRecordError` from a second `read_records` on a
  journal that mutated mid-run, say) is a defect and a traceback, not
  gate output to be escaped.
- **The transcript's escape point stays the finished line.** Every path
  the gate names already joins a line that `say` escapes — the scope
  line's outside paths, rename sources and targets, record paths in the
  collision and append-only lines, extension and manifest paths in the
  removal and named-extension lines. This change adds no second escape
  site; it pins the guarantee with tests so it cannot silently regress.
- **The escape is not injective, as before.** A path carrying the two
  literal characters `\` and `n` prints like an escaped newline. That
  cannot forge a line or reorder text — the harms this rule guards — and
  escaping backslashes would change ordinary output, which the
  byte-identical requirement forbids.
- **Tests create the hostile names for real.** A newline, a
  right-to-left override and a raw non-UTF-8 byte are legal in a Linux
  file name, so the tests commit files carrying them rather than mocking
  the listing; where a filesystem refuses such names the test skips with
  a reason, since what it demonstrates is the gate's output, not the
  platform's rules.
