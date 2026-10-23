## Context

`doctor` is two surfaces: named checks whose results print on stdout and
decide the verdict and the exit status (`_run_doctor` formats them as
`OK` / `FAIL` / `TODO`), and a report on stderr which can never make the
command fail. CR-213 put the extension manifests on the check side —
`extension manifest <name>` per discovered name — and the per-extension
listing on the report side.

Manifests already expose a parsed `wraps` — `journal/extensions.py`
validates `[wraps].runtime` as `<name> >= <version>` and exposes the
string whole — and `[wraps]` can only ever come from the directory form,
because a `lock` under `lock/` is mandatory and the single-file form has
no directory for it to name. `doctor`'s git check already shows the
shape this check needs: `shutil.which` for the lookup, `subprocess.run`
with an argv list for `--version`, a regex reading the first dotted
number out of the answer.

## Goals

- A developer sees, before any stage runs, whether the runtime a wrapper
  needs is present and new enough — the `doctor` half of ADR-0013
  decision 13's amended sentence, the stage runner being CR-211's line.
- A runtime problem fails the way `doctor` fails things — one named
  check per extension, the failure counting in the verdict and the exit
  status — because a missing or too-old runtime is a defect of the
  machine for this project, not a fact to note.
- Nothing guesses: a version the output does not name is reported
  unreadable, and a project with no wrapper is byte-for-byte `doctor`
  of today.

## Non-Goals

- Dependencies against their locks (decision 12's `doctor` check of the
  installed tree against `lock/`) — a later task.
- The stage runner using the runtime — that arrives with the wrapper
  extension itself, CR-211's line of work.
- Installing a runtime, or anything else: `doctor` runs `PATH` lookups
  and `--version` calls; it changes nothing on the machine.
- Protection beyond what the published decisions promise — docs/threat-
  model.md bounds `doctor` to "checks the preconditions it can reach".

## Decisions

- **One `extension runtime <name>` check per extension whose manifest
  parses and declares `[wraps]`.** The check lives beside the manifest
  check, under the same discovery (`_extension_names` over
  `.agentmarshal/extensions/`), and is built only when the manifest read
  at build time yields a `wraps`: an extension without `[wraps]` gets no
  runtime line, an unreadable manifest gets none either — the manifest's
  own check already says why — and a project without wrappers adds
  nothing at all, keeping today's checks, today's verdict.
- **The lookup is `shutil.which`; the invocation is argv, never a
  shell.** The declared `<name>` is resolved through the same injected
  resolver the git check uses, so a test puts a fake runtime on a
  temporary `PATH` and nothing depends on the machine — and a `<name>`
  carrying a directory component (`.`/`..`, `/`, `\`) fails the check
  first, because `which` skips the `PATH` search for such an argument
  and probes the path directly: the one exception is a bare program
  name. The resolved path runs `subprocess.run([path, "--version"],
  capture_output=True, encoding="utf-8", timeout=10)` — an absolute
  argv, `shell=True` impossible by construction, a short limit so a
  hung runtime is the check's failure rather than `doctor`'s.
- **The version is the first run of numeric dot-separated components in
  the answer, a leading `v` ignored** — `v20.11.0` reads as `20.11.0`,
  the way `_git_version` reads `git version 2.39.2.windows.1` as
  `2.39.2`; stdout is consulted first, then stderr. Comparison is
  numeric component by component with a missing trailing component
  reading as zero — `9.11.0` is below `20`, `20` meets `20.0` — and a
  declared minimum or a reported answer naming no number is reported
  unreadable, never guessed.
- **Every value a result names is escaped at construction.** The found
  path is machine text (a `PATH` element can carry a newline), the
  requirement is manifest text, and `_run_doctor` prints details raw —
  so the check escapes them into the detail the way the manifest check
  escapes the reader's error, and the extension's name into the check's
  name.
- **The result detail names the path, the version and the requirement.**
  `OK` reads `<path> reports <version>, meeting 'name >= minimum'`;
  each failure says which of the four it is — not found, not runnable or
  non-zero, silent past the limit, unreadable or below — naming what it
  learned and nothing it did not.

## Risks

- [A runtime's `--version` answers something unversioned or hostile]
  → the output is never echoed: only the parsed numeric components are
  displayed, escaped anyway, and an answer naming none fails as
  unreadable.
- [A slow or hung runtime stalls `doctor`] → the ten-second limit makes
  it a failed check with a named reason.
- [The manifest is read once at check-build to decide the runtime check
  exists and again inside the manifest check at run] → accepted: the two
  reads are adjacent in one process, and disagreement degrades to a
  stale detail, never a wrong verdict (CR-213 accepted the same).
