Проверил весь дифф против кода на `5797c88`. Ниже — прозовая часть, затем verdict.

**Acceptance criterion 1 (CHANGELOG, AUD-docs-claims-1-1) — met.** `src/agentmarshal/journal/records.py:2113-2124` does `json.dumps` and `.encode()` before `_create_exclusive(path)`, and nothing rolls the file back after creation, so the new wording («a write that fails at that step — an encoding or serialization failure — leaves no record file behind; a failure while writing or closing the created file is not rolled back») states exactly what holds and drops the old over-promise. Demonstrated by `tests/test_record_text_safety.py::test_a_failure_while_encoding_leaves_no_file` (an unpaired surrogate in `outcome` raises `UnicodeEncodeError` and `journal_root` does not exist afterwards).

**Acceptance criterion 2 (README, AUD-docs-claims-1-2) — met.** `README.md:43-56` no longer calls the policy inactive: the preset table it states matches `_PRESETS` in `src/agentmarshal/journal/capture.py:70-86` (`attested`→`hash`, `full`→`commit`, `minimal`→`off`), `capture.overrides.reviews` is the parsed key (`capture.py:211-237`), `commit` pins an artifact (`journal/submit_review.py:137-144`), `hash` lands in local state with a `review-prose` event (`journal/review.py:712-743`), and the not-shipped parts are named separately and correctly: `CaptureClass.ECONOMICS`/`SESSIONS` are read by no production caller (only `review_capture_level_from_journal` is imported, in `review.py:36` and `cli.py:39`), and `journal/attestation.py:21` says in so many words that it emits no Statement. Demonstrated by `tests/test_review_capture.py` together with `tests/test_capture.py` (preset/override resolution) and `tests/test_attestation.py`.

**Acceptance criterion 3 (proposal bodies, AUD-docs-claims-1-3) — met.** All eighteen named proposals plus 009, 016, 018, 020, 023 and 035 got a current-status line, each matching both `docs/proposals/README.md` and the code: 024 `resets_at` (`journal/session.py:45,84`), 025 ADR-0015 by its actual title, 026/039 `previous_review`+`classes`+`report --findings` aggregation (`journal/review.py:93`, `journal/report.py:802-812`, `status_view.py:524`), 027 `advisory_dispositions` with the per-finding requirement (`journal/complete.py:112-123`, `status_view.py:584-601`) and the ADR-0018 quote verbatim at `docs/adr/ADR-0018-governing-the-contract.md:33`, 028 `record-check`/`report`/`brief` (`journal/report.py:58,437`, `journal/brief.py:96-121`), 030 `verification` (`records.py:1166`), 031 the pinned `contract` hash which `open` always writes (`journal/open_task.py:411`) and `agentmarshal agree` (`cli.py:1914`), 032/040 lead time and phases (`journal/report.py:318-374`) with the still-unexposed lane and the branching-but-tree-switching helper (`templates/journal-transaction.sh:115-116`), 034/041 the five outcome values documented in ADR-0022 §4 (lines 176-183) plus `report_ready` and the header fields, 035 the gate warning verbatim (`journal/gate.py:2312`) and `Records absent from <base>` (`cli.py:1530`), 036 the status line verbatim including `(did not end 'implemented')` (`status_view.py:664-676`), 037 the per-file decode (`review.py:1843-1856`), 042 the step events and the still-declined `step` stage (`stages.py:212-213`), 044 wording that matches `CHANGELOG.md:196-204` and `report.py:114-126`, 045 the `SENT` manifest, `skipped as sent: <n>` and `--index` on all three subcommands (`src/agentmarshal/outbox.py:125-142`). Each original finding/disposition text is left intact; the corrections sit in `## Where` or a dated bullet, which is this repo's existing convention (019 and 035 already used it). Demonstrated by `tests/test_unmeasured_session_usage.py`, `tests/test_outbox.py`, `tests/test_status_base.py`, `tests/test_status_candidate_session.py`, `tests/test_review_links_and_classes.py`, `tests/test_review_verification_and_evidence.py`, `tests/test_complete_dispositions.py`, `tests/test_brief_last_failing_check.py`, `tests/test_contract_hash.py`, `tests/test_agree.py`, `tests/test_report_lead_time.py`, `tests/test_gate_independence.py`, `tests/test_journal_transaction.py`, `tests/test_steps.py` and `tests/test_complete_stages.py`.

**Acceptance criterion 4 — met for scope and links.** The diff touches only `CHANGELOG.md`, `README.md` and files under `docs/proposals/`, all in scope; every newly added link target exists (`docs/adr/ADR-0013/0015/0018/0021/0022…`, `docs/proposals/023…`, `029…`, `033…`). I did not re-run the CI sequence; the coordinator reports it green on this commit.

`ADV-readme-capture-off-1` (advisory, claim-accuracy): `README.md:52` says the `off` level "keeps nothing", but `off` only stops the *accepted* verdict's prose from being kept (`journal/review.py:1619-1622`) — a refused verdict's raw reviewer bytes are still written to a file whose path the refusal prints, at every capture level (`journal/review.py:813-824`, `_reject(..., preserve_output=True)` by default), which is the very behaviour `CHANGELOG.md:249-253` advertises. Since this task is about narrowing claims to what holds, the clause would read truer as "`off` keeps nothing of an accepted review's prose". Not blocking: it is one clause in a sentence that is otherwise exact, and the criterion it serves (naming the review class as shipped) is met.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "5797c883853b3534cda3d42194f2b198d1a21637",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-readme-capture-off-1"],
  "classes": {
    "ADV-readme-capture-off-1": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep write_record in src/agentmarshal/journal/records.py (lines 2092-2125)", "result": "json.dumps + .encode() precede _create_exclusive; no rollback after creation — CHANGELOG's narrowed claim holds"},
      {"what": "grep _PRESETS / overrides parsing in src/agentmarshal/journal/capture.py", "result": "attested->HASH, full->COMMIT, minimal->OFF for REVIEWS; 'overrides' key parsed — README's preset table matches"},
      {"what": "grep -rn 'CaptureClass\\.|level_for' src/ excluding capture.py", "result": "only review_capture_level_from_journal imported (review.py:36, cli.py:39); economics and sessions classes read by no production caller"},
      {"what": "grep Statement in src/agentmarshal/journal/attestation.py", "result": "line 21: 'This module owns the declaration; it emits no Statement.'"},
      {"what": "grep -rn 'records of other tasks' / 'Records absent from' src/", "result": "gate.py:2312 and cli.py:1530 match proposal 035's new text verbatim"},
      {"what": "sed -n '630,680p' src/agentmarshal/journal/status_view.py", "result": "'Reviewed commit <sha7>: implementer session <id>' and \"(did not end 'implemented')\" match proposal 036 verbatim"},
      {"what": "grep -rn 'resets_at|report_ready|cli_session|started_at|verification|classes|previous_review|advisory_dispositions|_SESSION_COST_KEYS' src/", "result": "every field named in proposals 018, 024, 026, 027, 030, 031, 032, 041, 042 exists in records.py/session.py/review.py/status_view.py"},
      {"what": "grep -n '^### ' CHANGELOG.md and version headers", "result": "0.6.0 ships extension stages (CR-206..CR-225) and complete running them; 0.5.0 ships cli_session/report_ready/--if-missing (line 379-381); 0.2.0 ships the init outbox scaffold (line 855); 0.4.0 ships the coordination activity (line 599) — the release attributions in 009, 012, 018, 023, 039, 040, 042 check out"},
      {"what": "sed -n '176,205p' docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md", "result": "section 4 is the session outcome vocabulary and documents provider-limit, output-limit, stalled, safety-limit, time-limit; section 5 the implementers/reviewers/independence header — proposals 034 and 041 cite it correctly"},
      {"what": "grep -n 'switch|branch' templates/journal-transaction.sh", "result": "line 115-116 creates journal/<task>-<slug> and git switch -c — proposal 032's 'branches per task' and 040's 'still switches the working tree' both hold"},
      {"what": "grep -n 'add_argument' src/agentmarshal/outbox.py", "result": "--index on check (126), send (134) and status (142) — proposal 045's claim holds"},
      {"what": "grep -c '^## Where' docs/proposals/*.md and grep for pending phrasings in untouched proposals", "result": "every proposal whose README row states a shipped status now carries a matching Where; the remaining 'not shipped yet' lines sit in untouched disposition/finding text or belong to 038 and 043, which the index also lists as not shipped"},
      {"what": "sed -n '435,470p' tests/test_record_text_safety.py", "result": "test_a_failure_while_encoding_leaves_no_file asserts UnicodeEncodeError and that journal_root does not exist — the test behind criterion 1"},
      {"what": "grep -n 'def _reject' -A 12 src/agentmarshal/journal/review.py", "result": "preserve_output defaults to True, so a refused verdict's bytes are kept at any capture level — basis of ADV-readme-capture-off-1"},
      {"what": "resolved every relative link added by the diff against docs/adr/ and docs/proposals/ listings", "result": "all targets exist; no broken link"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section, 0.5.0/0.4.0/0.2.0 headers and the outbox, unmeasured and audit entries)",
      "README.md:41-60",
      "docs/proposals/README.md (all batch tables)",
      "docs/proposals/009, 012, 016, 018, 019, 020, 023, 024, 025, 026, 027, 028, 029, 030, 031, 032, 034, 035, 036, 037, 039, 040, 041, 042, 044, 045",
      "docs/adr/ADR-0013, ADR-0015, ADR-0016, ADR-0018, ADR-0022",
      "src/agentmarshal/journal/records.py, capture.py, review.py, submit_review.py, report.py, status_view.py, brief.py, complete.py, open_task.py, gate.py, attestation.py",
      "src/agentmarshal/stages.py, steps.py, doctor.py, outbox.py, cli.py, project.py",
      "templates/journal-transaction.sh, templates/github/agentmarshal-governance.yml",
      "tests/ listing, tests/test_record_text_safety.py, tests/test_release_audit_check.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; the coordinator states the full sequence passed on 5797c883853b3534cda3d42194f2b198d1a21637"}
    ]
  },
  "evidence": {
    "ADV-readme-capture-off-1": "README.md:52 states '`off` keeps nothing'; src/agentmarshal/journal/review.py:1619-1622 applies `off` only to the accepted verdict's prose, while review.py:813-824 (`_reject`, preserve_output=True by default) writes a refused verdict's raw reviewer bytes to a file and names it in the error — the behaviour CHANGELOG.md:249-253 advertises for refused verdicts at any level"
  }
}
AGENTMARSHAL_VERDICT_END
