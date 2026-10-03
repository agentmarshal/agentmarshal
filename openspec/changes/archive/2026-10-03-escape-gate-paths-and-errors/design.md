## Context

`escape_for_display` in `journal/display.py` renders every character
`forges_rendered_text` refuses as a visible escape — `\n`, `\r` and `\t`
by name, `\uXXXX` (`\UXXXXXXXX` past the Basic Multilingual Plane) for
the rest. CR-155 routed `status` and `report` through it; CR-161 routed
the gate's transcript, the brief and the reviewer prompt, escaping each
finished transcript line at `say` so a line added later cannot forget.

Two surfaces were left. A candidate's file names are not record text —
they are legal in git, no writer refuses them, and the gate reads its
path listings raw (`git diff --name-status -z`, `git status -z`,
`git ls-tree -z`) precisely so a quoted name cannot hide from a matcher.
When the gate names one — the scope line, the record-collision and
append-only lines, an extension's removal — the escaped line keeps it
safe, but nothing pinned that until now. And a `GateError`'s text is
printed by the CLI as it stands: messages like `git <arguments> failed:
<detail>` echo a caller-supplied ref or git's own error output raw, so a
ref carrying a newline prints a line the gate never said.

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
- **The transcript's escape point stays the finished line.** Every path
  the gate names already joins a line that `say` escapes — the scope
  line's outside paths, rename sources and targets, record paths in the
  collision and append-only lines, extension and manifest paths in the
  removal and named-extension lines. This change adds no second escape
  site; it pins the guarantee with tests so it cannot silently regress.
- **The leak-scan's own forms compose with the line escape.** A `WARN`
  line interpolates `render_leak_hits` or `render_undecodable_files`,
  whose names arrive already masked (`safe_path` replaces any secret a
  path carries) or in the scan's printable escapes (C-quoted header
  names, `\xNN` for undecodable bytes). Those forms are printable ASCII,
  so escaping the finished line leaves them untouched — the scan's rule,
  which decides *what* may print (never a secret), keeps its wording. The
  line escape then catches what masking does not cover: a path that is
  valid UTF-8 yet carries a refused character, which is no secret and
  passes `safe_path` unmolested, prints with each refused character
  escaped. Two different guarantees on the same line, each at its own
  layer.
- **The escape is not injective, as before.** A path carrying the two
  literal characters `\` and `n` prints like an escaped newline. That
  cannot forge a line or reorder text — the harms this rule guards — and
  escaping backslashes would change ordinary output, which the
  byte-identical requirement forbids.
- **Tests create the hostile names for real.** A newline and a
  right-to-left override are legal in a Linux file name, so the tests
  commit files carrying them rather than mocking the listing; where a
  filesystem refuses such names the test skips with a reason, since what
  it demonstrates is the gate's output, not the platform's rules.
