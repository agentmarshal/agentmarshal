## Context

`doctor` is two surfaces: named checks whose results print on stdout and
decide the verdict and the exit status (`_run_doctor` formats them as
`OK` / `FAIL` / `TODO`), and a report on stderr — the journal, process
log and local-state paths through `print_paths`, then every overdue step
— which can never make the command fail. Malformed project settings sit
on the check side: each malformed key fails a `project setting <key>`
check of its own.

Manifests are already read everywhere through one reader —
`read_extension_manifest` in `journal/extensions.py` — which knows both
forms of ADR-0013 decision 9, refuses a name in both forms, refuses
links lexically before existence is decided, and returns a parsed
manifest that exposes its schema, stages, declared `ext` kinds and, for
the directory form, the directory it was read from. Grant state is
already computed by `extension list` in `extension_trust.py`: the grants
recorded in the clone's `trust.toml`, a fresh per-file hash of the
extension's directory, and `_changed_after_approval` naming the first
differing file. This change wires those two pieces into `doctor`;
neither learns anything new.

## Goals

- A developer sees, in one `doctor` run, which shared extensions the
  project carries and whether this clone has approved each directory
  form — what ADR-0013 decision 14's "before each run" question looks
  like before the stage runner exists.
- An extension manifest that cannot be read fails the way a malformed
  project setting fails — loudly, per name, without stopping the rest —
  because a manifest that will not parse is the thing the developer most
  needs to see.
- Everything that is a fact about the machine rather than a defect —
  no grant yet, a grant overtaken by an edit — stays information on the
  report side and never moves the verdict.

## Non-Goals

- Dependencies against their locks, the runtime a wrapped product needs,
  and the environment (ADR-0013 decisions 12 and 13, section F) — a
  later, larger task.
- Personal and user-scope extensions (decision 9's other scopes) — a
  later task.
- Switches (section E) and whether a stage would run — the stage runner
  is CR-211's line of work.
- Running anything. `doctor` lists and hashes; it executes nothing an
  extension declares.

## Decisions

- **The section prints on stderr, beside the paths report.** The check
  report on stdout keeps its shape — `STATUS: name — detail` lines and
  the summary are what a parser reads — so the listing joins the report
  side, after the three path lines and before the overdue steps: paths,
  then what is installed, then what is late. With no project resolvable
  the section marks itself `unavailable` with the same reason the three
  paths carry, matching their degradation.
- **One check per extension manifest.** `doctor_checks` discovers the
  names under `.agentmarshal/extensions/` — a `<name>.toml` entry is
  the file form, a `<name>/` entry the directory form, a link under
  either spelling is found under the name it carries so the reader's
  own refusal reports it, and a name in both forms lists once — and adds
  a `extension manifest <name>` check per name whose run reads the
  manifest through `read_extension_manifest`. A read error fails that
  check alone, the `project setting <key>` pattern carried to
  manifests; a parsed manifest passes, its detail naming the form and
  the schema. Discovery that cannot run — `.agentmarshal` or
  `extensions/` a link, the directory unlistable — adds a single
  `extension manifests` check failing with the reason, and the section
  marks the listing unavailable. Where discovery finds nothing the
  checks add nothing: a project without the directory keeps today's
  output.
- **The section re-does discovery, not the checks' parsing.** The
  report lists the entries itself — the section is a view of the
  directory, not of the check results — so a manifest broken between
  the two reads (they share one run, but the report owes no check its
  answer) still renders on its own line. Each line names the extension,
  the form, the manifest's schema, the stages as their modes (phases)
  and the declared `ext` kinds — `none` where the manifest declares
  none — and, for a directory form, this clone's grant state. An
  unreadable manifest's line names the extension and the reason in one
  line; a real `<name>/` directory still shows its grant state on that
  line, since the grant covers the directory's contents, not the
  manifest's health.
- **The grant state is the `extension list` computation, called not
  redone.** `_read_grants` reads `trust.toml` once for the section;
  `_hash_directory` and `_changed_after_approval` give each real
  directory its `granted`, `not granted` or `changed after approval:
  <file> (<kind>)` — the same words `extension list` prints, including
  its "named rather than hashed through" treatment of links and its
  error in place of a state when the directory cannot be hashed. When
  the local state did not resolve or the grants file cannot be read,
  the grant position says `unavailable` with the reason — a report,
  never a failure, exactly as the paths lines degrade.
- **Escaping is the report's own.** Every section line goes through
  `escape_for_display` whole, as the paths and overdue-step lines do;
  the check side escapes the extension's name into the check's name and
  the reader's error into the detail, since the check report prints
  them raw (ADR-0015 decision 5's rule — a value the reader refused can
  still carry a refused character, and a file name on disk can carry
  one the name rule never saw).

## Risks

- [A manifest read twice — once for its check, once for its line —
  could disagree mid-run] → accepted: the two reads are adjacent in one
  process, and disagreement degrades to a stale detail, never a wrong
  verdict.
- [Hashing a large directory on every `doctor` run] → the hash is the
  decision's own mechanism (ADR-0013 decision 14's "recomputes the
  directory hash" before each run), bounded by the extension's own
  directory.
- [A name carrying a forgeable character reaches stdout through the
  check's name] → the check name and detail are escaped at construction,
  the same escaping the section applies whole.
