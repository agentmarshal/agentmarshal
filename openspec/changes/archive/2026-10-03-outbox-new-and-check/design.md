# Design

## Context

`init` scaffolds the outbox beside `project.json`
(`_scaffold_outbox` in `project.py`): `project_root/.agentmarshal/upstream/`.
In an embedded project that is the host repository's `.agentmarshal/`; in a
sidecar it is the journal repository's — `project.json` lives there. So the
outbox is found the same way in both placements: `find_project_root` gives
the project root, and the outbox is `upstream` under its `.agentmarshal/`.
No host lookup is involved; `new` and `check` never touch the host.

The five fields and their hints are CONTRIBUTING's "Reporting a finding":
Symptom, Measurements, Version, Environment, Expected. `agentmarshal
--version` prints the running tool's version; OS and Python version come
from the machine.

The leak scan the merge boundary runs is `scan_diff_for_leaks`
(`capture.py`) over the added lines of a diff. The drafts are not a diff:
every byte of a draft would be sent, so the scan here runs over each file's
whole content — reusing the scanner's signatures and the configured
markers, not writing another scanner.

## Goals / Non-Goals

**Goals:**

- One command from a gist to a conformable draft: the fields a reporter
  drops are the ones a command can fill.
- A check that names every gap and every hit before a batch, and refuses
  by exit status so a wrapper needs no parsing.

**Non-Goals:**

- `outbox send` and `outbox status` — ADR-0020 decisions 4–5, a later task.
- Scanning the repository or removed content: only the drafts' content.
- New signatures, new marker configuration, or a second scanner.
- Enforcing the file-name scheme on drafts an adopter wrote by hand.

## Decisions

- **A draft is Markdown with the five fields as `## ` headings.** A `## `
  heading matching a field name exactly marks that field's section; its
  body is everything up to the next `## ` heading or the end of the file.
  Deeper headings (`###`) are body, other level-2 headings are allowed,
  and a duplicate field heading is just another section of that field —
  the check then wants every occurrence filled. The scaffold's draft also
  carries a `# ` title line: the gist's first line.
- **File name: `NNNN-<slug>.md`.** `NNNN` is decimal, zero-padded to a
  minimum of four digits; the next number is one more than the largest
  number among `NNNN-*.md` files already in the outbox — 1 when there are
  none. Monotonic, so a gap a removed draft left is never refilled and
  name order stays creation order. The slug is the gist lowercased with
  every run of non-`[a-z0-9]` collapsed to `-`, trimmed of `-`, cut to 60
  characters and trimmed again; a gist that yields nothing — reports may
  be in any language, and a non-Latin alphabet slugs to empty — falls
  back to `draft`. An empty gist is refused: a draft needs a name.
- **Creation is exclusive.** The file is opened `O_EXCL`; on collision the
  number advances and creation retries, so `new` can never overwrite —
  not by race and not by a manually placed file.
- **Unfilled is empty or the scaffold's placeholder, unchanged.** The
  scaffold writes an HTML comment carrying the field's CONTRIBUTING hint —
  `<!-- what you observed, with the exact command and its output -->`
  under Symptom and so on — which instructs the reporter in the source and
  disappears when rendered. The check compares the stripped body: empty,
  or that field's placeholder verbatim, is unfilled. A reporter who adds
  content beside the comment has filled the field.
- **Version and Environment arrive filled.** Version is the running tool's
  `agentmarshal --version` output verbatim. Environment is
  `platform.platform()` plus the Python version — what the machine can
  say; the git provider CONTRIBUTING also lists is the reporter's to add.
- **Every regular file in the outbox is a draft, except `README.md`.** The
  outbox is one file per finding: whatever sits there is what would be
  sent, so a file that does not conform is named rather than reclassified
  out of the check. A file that is not UTF-8 text is named as such — it
  cannot carry the fields — and its bytes are still searched: decoded for
  the scan with U+FFFD for the undecodable spans, the same lossy-search
  rule the diff scan follows, so an ASCII signature in a binary file still
  matches.
- **The scan is content-level, per file, with the diff scan's
  vocabulary.** Each draft's text goes through `scan_for_leaks` for the
  built-in signatures; configured markers are matched by position exactly
  as `scan_diff_for_leaks` identifies them (`private-marker #N`). Hits are
  the shared `LeakHit`s — the draft's name passed through `safe_path` —
  rendered by `render_leak_hits` unbounded: this command's output is the
  list of places to look. The diff scan's "only added lines" rule does not
  carry over — its reason (do not re-flag what is already in the tree)
  does not hold for a file whose every byte leaves the repository.
- **Markers come from the working `project.json`.** The drafts are the
  adopter's own and there is no candidate tree to distrust, so the working
  configuration is the trusted source — read the way
  `markers_from_config` reads it, from `project.json` at the project root.
  In a sidecar that is the operator's own repository, the same side the
  standalone `leak-scan` trusts.
- **Every name the check prints goes through `safe_path`.** A draft's
  file name can itself carry a marker or match a signature, in a
  conformance line as much as in a hit — so names are masked everywhere,
  before the markers are even needed for content. An unreadable
  `project.json` is an error, not a scan with no markers.
- **The report goes to stdout, the refusal and errors to stderr.** Draft
  problems and hits are the report the operator reads; "no outbox",
  "cannot read project config" and the refusal summary are operational
  and go to stderr beside the best-effort caveat. Exit 0 only when every
  draft conforms and the scan found nothing — the refusal `send`'s
  wrapper relies on.
- **The group registers itself.** `outbox.py` owns a `register(subparsers)`
  for the `outbox` parser with its `new`/`check` subcommands and a
  `run(args, stderr)`; `cli.py` gains one line in `_build_parser` and one
  in dispatch. The subcommand name lives in `args.outbox_command`.

## Risks / Trade-offs

- [A signature or marker wording drifts from the diff scan's] → there is
  nothing to drift: `scan_for_leaks` owns the signature list and the
  marker position is formatted the same way `scan_diff_for_leaks`
  identifies it.
- [A marker that is itself a filename-safe word lands in a slug] → the
  slug keeps only `[a-z0-9-]`, so punctuation in a marker cannot survive;
  a marker that is pure filename characters in a gist the operator typed
  is echoed back at them, and `check` still masks every name it prints.
- [A whole-file scan flags a marker the adopter quoted deliberately] →
  inherent to content-level scanning; the hit names the file and the
  operator strips it before sending — that refusal point is what the
  check exists to give.
- [A draft that is a subdirectory or a symlink to one] → only regular
  files are drafts; anything else sits outside the one-file-per-finding
  convention and is not named either.
