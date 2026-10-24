## Что я проверил

Прочитал `src/agentmarshal/journal/report.py`, `src/agentmarshal/journal/status_view.py`, `src/agentmarshal/journal/display.py`, `records.create_session_record`, новый `tests/test_unmeasured_session_usage.py`, существующие `tests/test_report.py`, `tests/test_report_cost_checks_findings.py`, `tests/test_report_lead_time.py`, итоговый `openspec/specs/session-activity/spec.md`, архивированный change и ADR-0019/ADR-0022. Выполнить команды в этой песочнице нельзя (`uv`/`python3` отклонены), поэтому результат CI-последовательности я не перепроверял и ни на что не ссылаюсь как на запущенное — беру его из записки координатора.

## Приёмочные критерии

**AC1 — change, delta, сценарии, архив: выполнен.** `openspec/changes/archive/2026-10-24-unmeasured-session-usage/` содержит `proposal.md`, `design.md`, `tasks.md` и delta `specs/session-activity/spec.md` с пятью ADDED-требованиями и двумя MODIFIED — «report --task shows the task's cost per currency» и «report aggregates cost per currency» — полным текстом, заголовок в заголовок с `openspec/specs/session-activity/spec.md:502` и `:548`, со всеми шестью и четырьмя их сценариями соответственно; delta приложена к `openspec/specs/session-activity/spec.md:714-816`. Все 12 ADDED-сценариев названы докстрингами в `tests/test_unmeasured_session_usage.py` (строки 83, 89, 100, 109, 129, 151, 171, 192, 217, 250, 289, 317), все 10 сценариев MODIFIED-требований — докстрингами в `tests/test_report_cost_checks_findings.py:124,150,172,228,245,272,288,325,359,384`. Требования о token-сумме в спеке раньше не было, так что MODIFIED-оговорка критерия применяться было не к чему.

**AC2 — чтение «unmeasured»: выполнен.** Предикат один — `report.py:176-195` (нулевые все три счётчика и отсутствующий `usage`); `status` показывает его через `_render_session_line` (`status_view.py:302-318`, регистрация `:333`) — демонстрирует `test_an_unmeasured_sessions_tokens_show_as_unmeasured`; token-суммы исключают такие сессии в `report.py:400` (строка задачи) и через `sum(task.tokens)` в агрегате — `test_the_task_line_names_the_unmeasured_sessions_it_left_out`, `test_the_summary_names_the_unmeasured_sessions_it_left_out`; cost-суммы и `sessions_without_cost` — `report.py:348-350`, демонстрируют `test_an_unmeasured_sessions_cost_is_left_out_of_the_sums`, `test_every_cost_line_names_the_sessions_left_out`, `test_a_task_holding_only_unmeasured_sessions_prints_no_cost_lines`, `test_the_aggregate_leaves_unmeasured_sessions_out_and_names_them`; `unmeasured=<n>` печатается последним полем везде, где печатается сумма (`report.py:695,703,705-707,738-739,768-769`). Сессия с `usage` или с любым ненулевым счётчиком читается как раньше — `test_a_session_with_a_usage_block_reads_as_today`, `test_a_session_with_a_non_zero_token_reads_as_today`, `test_a_measured_sessions_line_is_unchanged`.

**AC3 — ничего не пишется, вывод без таких сессий прежний: выполнен.** Диффа в `records.py`, в писателях и правилах записи нет вовсе; поле добавляется только при непустом счётчике (`report.py:695,738,768`). Демонстрируют `test_with_no_unmeasured_session_nothing_changes` и существующие пины `tests/test_report_cost_checks_findings.py:498` («today's report output is the new output's prefix») и `tests/test_report.py:255-265` — они строят сессии с ненулевыми токенами (10/5/0, `--input-tokens 2`), поэтому остались неизменными без правок. Оговорка по честности: строку записи сессии в `status` до этой задачи не пинговал ни один существующий тест (грепом по `tests/` совпадений на `- <id> session <created_at>` нет), так что статусную половину этого критерия демонстрирует новый `test_a_measured_sessions_line_is_unchanged`, а не старый тест.

**AC4 — экранирование, прочие команды: выполнен.** Новые поля — целые числа и литерал `tokens=unmeasured`, значений из записей они не несут; строка сессии целиком проходит `escape_for_display` на диспетчере (`status_view.py:835`), а посимвольное экранирование (`display.py:40-43`) делает это тождественным прежнему по-полю; валюта по-прежнему экранируется в `report.py:698`. `build_report`/`format_report` читает только `_run_report` (`cli.py:1356-1376`), `_is_unmeasured` импортирует только `status_view.py:24`, так что других команд изменение не касается. Полную CI-последовательность я не запускал.

## Замечания (все не блокирующие)

**CR-229-A1** — в `openspec/specs/session-activity/spec.md` остались два прежних требования, которые теперь спеке противоречат: «the new lines leave today's output first and unchanged» (`:485-489`) и «the cost and check lines leave today's output first and unchanged» (`:619-623`) безусловно обещают, что каждая строка, которую `report` и `report --task` печатают сегодня, печатается без изменений, — а при наличии unmeasured-сессии строка задачи (`report.py:738-739`), строка `Summary` (`:768-769`) и каждая строка `Cost` (`:695,703,705-707`) получают новое поле. Новое ADDED-требование «a journal holding no unmeasured session prints what it prints today» (`:808`) сужает обещание до журналов без таких сессий, но старые два под это не были переведены в MODIFIED. Критерий AC1 этого не требовал (он называет MODIFIED только для требований о суммировании токенов), поэтому замечание советующее, но спека сейчас сама себе противоречит.

**CR-229-A2** — три сценария требования «an unmeasured session reads as unmeasured» утверждают, как запись читается «в `status` и `report`», а демонстрирующие их тесты (`tests/test_unmeasured_session_usage.py:82-104`) проверяют только сам предикат `_is_unmeasured` и ни одной из двух команд не вызывают. По букве AC1 («сценарий демонстрируется тестом, чей докстринг его называет») это выполнено, и уровень представлений покрыт другими сценариями, но демонстрация именно этих трёх тонкая.

**CR-229-A3** — поля `TaskReport.sessions` и `JournalReport.sessions` (`report.py:105,132`, оба класса экспортируются из `agentmarshal.journal`) теперь означают число *измеренных* сессий, а не всех; имя и докстринги классов об этом не говорят — сказано только в докстринге `_cost_sums` (`:322-325`). Внутри дерева потребитель один (`_cost_lines`), так что дефекта поведения нет, но читателю структуры смысл поля больше не виден.

Блокирующих находок нет: предикат, суммы, строки представлений и экранирование согласованы со спекой, ADR-0019 решение 4 (валюты не смешиваются, суммы — Decimal) и ADR-0022 (запись не меняется, «не проверено/не измерено» говорится, а не умалчивается) не нарушены.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "5cf5f228d8a5aaf50bf9e99a087ae4c0de3be6ae",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["CR-229-A1", "CR-229-A2", "CR-229-A3"],
  "classes": {
    "CR-229-A1": "contract-mismatch",
    "CR-229-A2": "test-gap",
    "CR-229-A3": "style"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/display.py",
      "src/agentmarshal/journal/records.py (create_session_record)",
      "src/agentmarshal/journal/open_task.py (_contract_content)",
      "src/agentmarshal/cli.py (_run_report)",
      "tests/test_unmeasured_session_usage.py",
      "tests/test_report.py",
      "tests/test_report_cost_checks_findings.py",
      "tests/test_report_lead_time.py",
      "openspec/specs/session-activity/spec.md",
      "openspec/changes/archive/2026-10-24-unmeasured-session-usage/ (proposal.md, design.md, tasks.md, specs/session-activity/spec.md)",
      "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md"
    ],
    "executed": [
      {"what": "grep -rn \"build_report|format_report|TaskReport|JournalReport|_cost_sums|_is_unmeasured\" over src/", "result": "only cli.py:1367-1368 (_run_report), journal/__init__.py exports and status_view.py:24,316 — no other command reads the changed API"},
      {"what": "grep -rn \"0, 0, 0\" and create_session_record call sites over tests/", "result": "every existing report/status test builds sessions with non-zero tokens (10/5/0, 1/2/3, 4/5/6, --input-tokens 2), so none becomes unmeasured"},
      {"what": "grep -rn for an existing assertion on the status session record line over tests/", "result": "no match outside tests/test_unmeasured_session_usage.py"},
      {"what": "grep -c '#### Scenario:' on the archived delta vs grep of Scenario docstrings in the new test file", "result": "22 delta scenarios = 12 ADDED (all 12 named in tests/test_unmeasured_session_usage.py) + 10 in the two MODIFIED requirements (all 10 named in tests/test_report_cost_checks_findings.py)"},
      {"what": "grep -rn \"tokens=\" over docs/, README.md, templates/", "result": "only docs/sidecar.md:335, an example line with measured tokens — unaffected"}
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "this read-only review session cannot execute commands (uv and python3 invocations were refused by the sandbox); the coordinator states the sequence passed on this commit"}
    ]
  },
  "evidence": {
    "CR-229-A1": "openspec/specs/session-activity/spec.md:485-489 and :619-623 ('Every line `report` and `report --task` print today SHALL print first and unchanged') versus src/agentmarshal/journal/report.py:738-739 (task line gains '\\tunmeasured=<n>'), :768-769 (Summary line) and :695,703,705-707 (every Cost line); the carve-out added instead is spec.md:808-816",
    "CR-229-A2": "tests/test_unmeasured_session_usage.py:82-104 — the three tests assert only `_is_unmeasured(...)`, while the scenarios at openspec/specs/session-activity/spec.md:727-740 state the read 'in `status` and `report`'",
    "CR-229-A3": "src/agentmarshal/journal/report.py:105 and :132 declare `sessions: int = 0` with no note; the narrowed meaning is stated only in the `_cost_sums` docstring at :322-325, and both dataclasses are exported by src/agentmarshal/journal/__init__.py:19-22"
  }
}
AGENTMARSHAL_VERDICT_END
