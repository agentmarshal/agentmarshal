Разобрал контракт, дифф и окружающий код. Ниже — проза по каждому критерию приёмки и по двум advisory-находкам.

**Критерий 1 (change + archive + тест на каждый сценарий) — выполнен.** `openspec/changes/archive/2026-10-24-accept-pause-operational/` содержит `proposal.md`, `design.md`, `tasks.md` и дельту `specs/operator-acceptance/spec.md` с тремя ADDED-требованиями и одним MODIFIED (тем самым, чей хвост «nothing else SHALL act on the new forms» устарел); `openspec/changes/` не содержит ничего кроме `archive/`, то есть команда архивации действительно прошла. Блок ADDED дельты (строки 5–149) побайтово совпадает с `openspec/specs/operator-acceptance/spec.md:167-311`, а MODIFIED (153–199) — с `spec.md:119-166` с точностью до одной хвостовой пустой строки. Все 15 новых сценариев имеют тест с докстрингом, который их называет, в `tests/test_pause_and_operational_acceptance.py`: `test_a_pause_acceptance_is_written_for_a_declared_extension_at_the_resolved_commit`, `..._where_no_review_stands`, `test_a_short_or_symbolic_commit_resolves_to_the_full_id`, `test_a_commit_that_does_not_resolve_is_refused_writing_nothing`, `test_an_extension_no_shared_manifest_declares_is_refused_naming_it`, `..._whose_manifest_cannot_be_read_...`, `test_an_extension_declared_in_the_directory_form_is_accepted`, `test_a_task_that_admits_no_acceptance_is_refused_writing_nothing`, `test_an_operational_acceptance_is_written_at_the_resolved_commit`, `test_an_operational_commit_that_does_not_resolve_is_refused_writing_nothing`, `test_a_task_that_admits_no_acceptance_refuses_an_operational_write`, `test_pause_and_operational_together_are_refused_naming_the_flags`, `test_accepted_finding_is_refused_with_pause_or_operational_naming_the_flags`, `test_finding_is_refused_with_pause_or_operational_naming_the_flags`, `test_an_acceptance_over_findings_is_unchanged`.

**Критерий 2 (`--pause`) — выполнен.** `accept_pause_or_operational` (`src/agentmarshal/journal/acceptance.py:138`) пишет через существующий параметр `create_acceptance_record(..., accepted_pause=)` с `findings=None` (`acceptance.py:173-182`), привязка — `accepted_commit` к полному 40-hex id из `_resolve_commit` (`acceptance.py:172`), а имя extension проверяется `read_extension_manifest(project_root, ...)` (`acceptance.py:166`), чей `_validate_name` (`extensions.py:348`) отрабатывает раньше правила записи, так что дрейфа между двумя правилами имени нет. Демонстрируют: первый тест выше (file form, запись `accepted_pause={"extension": "openspec"}`, `schema == 7`, `"findings" not in record`), `test_an_extension_declared_in_the_directory_form_is_accepted` (directory form) и два теста отказа, каждый проверяющий и имя в stderr, и неизменность журнала.

**Критерий 3 (`--operational`) — выполнен.** `operational=True` уходит в тот же вызов, ревью не читается вовсе — единственная проверка со стороны задачи это `load_task_for_record` (`acceptance.py:163`). Демонстрируют `test_an_operational_acceptance_is_written_at_the_resolved_commit` (задача без ревью) и `test_a_pause_acceptance_is_written_where_no_review_stands` (одобренное ревью не мешает).

**Критерий 4 (три формы взаимно исключают друг друга) — выполнен.** `--pause`/`--operational` лежат во второй mutually exclusive группе (`cli.py:214-229`), а `--finding`/`--accepted-finding` отбиваются в `_run_accept` до разрешения placement (`cli.py:708-730`) — отказ называет оба флага и физически не может ничего записать. Форма по findings выбирается отсутствием обоих новых флагов и идёт по прежнему `accept_findings`. Демонстрируют три теста отказа (включая `SystemExit(2)` от argparse) и `test_an_acceptance_over_findings_is_unchanged`, который пинит `findings == ["F-2", "F-1"]`, `schema == 3` и отсутствие новых полей.

**Критерий 5 (отказ не пишет ничего; gate и остальные команды не меняются) — выполнен.** Порядок проверок — флаги, `load_task_for_record`, манифест, `rev-parse`, затем `create_acceptance_record` и только потом `write_record`; каждый тест отказа сравнивает `_snapshot(journal)` до и после. Дифф трогает только парсер и диспетчер `accept` в `cli.py` и `acceptance.py`; `journal/gate.py` не изменён, пинованные ранее выводы gate/`status`/`report` держат тесты из первой половины того же файла.

**advisory `sidecar-placement-untested`** — новое требование спеки нормативно обещает, что commit разрешается (и манифест читается) «in the journal's repository: the repository that holds the journal in either placement, so a sidecar records against the commits its own repository carries» (`openspec/specs/operator-acceptance/spec.md:174-181`), но все новые тесты строят embedded-проект через `_status_repo` (`tests/test_pause_and_operational_acceptance.py:534`), где `project_root == host_root`; подмена `placement.project_root` на `placement.host_root` в `cli.py:741` прошла бы весь новый набор молча. Сиблинг-команда, которая этот паттерн ввела, такой сценарий и тест имеет — `tests/test_record_ext.py:340` «in a sidecar the commit resolves in the journal repository». Формально критерий 1 не нарушен (сценария про sidecar в дельте нет), поэтому находка не блокирующая.

**advisory `resolve-commit-duplicated`** — `_resolve_commit` в `src/agentmarshal/journal/acceptance.py:105` стал четвёртой копией одной и той же функции: `src/agentmarshal/record_ext.py:130` и `src/agentmarshal/record_check.py:137` совпадают с ней вплоть до докстринга и текста сообщения, отличаясь только классом исключения, а `src/agentmarshal/acknowledge.py:139` — ещё и одним словом в сообщении. Один хелпер с фабрикой ошибки убрал бы ~30×4 строк; `design.md` этот повтор осознанно решает («replicated in `acceptance.py` the way `record_ext.py` replicates it»), и общего git-модуля в пакете нет, так что это дом-привычка кодовой базы, а не дефект — отсюда advisory.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "bce1e53e1d518634917e36a95fbe5b6e3e015baa",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["sidecar-placement-untested", "resolve-commit-duplicated"],
  "classes": {
    "sidecar-placement-untested": "test-gap",
    "resolve-commit-duplicated": "style"
  },
  "verification": {
    "executed": [
      {"what": "diff of openspec/specs/operator-acceptance/spec.md lines 167-311 against the delta spec's ADDED block (lines 5-149)", "result": "identical"},
      {"what": "diff of openspec/specs/operator-acceptance/spec.md lines 119-166 against the delta spec's MODIFIED block (lines 153-199)", "result": "identical apart from one trailing blank line"},
      {"what": "ls openspec/changes/", "result": "only 'archive' — openspec/changes/accept-pause-operational/ is gone, so the archive command ran"},
      {"what": "ls openspec/changes/archive/2026-10-24-accept-pause-operational/", "result": "design.md, proposal.md, specs, tasks.md"},
      {"what": "grep -n '^### Requirement:' openspec/specs/operator-acceptance/spec.md", "result": "8 requirements; the three new ones at lines 167, 243, 277"},
      {"what": "grep -rn \"rev-parse --verify\" --include=*.py src", "result": "acceptance.py:116, record_ext.py:141, record_check.py:148, acknowledge.py:151 plus the _run_git call sites in gate.py/review.py/prune.py — four hand-rolled copies of the same helper"},
      {"what": "grep -n sidecar tests/test_record_ext.py", "result": "line 340 test_in_a_sidecar_the_commit_resolves_in_the_journal_repository — the precedent CR-215 does not match"},
      {"what": "grep -rn 'sidecar' tests/test_pause_and_operational_acceptance.py", "result": "no match — every new test runs the embedded _status_repo fixture (line 534), where project_root == host_root"},
      {"what": "grep -rn 'record acceptance over|record an operator acceptance' tests docs templates .agents README.md", "result": "no match — no test or doc pins accept's help text, so the help rewording breaks nothing"},
      {"what": "grep -n 'CR-212|CR-215|Unreleased' CHANGELOG.md", "result": "no match — recent CRs (including CR-212's record-ext) carry no per-CR CHANGELOG or docs entry, so omitting one here follows the repo's current convention and is outside the contract's scope list"}
    ],
    "read": [
      "src/agentmarshal/journal/acceptance.py",
      "src/agentmarshal/cli.py (accept parser 194-229, _run_accept 708-772, _placement 562-580)",
      "src/agentmarshal/journal/extensions.py (_validate_name 348, read_extension_manifest 564)",
      "src/agentmarshal/journal/records.py (_check_acceptance_fields_7 1039, create_acceptance_record 2427)",
      "src/agentmarshal/journal/status.py (load_task_for_record 164)",
      "src/agentmarshal/journal/placement.py (Placement, resolve_placement)",
      "src/agentmarshal/record_ext.py (_resolve_commit 130, _declared_kind 163)",
      "src/agentmarshal/record_check.py (_resolve_commit 137)",
      "src/agentmarshal/acknowledge.py (_resolve_commit 139)",
      "tests/test_pause_and_operational_acceptance.py",
      "openspec/specs/operator-acceptance/spec.md",
      "openspec/changes/archive/2026-10-24-accept-pause-operational/{proposal.md,design.md,tasks.md,specs/operator-acceptance/spec.md}",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decisions 5, 6, 17, 18)",
      "docs/threat-model.md (sections on extensions and the operational lane)",
      "pyproject.toml"
    ],
    "not_run": [
      {"what": "pytest, ruff, mypy, agentmarshal validate", "why": "read-only review in a sandbox that denied executing the interpreter and test runner; relying on the coordinator's statement that the full CI sequence passed on bce1e53e1d518634917e36a95fbe5b6e3e015baa"},
      {"what": "an end-to-end sidecar run of accept --pause", "why": "requires executing the CLI, which this session could not do; the gap is reported as the advisory finding rather than asserted as a defect"}
    ]
  },
  "evidence": {
    "sidecar-placement-untested": "openspec/specs/operator-acceptance/spec.md:174-181 states the resolution happens in the journal's repository 'in either placement'; tests/test_pause_and_operational_acceptance.py:534 (_status_repo) builds an embedded project where project_root == host_root, and grep for 'sidecar' in that file returns nothing, so substituting placement.host_root at src/agentmarshal/cli.py:741 would pass every new test; the sibling command covers it at tests/test_record_ext.py:340",
    "resolve-commit-duplicated": "grep -rn \"rev-parse --verify\" --include=*.py src → src/agentmarshal/journal/acceptance.py:116, src/agentmarshal/record_ext.py:141, src/agentmarshal/record_check.py:148, src/agentmarshal/acknowledge.py:151; acceptance.py:105-135 and record_check.py:137-167 differ only in the raised exception class"
  }
}
AGENTMARSHAL_VERDICT_END
