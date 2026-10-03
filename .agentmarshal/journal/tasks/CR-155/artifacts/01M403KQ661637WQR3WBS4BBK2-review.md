I reviewed the diff statically. `uv`, `pytest`, `ruff` and `mypy` are not installed in this snapshot and Python execution is blocked here, so I could not run the CI sequence myself — the findings below come from reading the code, the spec and the tests.

What I verified:

- `escape_for_display` (`src/agentmarshal/journal/display.py:27`) asks `forges_rendered_text` per character, so the escaped set is exactly the refused set by construction; the early full-value check is only a fast path. Surrogates (`Cs`) escape as `\udXXX`, `\n`/`\r`/`\t` by name, everything else `\uXXXX`/`\UXXXXXXXX`.
- Every record- or contract-derived string on the `status` and `report` paths goes through it: the task list (`src/agentmarshal/cli.py:964`), the per-task view's `ID`, `Title`, acceptance trail, scope and both record branches (`src/agentmarshal/journal/status_view.py:158`-`199`, with the dispatch escaping whole renderer lines), and `task_id`/`usage` in `format_report` (`src/agentmarshal/journal/report.py:149`-`174`). `state` comes from the closed `_RECORD_TYPE_STATES` table (`status.py:33`) and `decision` from fixed literals, so leaving them unescaped is correct.
- The delta's MODIFIED header matches the baseline header byte-for-byte, the applied spec text matches the delta, and every delta scenario is named in a test docstring: the seven refusal scenarios in `tests/test_record_text_safety.py`, the four new ones in `tests/test_display.py` and `tests/test_status_view.py:81`.
- The pin test's new record sequence is admissible under `project_status` (completed → reopened → finding → finding-bound completed → reopened → abandoned → session), and the state still projects to `abandoned`, so the pinned header is unchanged. No existing status/report test fixture carries a refused character (the `\u202e`/`\u2028` fixtures in `test_journal.py` and `test_extensions.py` are refusal tests), so the byte-identical claim holds.

Two non-blocking points.

The new sentence appended to the refusal requirement in `openspec/specs/record-text-safety/spec.md:29-31` says a record carrying a refused character "SHALL be escaped where the tool displays it", with no scoping — while the ADDED requirement below it scopes escaping to `status` and `report` and names the gate transcript, the brief and the reviewer prompt as later work. As it stands the spec carries an unqualified SHALL that the code does not yet meet: `src/agentmarshal/journal/brief.py:51` still interpolates an amendment's `reason` straight into the brief. The contract makes that implementation gap a non-goal, so this is about the sentence's breadth, not the missing work.

`tests/test_display.py:35` sweeps all 1,114,112 codepoints and calls `escape_for_display` on each one, and that function scans the value twice per call — several seconds added to the default unit suite for coverage that the refused set plus a sampling of accepted characters and plane boundaries would mostly give. The exhaustive form does pin "every other character is left as it is" in a way sampling cannot, so this is a cost note rather than a defect.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "07ec3b541992d7119e3a64f2cb260aefb6d07858", "verdict": "approved", "findings": [], "advisory_findings": ["spec-escaping-sentence-unscoped-vs-brief", "full-plane-sweep-test-cost"]}
AGENTMARSHAL_VERDICT_END
