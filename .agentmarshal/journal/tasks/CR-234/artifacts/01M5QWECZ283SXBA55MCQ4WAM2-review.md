Review complete. I verified the diff's claims against the source rather than the specs' prose alone.

## Acceptance criteria

**AC1 — the `## 0.6.0 — unreleased` section.** Met. `CHANGELOG.md:11` opens the section above 0.5.0 (`CHANGELOG.md:276`), grouped by subject, every heading naming its CR ids, with the schema-compatibility opener and the UPGRADING pointer at `CHANGELOG.md:19-23`. Coverage of CR-205…CR-236 is complete: CR-206–233, 235, 236 named in entries; CR-205, CR-226, CR-230 in the closing line at `CHANGELOG.md:274`. CR-237 exists but holds only an `opened` record (`.agentmarshal/journal/tasks/CR-237/records/`), so it is correctly absent. No test demonstrates a documentation criterion; this one is verified by reading.

**AC2 — what the section covers, each checked against the code.** Met. Spot-verified against source, not memory: the grant/`trust.toml`/`trust-changed` claims against `extension_trust.py:8-15,614,733-741`; the single-file form getting no line against `extension_trust.py:724` (`if not entry.is_dir(): continue`); the five result-line forms against `_result_text` (`stages.py:950-962`) and `exit {returncode}` (`stages.py:919`); the four command-level refusals against `stages.py:1035` (unknown phase), `stages.py:1043` (sidecar), `stages.py:1563` (`validate_task_id` ahead of placement) and `stages.py:1096` (`_base_extensions` raising); CI bypass at `stages.py:11,460`; exit 3 at `stages.py:1546`; the `validate` warning byte-for-byte at `validate.py:189-191`; the operational verdict string at `gate.py:1355`; the generated contract scope at `switch_off.py:463`; `complete --target` at `cli.py:353`; `accept --pause/--operational` at `cli.py:224,233`; the isolation paragraph side-by-side with `docs/threat-model.md:448-470` — nothing is stated as enforced that the threat model does not. CR-233 is merged on master (`completed` record present; `read_personal_manifest` at `extension_trust.py:263`, `--skip-ext` at `stages.py:294`), so the entry describes master. Demonstrating tests exist per feature (e.g. `tests/test_extension_trust.py`, `tests/test_doctor_extensions.py`, `tests/test_outbox.py`), but no test asserts the changelog text.

**AC3 — the "leaves out" paragraph.** Met (`CHANGELOG.md:252-272`). Each negative claim holds in code: `_SUPPORTED_SCHEMAS = frozenset({1,…,7})` (`records.py:192`) with `artifact-ref-text`/`timestamp-text` bound at 8 (`records.py:1598-1599`); no `next` subcommand and `plan_file` (`localstate.py:70`) read by nothing; `carried_approval` and `mode: resolution` absent from `src/` entirely; the user scope reserved "when an adopter asks" at `ADR-0013:165-166` with the exact `~/.config/agentmarshal/extensions/` path at `ADR-0013:161`.

**AC4 — UPGRADING 0.5.0 → 0.6.0.** Met, inserted above `## 0.4.1 → 0.5.0`. All five required statements present and checked: `not run (not granted)` at `stages.py:507`; the lane's two extra preconditions at `gate.py:1007` and `gate.py:1009-1016`; `complete --target`; the `SENT` manifest (`outbox.py:60,537`) and `--index` on both `check` and `send` (`outbox.py:120,129`); the OpenSpec pin at `.agentmarshal/extensions/openspec.toml` (`version = "1.15.0"`).

**AC5 — the four deferred documentation items.** Met. `docs/proposals/README.md` now shows 020's acknowledge as shipped in 0.5.0, and every other "shipped" claim I sampled holds (023/028/029/030/031/034/037's rows against the 0.5.0 section at `CHANGELOG.md:301-447`; 019/032/035/039's 0.6.0 rows against `templates/journal-transaction.sh` and `gate.py:2159`; the ADR-0018 quote verbatim at `ADR-0018:31-32`; `output-limit`/`stalled`/`safety-limit` at `ADR-0022:181-182`). The threat model's refusal list matches `stages.py`/`cli.py`. README names `.agentmarshal/upstream/README.md` among `init`'s writes, which `_scaffold_outbox` (`project.py:298-331`) does write. `docs/README.md:87-88` adds 044 and 045 in the 041–043 form.

**AC6 — release-audit documentation fixes.** Met. `journal_only = all(path.startswith(".agentmarshal/journal/"))` at `gate.py:78,1252` matches the new overview wording; no `0.4.1`-as-current remains in `docs/overview.md`; the acceptance-covers-findings path is `gate.py:1768-1774` (exact set equality); the `INFO: changes_required verdicts for …` line is `gate.py:2274`, which makes the corrected 0.4.1 → 0.5.0 note true; the symlink refusal the open question now points at is `gate-lanes/spec.md:249-250`.

**AC7 — the version is 0.6.0.** Met in `pyproject.toml:3`, `src/agentmarshal/__init__.py:3` and `uv.lock:11`; demonstrated by `tests/test_smoke.py::test_version_is_declared` (asserts `"0.6.0"`) and `test_console_version_prints_package_version` (asserts `--version` stdout equals it). No `0.6.0.dev0` remains anywhere outside the journal. Setting a non-dev version here is what `CONTRIBUTING.md:129-133` prescribes for the release task.

**AC8 — nothing else changes, links resolve.** Met. The diff touches only the twelve scoped paths. Every link added resolves: the four ADR filenames (`ADR-0013-…`, `ADR-0015-…`, `ADR-0018-…`, `ADR-0022-…`) and the two proposal files exist as named.

## Advisory finding

**ADV-CITE-001** — in `docs/threat-model.md:270-277`, the four specification citations the diff adds for the command-level refusals ("a manifest the base cannot parse fails the run naming the extension", "a sidecar runs no stages", "an invalid task identifier refuses before any stage is planned", "a malformed trust.toml fails the command naming it") name `#### Scenario:` headings, not requirements. The document's own preamble (`docs/threat-model.md:9-11`) says it cites "a specification under `openspec/specs/` by its capability and requirement", and every other citation I sampled — including the one this same diff adds at line 285 ("the operational lane verifies the switches file against the task and the base") — names a `### Requirement:`. The supporting text does exist verbatim in the named specification, so no statement is unsupported; a reader following the stated convention is simply pointed at a heading level the convention does not use. The covering requirements would be "`stage run` invokes the declared stages of the base's shared extensions" (`extension-stages/spec.md:30`) and "on a workstation a stage runs only under a matching grant" (`:276`).

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "71cd0352ad3656bec517a74887764e11b881908f",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-CITE-001"],
  "classes": {
    "ADV-CITE-001": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep for the version in pyproject.toml, src/agentmarshal/__init__.py, uv.lock, tests/test_smoke.py", "result": "0.6.0 in all four; no 0.6.0.dev0 remains outside the journal"},
      {"what": "grep -rF for each output string the CHANGELOG quotes (not granted, changed after approval, did not finish (timeout), shared switches file unreadable, a shared extension of this name wins, skipped for this run, disabled (personal), trust-changed, extension-event, pause accepted by, operational lane; review not required, addressee not found, tokens=unmeasured, unmeasured=, skipped as sent, Records absent from, implementer session, did not end 'implemented') over src/", "result": "every string found at its claimed site; stages.py:950-962 _result_text, gate.py:1355, validate.py:189-191, status_view.py:317,684,692, report.py:731,779,812, outbox.py:723, cli.py:1436,1445,1528"},
      {"what": "read stages.py:1026-1115 and 1545-1600 for the refusal order", "result": "unknown phase (1035), sidecar (1043), base manifest unreadable (1096), task id validated in _run_stages before placement (1563) — none print a stage line"},
      {"what": "read gate.py:1252, 2038-2165, 969-1017, 1750-1830, 2238-2276", "result": "journal-only lane keys on .agentmarshal/journal/ (78,1252); other-task lifecycle projection and the CR-210 warning confirmed; operational_candidate closes the lane on a scope mismatch (1007) or an unjudgeable base (1009-1016); acceptance requires exact finding-set equality (1771); INFO changes_required line at 2274"},
      {"what": "read records.py:192, 598-637, 1595-1609 for the CR-236 claims", "result": "_SUPPORTED_SCHEMAS ends at 7; timestamp-text covers created_at/started_at/ended_at/resets_at; artifact-ref-text and timestamp-text bound at schema 8, so they reach no loadable record"},
      {"what": "grep src/ for carried_approval, mode: resolution, an agentmarshal next subcommand, and readers of plan.toml", "result": "no match for the first two; no next subcommand; localstate.py:70 plan_file has no caller"},
      {"what": "read project.py:232-331", "result": "_scaffold_outbox writes .agentmarshal/upstream/README.md, confirming the README claim about init"},
      {"what": "list docs/adr/ and docs/proposals/ and resolve every link target added by the diff", "result": "all six added targets exist; no broken link introduced"},
      {"what": "list .agentmarshal/journal/tasks/ and read the records of CR-204, CR-233, CR-235, CR-236, CR-237", "result": "CR-233/235/236 completed; CR-237 holds only an opened record, so the CR-205..CR-236 coverage line is complete"},
      {"what": "grep openspec/specs/extension-stages/spec.md for the four phrases the threat model newly cites", "result": "found at lines 80, 92, 96 and 308 as '#### Scenario:' headings, not '### Requirement:' headings (ADV-CITE-001)"},
      {"what": "grep openspec/specs/ for four pre-existing threat-model citations", "result": "process-log:98, gate-lanes:170, extension-records:383, extension-manifest:208 — all '### Requirement:', establishing the convention the new citations depart from"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section in full; 0.5.0 and 0.4.1 sections for the history claims)",
      "UPGRADING.md (the new 0.5.0 -> 0.6.0 section and the corrected 0.4.1 -> 0.5.0 note)",
      "README.md (trust boundary, Status, Quickstart and journal-transaction prose)",
      "docs/overview.md (glossary Record and Lane entries; the roadmap section)",
      "docs/proposals/README.md (the preamble and every changed row)",
      "docs/self-hosting-workflow.md (gate step and Notes)",
      "docs/threat-model.md (isolation paragraph, the stage-line refusals, open questions 2 and 5, the citation convention at lines 9-11)",
      "docs/README.md (the proposals block)",
      "docs/quickstart.md (contract guidance, for proposal 039's row)",
      "AGENTS.md, CONTRIBUTING.md (release order and the .dev0 version rule)",
      "openspec/specs/gate-lanes/spec.md (the operational-lane requirements)",
      "openspec/specs/extension-stages/spec.md (requirement headings)",
      "src/agentmarshal/stages.py, extension_trust.py, switch_off.py, outbox.py, doctor.py, project.py, localstate.py, record_ext.py, cli.py",
      "src/agentmarshal/journal/gate.py, records.py, validate.py, status_view.py, report.py, attestation.py",
      "templates/journal-transaction.sh, .github/scripts/check_release_audit.py, .github/workflows/agentmarshal-governance.yml",
      ".agentmarshal/extensions/openspec.toml",
      ".agentmarshal/journal/tasks/CR-235/contract.md, CR-236/contract.md",
      "docs/adr/ADR-0013, ADR-0018, ADR-0022, ADR-0023"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the review snapshot is not a git repository and the project environment is not provisioned here; the coordinator states the full sequence passed on 71cd0352ad3656bec517a74887764e11b881908f, and I make no claim that any of these tools fails"}
    ]
  },
  "evidence": {
    "ADV-CITE-001": "docs/threat-model.md:270-277 cites \"a manifest the base cannot parse fails the run naming the extension\", \"a sidecar runs no stages\", \"an invalid task identifier refuses before any stage is planned\" and \"a malformed trust.toml fails the command naming it\"; grep -rn -F over openspec/ returns openspec/specs/extension-stages/spec.md:80, :92, :96 and :308, each prefixed '#### Scenario: ', while grep -n '^### Requirement:' openspec/specs/extension-stages/spec.md does not list any of the four. The document's convention is stated at docs/threat-model.md:9-11 ('a specification under `openspec/specs/` by its capability and requirement'); sampled pre-existing citations resolve to requirements (openspec/specs/process-log/spec.md:98, gate-lanes/spec.md:170, extension-records/spec.md:383, extension-manifest/spec.md:208), as does the citation the same diff adds at docs/threat-model.md:285 (gate-lanes/spec.md:241)."
  }
}
AGENTMARSHAL_VERDICT_END
