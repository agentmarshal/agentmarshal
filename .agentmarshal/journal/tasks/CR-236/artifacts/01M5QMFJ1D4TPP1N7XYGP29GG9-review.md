timestamp-read-regression: At `src/agentmarshal/journal/records.py:609`, the new timestamp refusal also runs when reading historical records. I reproduced a schema-3 record with `created_at="2026-10-01\n10:00:00Z"`: the previous parser accepts it, but current read validation refuses it. This contradicts ADR-0015 decisions 3–4 and `docs/threat-model.md:405`. Register timestamp text safety as a separate write-time rule bound beyond existing schemas.

Acceptance coverage:

1. Timestamp refusal and field-specific messages are implemented in `_utc_timestamp`; `test_a_timestamp_carrying_a_refused_character_is_refused` checks all four fields and absence of the journal directory.
2. `write_record` encodes before directory/file creation; `test_a_failure_while_encoding_leaves_no_file` forces the encoding failure.
3. The artifact-reference rule covers shared write validation while preserving historical reads; `test_an_artifact_ref_carrying_a_refused_character_is_refused_at_write` demonstrates both.
4. Review rejection paths retain raw bytes; `test_rejected_verdict_output_is_kept_as_the_bytes_the_reviewer_wrote` checks invalid UTF-8 byte equality.
5. The archived delta names all timestamp fields and matches the main specification. Each of its four scenarios has a matching test docstring. Use of the archive command and its version could not be independently verified.
6. Serialization retains the existing JSON settings and newline. Transcript coverage includes `test_default_run_transcript_matches_the_committed_fixture`. The coordinator reports all six CI checks passed; I did not rerun them because this snapshot is read-only and `uv` is unavailable.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "ace72390c9f62dad123d1f22df0ba2981f700088",
  "verdict": "changes_required",
  "findings": ["timestamp-read-regression"],
  "classes": {
    "timestamp-read-regression": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "In-memory historical timestamp read-validation reproduction",
        "result": "The old parser accepted a newline separator; current read validation refused it. Disabling only the new timestamp refusal restored successful validation."
      },
      {
        "what": "20 timestamp write-validation cases",
        "result": "All refused with field-specific messages."
      },
      {
        "what": "Invalid UTF-8 verdict rejection with preservation intercepted",
        "result": "Preservation received identical raw bytes."
      },
      {
        "what": "Archived delta and scenario-docstring comparison",
        "result": "Delta matches the main specification; all four scenarios have named test docstrings."
      }
    ],
    "read": [
      "Supplied contract and diff",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/review.py",
      "src/agentmarshal/project.py",
      "docs/adr/ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "CONTRIBUTING.md",
      "Archived OpenSpec delta, main specification, and relevant tests"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "Read-only snapshot; uv unavailable. Coordinator reports the complete sequence passed on the reviewed commit."
      }
    ]
  },
  "evidence": {
    "timestamp-read-regression": "src/agentmarshal/journal/records.py:609; created-at remains bound to schema 1 and session-fields-7 to schema 7. Reproduction: schema-3 created_at='2026-10-01\\n10:00:00Z' parses successfully with datetime.fromisoformat, but _validate_record(..., for_write=False, context={}) raises \"record field 'created_at' must not contain control characters\". Historical-read guarantee: docs/threat-model.md:405 and ADR-0015 decisions 3–4."
  }
}
AGENTMARSHAL_VERDICT_END
