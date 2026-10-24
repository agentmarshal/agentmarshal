I reviewed the diff against the contract and checked every behavioural claim against the source at `71cd0352ad3656bec517a74887764e11b881908f`.

## Acceptance criteria

**AC1 — the 0.6.0 CHANGELOG section.** Met. `CHANGELOG.md:11` opens the section above 0.5.0 (`CHANGELOG.md:276`), states the no-schema-change / mutual-readability point and links `UPGRADING.md`. I enumerated the journal: every task from CR-205 to CR-236 carries a `-completed.json` except CR-234 itself (CR-237 holds only an `opened`), and the section names all of them — the feature entries by heading, and CR-205 (the `0.6.0.dev0` bump), CR-226 and CR-230 in the one closing line at `CHANGELOG.md:273`. The "no schema changes" claim holds: `records.py:192` `_SUPPORTED_SCHEMAS = {1..7}`, `contracts.py:191` `{1,2,3}`, `extensions.py:387` `{1,2}` — all as 0.5.0 declared. No test covers changelog prose; the underlying version assertion is `tests/test_smoke.py::test_version_is_declared`.

**AC2 — every subject covered and checked against the code.** Met. Grants: `extension_trust.py:719-742` prints exactly `granted` / `not granted` / `changed after approval: <path> (<kind>)` and skips the single-file form. Stage lines: `stages.py:950-962` gives exactly the five tails, `stages.py:916-921` produces `failed (exit <n>)` and `did not finish (timeout)`. Command-level refusals printing no stage line: unknown phase `stages.py:1034` (and `--phase` choices at `stages.py:284`), sidecar `stages.py:1043`, invalid task id `stages.py:1564-1568`, unreadable base manifest `stages.py:1095-1098`. Grant rule and CI: `stages.py:499-515` (`not granted`, `changed after approval: <path>`), `stages.py:500` skips the grant in CI. `record-ext`: `record_ext.py:13-34,130-159`. `doctor`: checks at `doctor.py:557,575` with detail `<form> form, manifest schema <n>` (`doctor.py:400`) and the listing at `doctor.py:772-789`. `validate`: `validate.py:188-191` matches the quoted line verbatim. Switches/operational lane: `gate.py:969-1017` and `gate.py:1355-1450` match the entry's description of the lane, the verdict line and the `NOT EXAMINED` checks; `switch_off.py:463` emits the contract scope exactly. Isolation: `isolation.py:310-312` (bind + locked flags + `chdir`), `isolation.py:243-253` (capability drop), `stages.py:1194` (withheld provider secrets), `stages.py:1495-1499` (`stage run: note: … not enforced`) — and nothing is stated as enforced beyond `docs/threat-model.md:448-470`. Pause and completion: `stages.py:1484-1488` (`pause accepted by <party> (<reason>)`), `cli.py:1122-1156` (pre-gate run, exit 3, `--target` warning). Personal scope: `stages.py:658-675,1460,1524` and `extension_trust.py:25-38`. Outbox: `outbox.py:643-647,723`. Unmeasured: `report.py:213-228`, `status_view.py:316-317`, `report.py:731,779,812`. OpenSpec pin: `.agentmarshal/extensions/openspec.toml` (`schema = 1`, `version = "1.15.0"`). Release audit: `.github/workflows/release.yml:53-63` runs the check before `uv build`; `check_release_audit.py:49,188-193,313-331`. Demonstrated by `tests/test_stages.py`, `test_extension_trust.py`, `test_gate_operational.py`, `test_switch_off.py`, `test_isolation.py`, `test_complete_stages.py`, `test_pause_and_operational_acceptance.py`, `test_record_ext.py`, `test_validate_addressee.py`, `test_doctor_extensions.py`, `test_personal_extensions.py`, `test_outbox.py`, `test_unmeasured_session_usage.py`, `test_release_audit_check.py`.

**AC3 — what is decided but not shipped.** Met (`CHANGELOG.md:255-272`). Schema 8 is refused (`records.py:192`); the user scope is unimplemented (no `~/.config/agentmarshal` reader in `src/`) and ADR-0013:166 does reserve it "when an adopter asks"; there is no `next` subcommand and nothing reads `plan.toml` (`localstate.py:70` defines the path and no caller uses it).

**AC4 — UPGRADING 0.5.0 → 0.6.0.** Met (`UPGRADING.md:3-60`), above the 0.4.1 → 0.5.0 section. Each statement checks out, including the lane's two extra preconditions (`gate.py:1007-1016`), the `--target` sentence (`cli.py:1133-1147`) and the pin being a declaration only — nothing in the manifest reader compares top-level `version` against an installed product.

**AC5 — proposals index, threat model, README, docs/README.** Met apart from one advisory, below. 020's row now reads `shipped in 0.5.0`; I checked each "shipped" claim against the 0.5.0/0.6.0 record and found none overstated — including 039's "contract principles stand in the quickstart's contract guidance" (`docs/quickstart.md:189-201`), 032's "the shipped required-check template runs all of it" (`templates/github/agentmarshal-governance.yml:78`), and the ADR-0018 quotation (`ADR-0018:31-32`). The threat model's four new refusals are the ones the code makes, and the open question on a symlinked `switches.toml` is correctly retired — `openspec/specs/gate-lanes/spec.md:249-250` publishes "a link or a non-blob at the file's path refuses as not a file", implemented at `gate.py:1044-1045`. README's outbox claim matches `project.py:446` / `_scaffold_outbox`, which writes `.agentmarshal/upstream/README.md` and nothing else beyond `project.json`. `docs/README.md` gains the two lines and both targets exist.

**AC6 — release-audit corrections.** Met. `journal_only` is literally `all(path.startswith(".agentmarshal/journal/"))` (`gate.py:1252`, prefix at `gate.py:78`); overview no longer mentions 0.4.1 or 0.5.0 anywhere; the self-hosting note's acceptance sentence matches `gate.py:1770-1771` (findings covered *exactly*); the UPGRADING correction matches `gate.py:2274-2276` verbatim.

**AC7 — version.** Met: `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11`, and `tests/test_smoke.py::test_version_is_declared` plus `::test_console_version_prints_package_version` (the parser takes `version=__version__` at `cli.py:129-131`).

**AC8 — no history rewritten, links resolve, no other files.** Met. The only pre-0.6.0 history statement changed is the sanctioned UPGRADING 0.4.1 → 0.5.0 note; every added link (`docs/adr/ADR-0013…`, `ADR-0015…`, `ADR-0018…`, `ADR-0022…`, proposals 044/045) resolves; the diff touches only scope paths.

## Finding

**ADV-PROPOSALS-NO-WHERE-001 (advisory, non-blocking)** — In `docs/proposals/README.md` the 2026-08-30 batch table (`docs/proposals/README.md:234`) has columns `# | Theme | Reporters | Disposition` and no "where" column, so proposals from that batch whose work has since shipped are not shown as shipped with a version. Proposal 009 (`:244`) is the clearest case: its disposition says it was "answered by ADR-0013", and ADR-0013's executing half is exactly what this release ships; 008 (`:243`, session/token accounting) has parts that landed in 0.5.0. Read literally, AC5's "every proposal shipped in 0.5.0 or 0.6.0 is shown as shipped with its version" is not satisfied for that table. I am flagging it rather than blocking because the file's own prose (`:63-65`) documents the missing column as a deliberate pre-convention difference, and AC5's parenthetical names only 020 — so this may well be outside the criterion's intent, and correcting it means adding a column to a table the task never touched.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "71cd0352ad3656bec517a74887764e11b881908f",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-PROPOSALS-NO-WHERE-001"],
  "classes": {
    "ADV-PROPOSALS-NO-WHERE-001": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {"what": "enumerated completed tasks: find .agentmarshal/journal/tasks -name '*-completed.json'", "result": "CR-205..CR-236 all completed except CR-234 (this task); CR-237 holds only an opened record — the CHANGELOG's task list is exactly the set of tasks completed since v0.5.0"},
      {"what": "grep -H '^title' over .agentmarshal/journal/tasks/CR-2*/contract.md", "result": "every CR id in a 0.6.0 heading matches the work that heading describes; CR-205 (0.6.0.dev0 bump), CR-226 (documentation), CR-230 (digests) correctly sit in the closing documentation/process line"},
      {"what": "grep for schema bounds in records.py, contracts.py, extensions.py", "result": "_SUPPORTED_SCHEMAS = {1,2,3,4,5,6,7}; contract header {1,2,3}; manifest {1,2} — unchanged from 0.5.0, so the 'no schema change' claim holds"},
      {"what": "grep -rn '0.6.0.dev0' over the working tree", "result": "only historical journal records carry it; pyproject.toml, __init__.py, uv.lock:11 and tests/test_smoke.py all read 0.6.0"},
      {"what": "grep -n '0.4.1|0.5.0' docs/overview.md", "result": "no matches — the stale current-release references are gone"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 and 0.5.0 sections)",
      "UPGRADING.md",
      "README.md",
      "docs/threat-model.md",
      "docs/proposals/README.md",
      "docs/overview.md",
      "docs/self-hosting-workflow.md",
      "docs/README.md",
      "docs/quickstart.md",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/isolation.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/record_ext.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/project.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/validate.py",
      "src/agentmarshal/journal/review.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/attestation.py",
      "src/agentmarshal/journal/acceptance.py",
      "templates/journal-transaction.sh",
      "templates/github/agentmarshal-governance.yml",
      ".github/workflows/release.yml",
      ".github/scripts/check_release_audit.py",
      ".agentmarshal/extensions/openspec.toml",
      "openspec/specs/gate-lanes/spec.md",
      "openspec/specs/extension-stages/spec.md",
      "openspec/specs/extension-manifest/spec.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0018-governing-the-contract.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "tests/test_smoke.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the review environment denied the command; the coordinator attests the full sequence passed on this commit, and I report no tool-failure finding"}
    ]
  },
  "evidence": {
    "ADV-PROPOSALS-NO-WHERE-001": "docs/proposals/README.md:234 — the 2026-08-30 batch header row is '| # | Theme | Reporters | Disposition |' with no 'where' column; :244 proposal 009 'answered by ADR-0013' and :243 proposal 008 'Session/token accounting is not in the core' therefore carry no shipped-in version, although ADR-0013's executing half ships in 0.6.0 (CHANGELOG.md:13-21) and the cost/accounting fields shipped in 0.5.0 (CHANGELOG.md:382-392). The file's own convention note at docs/proposals/README.md:63-65 documents the absent column."
  }
}
AGENTMARSHAL_VERDICT_END
