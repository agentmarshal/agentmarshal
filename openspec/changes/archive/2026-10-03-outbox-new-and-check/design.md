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
- **Every name `new` could have written counts toward the number, and a
  hand-written date does not.** A name counts when it is exactly
  `NNNN-<slug>.md` — `NNNN` as `new` emits it (zero-padded to four digits
  below 1000, unpadded at and above) and the slug `[a-z0-9]+(-[a-z0-9]+)*`
  — whatever the slug's leading groups: `new` itself emits `-NN-NN-`
  there (the gist `12 34 widget` slugs to `12-34-widget`), so a digit-led
  slug must not hide a draft. The exception is the date shape a hand
  writes: an unpadded four-digit number followed by a valid `-MM-DD`
  reads as a date prefix — `2026-10-03-note.md` is not number 2026 —
  while `new`'s zero padding means `0001-10-03-note.md` can only be a
  draft's number 1. A scaffolded draft can still land on the date shape
  itself — an unpadded number 1000–9999 under a slug that opens `MM-DD-`
  is indistinguishable from a hand-written date; exclusive creation still
  yields a free number, so the counter being blind to it costs nothing.
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
- **Every regular file in the outbox is a draft, except `README.md`; every
  other entry is named as not checked.** The outbox is one file per
  finding: whatever sits there is what would be sent, so a file that does
  not conform is named rather than reclassified out of the check, and an
  entry that is not a regular file at all — a directory, a symlink, a
  FIFO, anything `lstat` does not report as regular — is named as not a
  draft and not checked and fails the run: a later `send` would stage it
  unchecked, and nothing in the outbox passes in silence. A file that is
  not UTF-8 text is named as such — it cannot carry the fields — and its
  bytes are still searched: decoded for the scan with U+FFFD for the
  undecodable spans, the same lossy-search rule the diff scan follows, so
  an ASCII signature in a binary file still matches. The `README.md`
  `init` writes is the one regular file that is not a draft — its fields
  are never checked — but it leaves with the batch like everything else,
  so its name and its content go through the same scan.
- **The scan is content-level, per file, with the diff scan's
  vocabulary.** Each draft's text goes through `scan_for_leaks` for the
  built-in signatures; configured markers are matched by position exactly
  as `scan_diff_for_leaks` identifies them (`private-marker #N`). Hits are
  the shared `LeakHit`s — the draft's name passed through `safe_path` —
  rendered by `render_leak_hits` unbounded: this command's output is the
  list of places to look. The diff scan's "only added lines" rule does not
  carry over — its reason (do not re-flag what is already in the tree)
  does not hold for a file whose every byte leaves the repository.
- **The file name is scanned too.** What leaves with the batch is the
  file, name included, so a name that contains a configured marker or
  matches a signature is a hit by itself — same vocabulary, the masked
  name beside the marker's position or the signature's identifier — even
  when the content is clean. This holds for every entry, draft or not.
- **Markers come from the working `project.json`.** The drafts are the
  adopter's own and there is no candidate tree to distrust, so the working
  configuration is the trusted source — read by `markers_from_config`
  itself, the same helper the standalone `leak-scan` command calls for the
  sidecar's own repository. In a sidecar that is the operator's own
  repository, the same side `leak-scan` trusts.
- **Every name and path the check prints goes through `safe_path`, and no
  exception's text is printed.** A draft's file name can itself carry a
  marker or match a signature, in a conformance line as much as in a hit —
  so names are masked everywhere, before the markers are even needed for
  content. An unreadable `project.json` is an error, not a scan with no
  markers. `str(OSError)` carries the path it failed on, so an OS error is
  described by its errno text (`strerror`, the errno name when there is
  none) and the path, where one is printed at all, only through
  `safe_path`; the `GateError` wrapping a failed config read is described
  the same way, since its text embeds the same path. A `leak_scan` section
  that is present but malformed fails the read with `CaptureError`, whose
  text echoes the configured keys it rejects, so `check` answers with a
  fixed diagnosis — the leak-scan configuration is malformed; run
  `agentmarshal doctor` — and quotes none of it. `new` prints the real
  path it wrote — the scenario's contract and the operator's own terminal
  — but its errors follow the same no-exception-text rule.
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
  is echoed back at them, and `check` reports it as a hit in the masked
  name — the name leaves with the batch, so it cannot pass silently.
- [A whole-file scan flags a marker the adopter quoted deliberately] →
  inherent to content-level scanning; the hit names the file and the
  operator strips it before sending — that refusal point is what the
  check exists to give.
- [A name-hit can only be resolved by renaming] → the file is named the
  way the scan describes names, and renaming is the fix a name that is
  itself the leak needs — the check cannot offer to keep it.
- [An entry that is a directory, a symlink or a FIFO sits in the outbox] →
  it is named as not a draft and not checked and fails the run; a later
  `send` stages whatever the outbox holds, so an unchecked entry cannot
  be waved through.
