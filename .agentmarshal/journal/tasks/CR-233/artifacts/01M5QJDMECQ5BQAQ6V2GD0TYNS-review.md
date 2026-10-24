F-1: `extension_trust.py:1096,1180` prints `state.switches_file` without escaping it; `_personal_names` also interpolates a raw path at line 988. A read-only probe of both successful commands with a newline-bearing clone path produced an extra output line. This violates acceptance criterion 5’s requirement that every displayed value be escaped. Escape these paths before printing.

F-2: `doctor.py:818–823,851–855` reads and reports personal switches even when `personal_names` is empty. A probe with no personal extensions and a stale `format = 2` switches file printed `personal switches: unavailable (...)`. This violates acceptance criterion 5’s unchanged-transcript requirement. Skip the personal switches report when no personal extensions exist.

Acceptance coverage, based on code and test inspection:

1. The archived proposal, design, delta and completed tasks exist; the main spec contains the identical added requirements. All 46 scenarios have matching test docstrings. `tasks.md` records the archive command; its execution was not independently verified.
2. `stages.py` discovers personal extensions through `LocalState`, bypasses discovery in CI, and uses the shared execution/isolation path. Tests cover grant-free execution, clone-directory reads, phases, completion, personal marks, pauses and shared-name collisions.
3. `read_personal_manifest` rejects forbidden fields; doctor lists and checks personal manifests. Tests include `test_doctor_fails_the_check_of_a_personal_manifest_carrying_a_forbidden_field` and `test_record_ext_refuses_a_kind_only_a_personal_manifest_declares`.
4. The CLI passes skips to both completion phases; switch commands persist personal state and refuse shared names. Tests cover skip, disable, enable, preservation of other entries and shared-name refusals.
5. The supplied diff leaves gate code unchanged. `test_a_clone_with_no_personal_extension_prints_exactly_what_it_prints_today` covers the normal absent-extension case, but F-1 and F-2 leave this criterion unmet.

No files were modified. The coordinator reports all six CI checks passed. I did not rerun them: `uv` is unavailable and this workspace is read-only.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "2465fca1e3d35c4f9c3d700cb63a36dbe273c98b",
  "verdict": "changes_required",
  "findings": ["F-1", "F-2"],
  "classes": {
    "F-1": "contract-mismatch",
    "F-2": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Read-only Python probes with filesystem operations mocked",
        "result": "Both switch commands printed a literal newline from the clone path; doctor printed a personal-switch diagnostic with no personal extension names."
      },
      {
        "what": "Compare delta scenario titles with test docstrings and archived delta with main specification",
        "result": "All 46 scenario titles matched; main specification ends with identical added requirements."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-233/contract.md",
      "CONTRIBUTING.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "Supplied diff, implementation files, archived OpenSpec artifacts and personal-extension tests"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "uv is unavailable and the workspace is read-only. Coordinator reports all checks passed."
      }
    ]
  },
  "evidence": {
    "F-1": "src/agentmarshal/extension_trust.py:1096 and :1180; probe returned status 0 with stdout '/clone\\nFORGED-LINE/.git/agentmarshal/switches.toml\\ndisabled mycheck\\n', and equivalent enable output.",
    "F-2": "src/agentmarshal/doctor.py:818 and :851; probe with personal_extension_names returning an empty set produced 'extensions: none\\npersonal switches: unavailable (/clone/.git/agentmarshal/switches.toml: unknown format 2)\\n'."
  }
}
AGENTMARSHAL_VERDICT_END
