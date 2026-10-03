## 1. The reader

- [x] 1.1 `src/agentmarshal/settings.py`: `ProjectSettings` dataclass,
  `read_project_settings(project_root)`, the per-key readers, the
  defaults (seven classes, 3, false) and `ProjectSettingsError` — verify:
  settings tests for the defaults and for absent-key fallback.
- [x] 1.2 Validation: vocabulary a non-empty list of distinct non-empty
  strings without control characters (`reject_control_characters`),
  threshold an integer ≥ 1 with booleans refused, flag a boolean, a
  non-object section named — every error names the dotted key and what it
  expects — verify: settings tests per malformed kind.
- [x] 1.3 `other` is accepted in the vocabulary — verify: the scenario's
  test.

## 2. doctor reports each malformed key

- [x] 2.1 One `DoctorCheck` per key after `project schema`, failing with
  the message that names key and expectation — verify: doctor tests for
  one malformed key and for several.
- [x] 2.2 The checks read the journal repository's `project.json` through
  the existing root discovery — verify: a doctor test in a sidecar
  journal repository.
- [x] 2.3 A project with none of the keys passes; existing doctor tests
  updated for the new check count — verify: pytest.

## 3. The spec holds

- [x] 3.1 Every scenario in the delta spec is demonstrated by a test whose
  docstring names it — verify: cross-check scenario titles against test
  docstrings; `openspec validate`.
