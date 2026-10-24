Я прочитал оба изменённых модуля, `status_view.py` (источник «тех же терминов»), ADR-0007, полный текст `openspec/specs/operator-acceptance/spec.md`, архивную дельту и все затронутые тесты. Запустить CI не смог — в снапшоте нет ни `uv`, ни `.venv`, а выполнение python в этой сессии было отклонено; полную последовательность проверок беру из записки координатора и помечаю как непроверенную мной.

**По критериям приёмки.**

AC1 выполнен на обеих поверхностях. Gate строит метку в `src/agentmarshal/journal/gate.py:1832-1840` через общую сверку `report._accepting_party_is_declared_writer` (`src/agentmarshal/journal/report.py:459-475`), импортированную на уровне модуля (`gate.py:64`); сверка воспроизводит `status_view._is_self_accepted` (`status_view.py:71-84`). Демонстрируют: `tests/test_self_acceptance_on_every_surface.py::test_the_gates_acceptance_line_marks_a_self_acceptance` (параметризован по e-mail автора, его смешанному регистру и по имени автора — `_WRITER` в `tests/test_gate.py:42` это `Worker <worker@test.invalid>`) и `::test_the_gates_acceptance_line_marks_a_committer_self_acceptance` (половина committer'а через `_implement_distinct_committer`). Строка `report` — `report.py:884-891` плюс поле `TaskReport.self_accepted` (`report.py:145`) и `_self_accepted` (`report.py:478-502`); демонстрируют `::test_reports_task_line_marks_a_self_acceptance` и `::test_reports_task_line_marks_a_committer_self_acceptance`. Непомеченные ветки закрыты `::test_an_acceptance_by_another_party_prints_unmarked` и `::test_reports_task_line_prints_unmarked_when_the_check_cannot_run` (отсутствующий commit и вовсе удалённый `project.json`). Репозиторий, в котором читаются writers, тот же, что у `status`: `report._writers_repository` берёт `resolve_placement(...).host_root` (`report.py:442-456`), а `status` передаёт `placement.host_root` в `print_task_detail` (`src/agentmarshal/cli.py:1525`).

AC2 выполнен: решение выводится из review и acceptance, привязанных к собственному binding'у записи `completed` (`report.py:518-574`). Шесть сценариев демонстрируют `::test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved`, `::test_a_commit_completed_over_findings_reports_accepted_over_findings`, `::test_a_finding_completed_over_findings_reports_accepted_over_findings`, `::test_a_commit_approved_after_its_own_acceptance_reports_approved`, `::test_an_acceptance_bound_to_another_commit_leaves_no_decision`, `::test_a_task_with_no_completed_record_keeps_todays_decision_rule`. Существующий пин `tests/test_report.py:435-438` остаётся зелёным по построению: CR-001 без `completed` идёт по старому правилу, CR-002 одобрен на своём commit'е. Индексация `completed["completed_commit"]` безопасна — `_validate_binding` (`records.py:1824-1849`) требует ровно один binding на чтении, и старый код индексировал так же.

AC3 выполнен. MODIFIED несёт то единственное требование, чью byte-for-byte оговорку метка задевает («Readers keep acceptance over findings to the acceptances that carry findings»), с заголовком и всеми шестью сценариями; я прогрепал остальные 22 capability-спеки — ни одна не содержит оговорки о выводе acceptance. ADDED несёт два новых требования, оба лежат в `openspec/specs/operator-acceptance/spec.md:316-397`, change переехал в `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/`. У каждого из 16 сценариев есть тест, чей docstring его называет.

AC4 выполнен в той части, что я могу проверить чтением: метка — константа, приклеенная после уже экранированных полей (`report.py:891`), `accepted_by` в `report` не печатается вообще, а `gate.say` экранирует готовую строку (`gate.py:142-147`). Пин экранирования в `tests/test_display.py:254` сохранён. Quickstart-транскрипт остаётся зелёным, потому что принимающая сторона там `operator@example.com`, а коммиты пишутся как `dev@example.com` (`tests/test_quickstart.py:73-76`). Отдельно отмечу без вынесения в findings: два существующих теста в `tests/test_pause_and_operational_acceptance.py` всё же отредактированы (принимающая сторона сдвинута с писателя коммита на `op`), так что буквально «existing status tests unchanged» не держится — но оба журнала были self-acceptance-журналами, то есть вне защищённого AC4 множества, а снятые пины status выживают в `tests/test_status_view.py:259-287`.

Блокирующих дефектов не нашёл. Четыре advisory.

ADV-gate-mark-wording — `gate.py:1833-1834` печатает квалификацию `(self-accepted: accepting party is a declared writer of the candidate)`, тогда как `status_view.py:809` печатает `(self-accepted: accepting party is a declared author or committer)`: AC1 просит «in the terms status uses», а получилось две разные формулировки одного понятия на двух поверхностях; вдобавок AC1 называет сверяемые identities как «the identities the gate's independence check already reads» — а это только e-mail'ы (`_range_emails`, `gate.py:505-507`), тогда как реализация завела новый, более широкий набор с именами (`_range_writer_identities`, `gate.py:509-527`). Расхождение в правильную сторону (без имён gate помечал бы меньше случаев, чем status) и задокументировано в design.md, но как отступление от текста контракта его стоило назвать.

ADV-report-mark-separator — и архивная дельта, и осевший спек (`openspec/specs/operator-acceptance/spec.md:321`) пишут метку строки `report` как `` ` self-accepted` `` с ведущим пробелом, а `report.py:891` выдаёт `"\tself-accepted"`; для спека, который сам себя объявляет byte-for-byte контрактом поверхности, это неточность — реализация по букве спека дала бы другую строку (и неверную: пробел попал бы внутрь значения поля `decision=`).

ADV-gate-extra-git-log — `gate.py:1824-1829` вызывает `_range_writer_identities` на каждом запуске gate, где есть review, то есть второй полный `git log` по `merge-base..candidate` рядом с `_range_emails`, хотя результат читается только в ветке `valid_acceptance is not None` (`gate.py:1835`); в подавляющем большинстве прогонов acceptance нет и набор не читается ни разу.

ADV-stage-pause-unmarked — заголовок нового требования «every surface marks a self-acceptance» переобещает: `src/agentmarshal/stages.py:1484-1487` печатает `accepted_by` pause-acceptance в строке `stage run` без всякой метки, хотя `status` pause-acceptance помечает (спек, строки 147-157). Путь вне scope контракта, так что это отступление, которое надо назвать, а не править здесь.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "10197420e17fb52a6ced52176b5256a1a379c940",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-gate-mark-wording",
    "ADV-report-mark-separator",
    "ADV-gate-extra-git-log",
    "ADV-stage-pause-unmarked"
  ],
  "classes": {
    "ADV-gate-mark-wording": "contract-mismatch",
    "ADV-report-mark-separator": "claim-accuracy",
    "ADV-gate-extra-git-log": "efficiency",
    "ADV-stage-pause-unmarked": "claim-accuracy"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/gate.py (lines 290-335, 490-540, 1141-1200, 1740-1960)",
      "src/agentmarshal/journal/status_view.py (lines 13-200, 772-840)",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/records.py (_project_root_for, _validate_binding, create_completed_record)",
      "src/agentmarshal/cli.py (lines 1495-1535)",
      "src/agentmarshal/stages.py (lines 1465-1515)",
      "openspec/specs/operator-acceptance/spec.md (full)",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/ (proposal.md, design.md, tasks.md, specs/operator-acceptance/spec.md)",
      "docs/adr/ADR-0007-operator-acceptance.md (decisions 4, 5, 6)",
      "docs/threat-model.md (lines 95-112)",
      "docs/quickstart.md (lines 430-495)",
      "tests/test_self_acceptance_on_every_surface.py",
      "tests/test_pause_and_operational_acceptance.py (lines 530-760)",
      "tests/test_gate.py (lines 42-300, 1540-1570, 3605-3640)",
      "tests/test_report.py (lines 400-440)",
      "tests/test_status_view.py (self-acceptance pins)",
      "tests/test_quickstart.py (lines 49-185)",
      "tests/test_display.py (lines 240-260)"
    ],
    "executed": [
      {
        "what": "grep -rn 'accepted over findings|decision=accepted-over-findings|decision=approved' openspec/specs/ excluding operator-acceptance",
        "result": "no output - no other capability spec carries an acceptance-output clause, so the MODIFIED delta's single requirement is the complete set AC3 asks for"
      },
      {
        "what": "grep -rn '_task_report|\\.decision\\b|self_accepted' src/ tests/ --include=*.py",
        "result": "TaskReport.decision is consumed only by format_report (report.py:882-891); _task_report has exactly two callers, build_report (report.py:609) and tests/test_display.py:254 - no other surface inherits the changed semantics"
      },
      {
        "what": "grep -rn 'accepted_by' src/agentmarshal/ excluding report.py, gate.py, status_view.py, records.py",
        "result": "only src/agentmarshal/stages.py:1486 - the stage-run pause line, which prints the party with no self-acceptance mark (basis of ADV-stage-pause-unmarked)"
      },
      {
        "what": "grep -rn 'accepted-over-findings' tests/ docs/ templates/ excluding the new test file",
        "result": "tests/test_report.py:437 (open task, no completed record -> today's rule) and tests/test_pause_and_operational_acceptance.py:707 - both still satisfied by the new derivation"
      },
      {
        "what": "grep -n 'user.email|GIT_AUTHOR|GIT_COMMITTER' tests/test_quickstart.py and grep -n '--by' docs/quickstart.md",
        "result": "writers are 'Dev Example <dev@example.com>' while the accepting party is 'operator@example.com' - the quickstart gate transcript stays unmarked, so its pin at tests/test_quickstart.py:163-168 is unaffected"
      },
      {
        "what": "grep -n '^from agentmarshal' on report.py's module-level dependencies (status.py, placement.py, display.py, records.py)",
        "result": "none imports gate or status_view, so gate.py:64's new module-level import of report introduces no cycle; _declared_commit_writers stays a function-local import because status_view imports report"
      },
      {
        "what": "grep -rn 'declared author or committer' tests/",
        "result": "tests/test_status_view.py:262 and :283 still pin status's self-accepted summary and record-line marker, so the pins dropped from test_pause_and_operational_acceptance.py lose no coverage"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "no uv and no .venv in the review snapshot, and python execution was declined in this session; the full sequence's result is taken from the coordinator's note on this commit and is not something I verified"
      }
    ]
  },
  "evidence": {
    "ADV-gate-mark-wording": "src/agentmarshal/journal/gate.py:1833 emits ' (self-accepted: accepting party is a declared writer of the candidate)' while src/agentmarshal/journal/status_view.py:809 emits ' (self-accepted: accepting party is a declared author or committer)'; the identity set is the new src/agentmarshal/journal/gate.py:509-527 ('log --format=%an%n%ae%n%cn%n%ce'), not the independence check's emails-only src/agentmarshal/journal/gate.py:505-507 ('log --format=%ae%n%ce') that the contract's AC1 parenthetical names",
    "ADV-report-mark-separator": "openspec/specs/operator-acceptance/spec.md:321 ('`report`'s task line SHALL carry ` self-accepted` after the decision field') and :338 vs src/agentmarshal/journal/report.py:891 ('line += \"\\tself-accepted\"'); the test pins the tab form (tests/test_self_acceptance_on_every_surface.py:263-265)",
    "ADV-gate-extra-git-log": "src/agentmarshal/journal/gate.py:1824-1829 computes writer_identities under 'if latest is not None', beside writer_emails at :1816-1823, but the value is read only at :1835 inside the 'valid_acceptance is not None' branch - two full 'git log' invocations over merge-base..candidate where runs without an acceptance need one",
    "ADV-stage-pause-unmarked": "src/agentmarshal/stages.py:1484-1487 prints 'pause accepted by <accepted_by> (<reason>)' with no self-acceptance mark, while openspec/specs/operator-acceptance/spec.md:147-157 has status mark a pause acceptance and :316 heads the new requirement 'every surface marks a self-acceptance'; stages.py is outside the contract's scope"
  }
}
AGENTMARSHAL_VERDICT_END
