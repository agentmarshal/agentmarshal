No blocking or advisory findings.

- Acceptance 1: `extensions.py` extracts the existing file-form refusal into one shared validator; `gate.py` calls it. `test_single_file_manifest_at_the_base_naming_a_directory_path_is_refused` covers commands and both lock forms using real Git trees.
- Acceptance 2: `switches.py` adds NaN-aware, type-sensitive equality, used by `switch_off.py` and `extension_trust.py`. Added tests cover switch off, enable, and disable. Direct checks of all three verifiers passed.
- Acceptance 3: All changed files are within scope; requirements and existing transcripts are unchanged in the supplied diff. Existing transcript and rewrite-preservation tests cover compatibility. Full CI passed according to the coordinator; I could not rerun it here.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4f11e156190296ff82e213032b2cf048434b209d",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "executed": [
      {
        "what": "Direct invocation of the existing TOML equality regression test",
        "result": "Passed"
      },
      {
        "what": "Direct NaN rewrite-verification checks for switch off, disable, and enable",
        "result": "All passed"
      }
    ],
    "read": [
      "Supplied CR-239 contract and diff",
      "All changed source files and regression tests",
      "Existing transcript and rewrite-preservation tests",
      "CONTRIBUTING.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/threat-model.md",
      "openspec/specs/extension-manifest/spec.md"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "uv is unavailable; pytest is also unavailable. Coordinator reports the full sequence passed on the reviewed commit."
      },
      {
        "what": "Independent verification of the snapshot commit SHA",
        "why": "The supplied snapshot has no Git metadata."
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
