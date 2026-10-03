## Context

ADR-0022 section 6 declares three `project.json` keys for the 0.5.0 record
model: `review.finding_classes` (ADR-0016 decision 3's vocabulary),
`review.changes_required_threshold` (decision 4, default 3) and
`contract.require_agreement` (ADR-0018 decision 2, default false). The file
is read by `read_project_file` and located by `project_file_path`; doctor
finds the project root with `find_project_root(start, stop_at=git_root)`,
which in a sidecar lands on the journal repository — the repository whose
`project.json` this is. No code reads the three keys today.

`project.json` is a hand-editable operator surface: the placement key is
already corrected by hand (`placement.py`'s comment calls it that), so a
mistyped value is a real case, not a hypothetical one.

## Goals

- One reader for all three keys, returning a typed result the later
  consumers (review launcher, `status`, the gate) call with one function.
- Absent means default; present means validated. A malformed value is named
  with what was expected, never silently replaced.
- `doctor` reports each malformed key as a failed check of its own.

## Non-Goals

- Any consumer of the settings — the launcher, `status`, the gate land in
  their own tasks.
- `init` writing the keys.
- Any other `project.json` key (`schema`, `placement`, `host`, `actors`
  keep their existing readers and rules).

## Decisions

- **One module, one call.** `settings.py` exposes
  `read_project_settings(project_root) -> ProjectSettings`, a frozen
  dataclass of the three values. It reads the file the way the project's
  other readers do — `project_file_path` + `read_project_file` — so a
  BOM-tolerant read and the sidecar location come for free. Doctor's
  per-key checks call the three single-key readers the module also
  exposes; each takes the project root the same discovery already found.
- **Absent and malformed are different states.** Absent — no section, or a
  section without the key — returns the default; the distinction is key
  membership (`key in mapping`), never a `None` value. A JSON `null` is
  present, not absent: a `null` section fails as a non-object and a `null`
  key fails the key's rule. Present and wrong raises
  `ProjectSettingsError`, a `ValueError`, whose message names the dotted
  key and what it expects. A malformed *section* (present, not an object)
  is a present malformed value too: the error names the key that could not
  be read. A malformed entry may be echoed in `repr` form — `repr`
  escapes control characters, so a string carrying one cannot forge
  output.
- **`other` may be listed, and is never required.** `other` is the
  fallback class: a finding outside the vocabulary is recorded as `other`
  (ADR-0016 decision 3), whether or not the project lists it. Listing it
  explicitly — so reviewers may assign it directly — is a reasonable
  configuration, and forbidding it would name a sensible value malformed.
- **The control-character rule is shared.** Class entries are checked with
  `reject_control_characters`, the same rule contract headers use, backed
  by the single `forges_rendered_text` predicate — a class name lands in
  review records and rendered output, where a newline would forge a line.
  The raised `JournalContractError` is re-raised as `ProjectSettingsError`
  so the module answers with one error type.
- **A boolean is not an integer.** `True` passes `isinstance(value, int)`,
  so the threshold refuses `bool` before testing `int`, and the flag tests
  `bool` exactly. The threshold also refuses non-integers and anything
  below 1.
- **Unknown keys inside the sections stay ignored.** Only the three named
  keys are read; anything else in `review` or `contract` is passed over,
  so a key a newer release adds does not break this one.
- **Doctor runs one check per key.** "Each malformed key as a failed
  check" reads literally: three `DoctorCheck`s, one per dotted key, after
  the existing `project schema` check. Each finds the root the way the
  other checks do, reads its one key, and fails with the error's message —
  which already names the key and what it expects. When the project file
  cannot be found or parsed the checks report that, like `project schema`
  does.

## Risks

- [Three more checks change doctor's output for every project] →
  intentional: the checks pass with the defaults shown, and the existing
  doctor tests that count checks are updated.
- [A consumer reading only one key would bypass validation of the others]
  → by design: each key's check must report independently of the others,
  and per-key readers are what make that possible.
