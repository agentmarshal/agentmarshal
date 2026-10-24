Проверил diff против контракта: прочитал все восемь документов из scope и сверил каждое утверждение с кодом (`stages.py`, `cli.py`, `extension_trust.py`, `doctor.py`, `switch_off.py`, `journal/gate.py`, `journal/records.py`, `journal/report.py`, `journal/status_view.py`, `outbox.py`, `isolation.py`, `project.py`, `templates/journal-transaction.sh`, `.github/scripts/check_release_audit.py`), со спеками в `openspec/specs/` и с журналом задач.

## Acceptance criteria — где diff их выполняет

1. **Секция `## 0.6.0 — unreleased` и покрытие задач** — выполнено: секция на `CHANGELOG.md:11` над `## 0.5.0 — 2026-10-23` (`:272`), 13 тематических entry, каждая называет свои CR; CR-205…CR-236 покрыты целиком (CR-205, CR-226, CR-230 — в закрывающей строке `:270`, их контракты действительно documentation/version-only), CR-237 несёт только `opened.json`, поэтому справедливо отсутствует. Открывающее утверждение про неизменные схемы проверяется кодом: `_SUPPORTED_SCHEMAS = {1..7}` (`records.py:192`) и `_SCHEMA_7_ACCEPTANCE_FIELDS = {"accepted_pause", "operational"}` (`records.py:256`) — поля, которые 0.5.0 уже admitted (`CHANGELOG.md:391`); демонстрируют `tests/test_record_schema.py`.
2. **Покрытие всех предметов, каждый сверен с кодом** — выполнено: result-строки `checked` / `failed (exit <n>)` / `did not finish (timeout)` / `not run (<reason>)` / `switched off (<task>, <reason>)` — `stages.py:950-962`, `:912-919`, `:1375-1380`; `extension list` — `extension_trust.py:719-742` (single-file форма строки не получает); `CI=true` — `stages.py:1124`; `record-ext` и 64 KiB — `record_ext.py:23-34`; doctor runtime — `doctor.py:421-461`; `validate` warning — `validate.py:188-191`; `switch off` scope — `switch_off.py:463`, sidecar — `:579`; operational lane — `gate.py:1355`; isolation — `isolation.py:1-42` и `stages.py:717`, один-в-один с `docs/threat-model.md:448-468`; `complete --target` — `cli.py:1133-1150`, post-gate — `cli.py:1207-1227`. Демонстрируют `tests/test_stages.py`, `test_extension_trust.py`, `test_record_ext.py`, `test_doctor_extensions.py`, `test_doctor_wrapper_runtime.py`, `test_validate_addressee.py`, `test_switch_off.py`, `test_gate_operational.py`, `test_isolation.py`, `test_pause_and_operational_acceptance.py`, `test_complete_stages.py`, `test_personal_extensions.py`, `test_status_candidate_session.py`, `test_status_base.py`, `test_outbox.py`, `test_unmeasured_session_usage.py`, `test_release_audit_check.py`.
3. **Параграф «What 0.6.0 leaves out»** — выполнено: пять пунктов, каждый с решением; schema 8 — `records.py:192`; user scope — `ADR-0013:166` («the user scope arrives when an adopter asks»); `next`/`plan.toml` — в `cli.py` нет сабкоманды `next`, `plan_file` читает только `tests/test_localstate.py`; `carried_approval`/`mode: resolution` в `src/` отсутствуют. Демонстрирует `tests/test_record_schema.py`.
4. **UPGRADING 0.5.0 → 0.6.0** — выполнено: нет schema change и ordering rule; grant/`not granted`/`changed after approval` — `stages.py:507-515`; operational lane — `gate.py:1355`; `complete --target` — `cli.py:1133`; `SENT` и `skipped as sent: <n>` — `outbox.py:60,723`, причём leak scan идёт вне `is_draft` (`outbox.py:688`); pin OpenSpec — `.agentmarshal/extensions/openspec.toml:20`. Демонстрируют `tests/test_stages.py`, `test_gate_operational.py`, `test_complete_stages.py`, `test_outbox.py:1294`.
5. **Proposals index, threat model, README, карта docs** — выполнено: 020 больше не «not shipped», 044/045 помечены shipped в 0.6.0 (`record-ext`/`report`/`outbox` подтверждают); перепроверенные строки опираются на реальные факты — `ADR-0018:33`, `ADR-0022:181` (`output-limit`, `stalled`, `safety-limit`), `journal-transaction.sh:116` (`git switch -c` — «всё ещё переключает working tree»), `review.py:341-360` (per-file decode). Threat-model refusals сверены с `stages.py:282` (choices для `--phase`), `:1564-1567` (task id до placement), `:1043` (sidecar), `_base_extensions` (manifest), и все четыре цитаты существуют: `openspec/specs/extension-stages/spec.md:80,92,96,308`. README's outbox — `project.py:446` и `_OUTBOX_README`, демонстрирует `tests/test_journal.py::test_init_scaffolds_the_upstream_outbox`; строки 044/045 в `docs/README.md:87-88`, файлы на месте.
6. **Исправления findings аудита в документации** — выполнено: journal-only = все пути под `.agentmarshal/journal/` — `gate.py:78,1252`; operational lane существует — `gate.py:1353-1355`; 0.4.1 больше не «текущий релиз» в `docs/overview.md` (остались только 0.6.0); self-hosting говорит и про acceptance вместо approving verdict, и про то, что journal-only и operational не требуют review; UPGRADING-правка точна — `INFO: changes_required verdicts for <task>: <count> (threshold <n>)` печатается именно в ветке под порогом (`gate.py:2272-2275`); open question 2 опирается на `openspec/specs/gate-lanes/spec.md:241` («a link or a non-blob at the file's path refuses as not a file»). Демонстрируют `tests/test_gate.py`, `test_gate_operational.py`, `test_acceptance.py`.
7. **Версия 0.6.0** — выполнено: `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11`, `--version` берёт `__version__` (`cli.py:129-131`); демонстрируют `tests/test_smoke.py::test_version_is_declared` и `::test_console_version_prints_package_version`.
8. **Ничего лишнего** — выполнено по форме: меняются ровно 12 путей из scope, текст 0.5.0 и раньше в CHANGELOG не тронут (чистая вставка над `:11`), все добавленные ссылки резолвятся (ADR-0013/0015/0018/0022, `UPGRADING.md`, proposals 044/045). Полную CI-последовательность я не запускал (read-only, без uv/сети) — опираюсь на твоё утверждение про f5fbc8c.

## Advisory findings

- **ADV-AUDIT-FIXES-SCOPE-001** — `CHANGELOG.md:222-223`: entry «Fixes from the release audit (CR-235, CR-236)» говорит «the two tasks named here are their fixes in the code», то есть подаёт две задачи как исправления всех findings аудита по gate-journal, тогда как AUD-gate-journal-4 и -5 держит CR-237, у которого в `records/` лежит только `opened.json` — к релизу эту строку придётся дописать, иначе release notes утверждают больше, чем смержено.
- **ADV-DOCTOR-CHECK-001** — `CHANGELOG.md:65-70`: листинг doctor'а («its form, manifest schema, declared stages and ext kinds, grant state») приписан проверке `extension manifest <name>`, но её detail — только `"<form> form, manifest schema <n>"` (`doctor.py:399-400`); stages, ext kinds, grant и switch-состояние печатает отдельная секционная строка `extension <name>: …` (`doctor.py:772-789`).
- **ADV-OPERATIONAL-LANE-001** — `CHANGELOG.md:86-88` (и то же в `UPGRADING.md`, `docs/overview.md`, `docs/self-hosting-workflow.md:143-146`): «only `.agentmarshal/switches.toml` and the task's own records may change» — формулировка ADR-0013 решения 17, но код admits весь подкаталог задачи, включая `contract.md` (`gate.py:997-1003`, `:921-949`), и у `gate-lanes` есть сценарий «the candidate amends the contract inside its own journal subtree → still takes the operational lane» (`openspec/specs/gate-lanes/spec.md:206-210`); для lane'а, который пропускает review, это преуменьшение стоит поправить.
- **ADV-WRAP-001** — косметика переноса строк, внесённая этим diff: `docs/self-hosting-workflow.md:40` — 106 символов в файле, который везде ≤79; `docs/threat-model.md:270` — 87; `CHANGELOG.md:224` — обрывок «ends, refusal begins: for», и `:241` начинает предложение с новой строки внутри того же абзаца.

Блокирующего не нашёл: содержательно релизные заметки сходятся с кодом по всем восьми критериям.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "f5fbc8c3cce45baf6739b662867ba20b75fe92cf",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-AUDIT-FIXES-SCOPE-001",
    "ADV-DOCTOR-CHECK-001",
    "ADV-OPERATIONAL-LANE-001",
    "ADV-WRAP-001"
  ],
  "classes": {
    "ADV-AUDIT-FIXES-SCOPE-001": "claim-accuracy",
    "ADV-DOCTOR-CHECK-001": "claim-accuracy",
    "ADV-OPERATIONAL-LANE-001": "claim-accuracy",
    "ADV-WRAP-001": "style"
  },
  "verification": {
    "executed": [
      {"what": "ls .agentmarshal/journal/tasks + ls of CR-233..CR-237 records", "result": "CR-233, CR-235, CR-236 carry completed records; CR-234 and CR-237 carry only opened.json — so CR-235/CR-236 are merged fixes and CR-237 is not"},
      {"what": "grep for the stage result-line vocabulary in src/agentmarshal/stages.py", "result": "stages.py:950-962 _result_text returns checked / failed (<reason>) / did not finish (<reason>) / switched off (<reason>) / not run (<reason>); :919 reason is 'exit <n>', :913 'timeout', :1377 '<task>, <reason>'"},
      {"what": "grep 'extension list' output strings in src/agentmarshal/extension_trust.py", "result": "extension_trust.py:733,736,741 print '<name>: not granted', 'granted', 'changed after approval: <path> (<kind>)'; :724 skips non-directories, so a single-file manifest gets no line"},
      {"what": "read src/agentmarshal/journal/gate.py lane classification", "result": "gate.py:78 _JOURNAL_PREFIX='.agentmarshal/journal/'; :1252 journal_only = all(path.startswith(_JOURNAL_PREFIX)); :1352-1355 the two PASS lines, the operational one byte-for-byte as CHANGELOG quotes it"},
      {"what": "read gate.py:2238-2276 (changes_required count line)", "result": "the under-threshold branch prints 'INFO: changes_required verdicts for {task_id}: {count} (threshold {threshold})' and is skipped on the journal-only and operational lanes — matching UPGRADING.md's corrected 0.4.1 -> 0.5.0 note"},
      {"what": "read gate.py:969-1017 operational_candidate", "result": "the lane admits '.agentmarshal/switches.toml' plus every path under '.agentmarshal/journal/tasks/<task>/' (docstring: 'the task's own subtree, contract included'), and requires contract.scope == (SWITCHES_RELPATH,)"},
      {"what": "read gate.py:2085-2165 (CR-235 and the CR-210 warning)", "result": "the other-task lifecycle projection FAILs naming the task and the reason; the warning string 'WARN: candidate adds opened/amendment records of other tasks' is at :2159"},
      {"what": "read records.py:192, :256, :590-650, :2092-2125 (CR-236 and the schema ceiling)", "result": "_SUPPORTED_SCHEMAS={1..7}; schema-7 acceptance fields are accepted_pause/operational; the timestamp-text rule refuses created_at/started_at/ended_at/resets_at before the parse and is bound past today's schemas; write_record encodes to bytes before _create_exclusive"},
      {"what": "grep outbox SENT manifest and the skip path in src/agentmarshal/outbox.py", "result": "_SENT='SENT' (:60), 'skipped as sent: <n>' (:723), --index on check/send/status (:117-141); hits.extend(_draft_hits(...)) at :688 sits outside the is_draft guard, so the leak scan covers skipped files"},
      {"what": "read report.py:213-233 and status_view.py:305-317 (unmeasured)", "result": "_is_unmeasured = session record, no 'usage', every token count zero; status appends ' tokens=unmeasured'; report carries unmeasured=/unmeasured_without_cost= on the task, Summary and Cost lines (:731,:779,:812)"},
      {"what": "grep the four extension-stages quotes the threat model adds", "result": "openspec/specs/extension-stages/spec.md:80, 92, 96, 308 carry them verbatim; openspec/specs/gate-lanes/spec.md:241 carries the switches-file requirement including 'a link or a non-blob at the file's path refuses as not a file'"},
      {"what": "read src/agentmarshal/project.py:232-446 (what init writes)", "result": "init writes .agentmarshal/project.json and scaffolds .agentmarshal/upstream/README.md and nothing else, so README's enumeration is complete"},
      {"what": "read .github/scripts/check_release_audit.py and .github/workflows/release.yml", "result": "ALWAYS_ALLOWED + fixed-task scopes bound the post-audit diff; ALLOWED_MODELS, merge-base --is-ancestor, _DISPOSITIONS and the last-lifecycle-record=='completed' rule are all present; the step runs before 'uv build'"},
      {"what": "grep version strings", "result": "pyproject.toml:3 and src/agentmarshal/__init__.py:3 and uv.lock:11 all read 0.6.0; tests/test_smoke.py:48 asserts it and :51-59 asserts `agentmarshal --version` prints __version__; no 0.6.0.dev0 remains outside the append-only journal"},
      {"what": "grep -nE '^.{80}' over the changed documents", "result": "docs/self-hosting-workflow.md:40 (106 chars) is the only over-length line in that file; docs/threat-model.md:270 (87) is newly added beside one pre-existing long line"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section, lines 11-270, and the 0.5.0 section for the history and interop claims)",
      "UPGRADING.md (the new 0.5.0 -> 0.6.0 section and the corrected 0.4.1 -> 0.5.0 note)",
      "README.md",
      "docs/threat-model.md (the stage-line refusals and open question 2)",
      "docs/proposals/README.md",
      "docs/README.md",
      "docs/overview.md",
      "docs/self-hosting-workflow.md",
      "docs/quickstart.md (contract principles, the 0.5.0-pinned install the contract leaves out of scope)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decisions 13, 16, 17, the scope table)",
      "docs/adr/ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md (referenced)",
      "docs/adr/ADR-0018-governing-the-contract.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md (sections 2, 3, 4, 7, 8)",
      "docs/adr/ADR-0023-next-the-next-step-of-a-task.md",
      "openspec/specs/extension-stages/spec.md",
      "openspec/specs/gate-lanes/spec.md",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/isolation.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/record_ext.py",
      "src/agentmarshal/project.py",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/validate.py",
      "src/agentmarshal/journal/complete.py",
      "src/agentmarshal/journal/capture.py",
      "templates/journal-transaction.sh",
      ".github/scripts/check_release_audit.py",
      ".github/workflows/release.yml",
      ".agentmarshal/extensions/openspec.toml",
      ".agentmarshal/journal/tasks/CR-234/contract.md",
      ".agentmarshal/journal/tasks/CR-235/contract.md",
      ".agentmarshal/journal/tasks/CR-236/contract.md",
      ".agentmarshal/journal/tasks/CR-237/contract.md",
      "tests/test_smoke.py",
      "tests/test_journal.py (init outbox tests)",
      "tests/test_outbox.py",
      "tests/test_personal_extensions.py",
      "tests/test_gate_operational.py",
      "tests/test_status_candidate_session.py",
      "tests/test_validate_addressee.py",
      "tests/test_project.py",
      "tests/test_localstate.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "read-only review sandbox without uv or network; the coordinator states the sequence passed on f5fbc8c, so no check-failure claim is made"},
      {"what": "agentmarshal --version as a process", "why": "command execution was declined in this sandbox; the wiring (cli.py:129-131) and tests/test_smoke.py::test_console_version_prints_package_version were read instead"},
      {"what": "git log / git diff against master", "why": "the snapshot is not a git repository, so merge state was established from the journal's lifecycle records instead"}
    ]
  },
  "evidence": {
    "ADV-AUDIT-FIXES-SCOPE-001": "CHANGELOG.md:222-223 'The audit filed findings against the gate's journal handling; the two tasks named here are their fixes in the code.' vs .agentmarshal/journal/tasks/CR-237/contract.md Context 'Release audit 0.6.0, area gate-journal, findings AUD-gate-journal-5 and -4 (confirmed by reproduction)'; `ls .agentmarshal/journal/tasks/CR-237/records` -> only 01M5QJ09B8H4RGPVRRJ8TE7K1S-opened.json (no completed record)",
    "ADV-DOCTOR-CHECK-001": "CHANGELOG.md:65-70 places the listing 'under an `extension manifest <name>` check per extension'; src/agentmarshal/doctor.py:399-400 `return True, f\"{form} form, manifest schema {manifest.schema}\"` is that check's whole detail, while src/agentmarshal/doctor.py:775-789 builds the stages/ext-kinds/grant/switch parts for the separate `extension <name>: …` section line",
    "ADV-OPERATIONAL-LANE-001": "CHANGELOG.md:86-88, UPGRADING.md ('changes only `.agentmarshal/switches.toml` and its own task's records'), docs/overview.md:141-144, docs/self-hosting-workflow.md:143-146 vs src/agentmarshal/journal/gate.py:997-1003 (`elif not path.startswith(task_prefix): return None`, task_prefix = '.agentmarshal/journal/tasks/<task>/') and gate.py:926-934 plus openspec/specs/gate-lanes/spec.md:206-210 'the candidate amends the contract inside its own journal subtree -> the candidate still takes the operational lane'",
    "ADV-WRAP-001": "`grep -nE '^.{80}' docs/self-hosting-workflow.md` -> single hit, line 40 ('that commit, and the evidence records are append-only and consistent. The `am-merge` host wrapper runs', 106 chars) in a file otherwise wrapped at <=79; docs/threat-model.md:270 (87 chars); CHANGELOG.md:224 is the 25-char fragment 'ends, refusal begins: for' and CHANGELOG.md:241 starts '`write_record` encodes the record to bytes' on a fresh line inside the same paragraph"
  }
}
AGENTMARSHAL_VERDICT_END
