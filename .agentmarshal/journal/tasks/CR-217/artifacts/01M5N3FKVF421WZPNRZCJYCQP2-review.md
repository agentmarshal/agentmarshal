No blocking or advisory findings.

Acceptance criterion 1 is met: the archived proposal, design, ADDED delta spec, tasks, and synchronized main spec are present; all 20 scenarios have matching `Scenario:` docstrings in `tests/test_switches.py`, and the coordinator reports `agentmarshal validate` passed.

Acceptance criterion 2 is met by the single `parse_switches` function and parser tests including `test_an_off_switch_parses_with_its_task_and_reason`, `test_an_unknown_or_missing_format_is_refused_naming_the_file`, and `test_a_switch_entry_outside_its_shape_is_refused_naming_the_file_and_the_entry`.

Acceptance criterion 3 is met by the stage tests covering base-only reads, non-execution, no pause, multiple result lines, malformed-file blocking, and events—particularly `test_the_switches_are_read_from_the_base_commit_never_the_candidate_or_the_working_tree` and `test_a_malformed_switches_file_is_reported_on_one_line_and_no_stage_of_an_extension_it_names_runs`.

Acceptance criterion 4 is met by the doctor tests, including `test_doctor_shows_a_switched_off_extension_with_its_task_and_reason`, `test_a_project_without_switches_toml_shows_nothing_new`, and the file-form and malformed-file cases.

Acceptance criterion 5 is met: `test_a_value_that_could_forge_a_line_is_escaped_on_display` covers display escaping; the supplied diff changes no gate or unrelated command; and the coordinator reports the complete CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"179b3593cd76ddba4d4a9dc8a379a82f5b8b248a","verdict":"approved","findings":[],"verification":{"executed":[{"what":"Compared archived delta-spec Scenario headings with Scenario docstrings using rg","result":"All 20 scenario headings have matching test docstrings."}],"read":["Task contract CR-217 supplied in the review request","docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md","docs/adr/ADR-0014-where-things-live.md","docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md","docs/threat-model.md","src/agentmarshal/switches.py","src/agentmarshal/stages.py","src/agentmarshal/doctor.py","tests/test_switches.py","openspec/changes/archive/2026-10-24-shared-extension-switches/","openspec/specs/extension-stages/spec.md"],"not_run":[{"what":"Independent full CI sequence","why":"The snapshot lacks uv; the coordinator reports the full sequence passed on the reviewed commit."},{"what":"Independent Git commit/diff verification","why":"The supplied snapshot contains no discoverable .git metadata; the reviewed SHA is taken from the task statement."}]}}
AGENTMARSHAL_VERDICT_END
