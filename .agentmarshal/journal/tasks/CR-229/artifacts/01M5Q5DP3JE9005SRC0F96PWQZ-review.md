Разобрал contract, diff, итоговый spec и код в рабочем дереве. Ниже — прозаическая часть: сначала по каждому acceptance criterion, потом два advisory finding'а.

**AC1 — change, delta, сценарии, archive: выполнен.** Change лежит целиком в `openspec/changes/archive/2026-10-25-unmeasured-session-usage/` (`proposal.md`, `design.md`, `tasks.md`, `specs/session-activity/spec.md`), живого каталога `openspec/changes/unmeasured-session-usage/` больше нет — только `archive/`, и delta приземлилась в `openspec/specs/session-activity/spec.md:762-884`, что соответствует прогону `openspec archive`. Все 13 ADDED-сценариев и 3 новых сценария в MODIFIED-требованиях демонстрируются тестами, чьи docstring'и называют их дословно, в `tests/test_unmeasured_session_usage.py`; ранее существовавшие сценарии, переписанные полным текстом в MODIFIED-требованиях, сохраняют свои тесты (`tests/test_report_lead_time.py:405`, `tests/test_report_cost_checks_findings.py:245,359,501`, `tests/test_status_candidate_session.py:298`). Условие «MODIFIED там, где существующее требование описывает суммирование token-итогов» не срабатывает: `grep -rn "token" openspec/specs/` даёт совпадения только в `session-activity` (и два посторонних в `reviewer-adapter`), и ни одно прежнее требование не описывало, как складываются `tokens=` — поэтому MODIFIED ограничен требованиями про cost-строки, префикс вывода и session-строку, у каждого полный текст, заголовок байт-в-байт и все сценарии.

**AC2 — чтение unmeasured: выполнен.** Один предикат `_is_unmeasured` (`src/agentmarshal/journal/report.py:192-212`) — `record_type == "session"`, нет ключа `usage`, все значения `tokens` нулевые; `status_view.py:302-318` импортирует именно его, второго определения нет. `status` помечает строку (`test_zero_tokens_and_no_usage_is_unmeasured`, `test_an_unmeasured_sessions_tokens_show_as_unmeasured`), `report` исключает сессию из token-суммы задачи (`report.py:421-424`) и из summary (`report.py:511`, сумма по `task.tokens`) и печатает `unmeasured=<n>` последним полем (`test_the_task_line_names_the_unmeasured_sessions_it_left_out`, `test_the_summary_names_the_unmeasured_sessions_it_left_out`). ADR-0019 decision 4 соблюдён: записанный `cost` суммируется как у измеренной сессии, из cost-сумм и из `sessions_without_cost` выпадает только unmeasured-сессия без `cost` (`report.py:366-372`) — `test_a_lone_unmeasured_session_with_a_cost_prints_its_cost_lines_as_today`, `test_an_unmeasured_sessions_recorded_cost_joins_the_per_currency_sums`, `test_an_unmeasured_session_carrying_no_cost_is_left_out_of_the_cost_sums_and_named`, `test_a_task_holding_only_unmeasured_sessions_carrying_no_cost_prints_no_cost_lines`, `test_the_aggregate_sums_a_recorded_cost_and_names_the_sessions_left_out`. Сессия с `usage` или с любым ненулевым счётчиком читается как раньше: `test_a_session_with_a_usage_block_reads_as_today`, `test_a_session_with_a_non_zero_token_reads_as_today`, `test_a_measured_sessions_line_is_unchanged`.

**AC3 — ничего не пишется и не перезаписывается: выполнен.** Diff не трогает `records.py`, `session.py`, `backfill.py`, `capture.py` и ни одно правило записи; изменения — только два reader-модуля и tests. Журнал без unmeasured-сессий печатает то же самое: `test_with_no_unmeasured_session_nothing_changes`, а существующие status/report-тесты остались без правок и проходят — их сессии измерены (`tests/test_report_cost_checks_findings.py:72` пишет 10/5/0, `tests/test_status_view.py:191,236` — 1/2/3 и 4/5/6), единственная нулевая сессия в старых тестах (`tests/test_journal.py:694`) проверяет валидацию записи, а не вывод.

**AC4 — escaping и границы: выполнен.** Новый session-renderer возвращает сырую строку, а `status_view.py:835` пропускает её через `escape_for_display` целиком, ровно как у остальных renderer'ов, так что измеренная строка байт-в-байт равна прежнему generic-fallback'у (`status_view.py:828-833`); новые поля в `report` — целые числа, а `escape_for_display` на `task_id`, `usage` и `currency` сохранён (`report.py:756-762`, `726`). Других команд изменение не касается: `build_report`/`format_report` вызываются только из `cli.py:1376`, а `_RECORD_RENDERERS` читается только в `status_view.py:827`.

**ADV-IMPORTED-ZERO-TOKENS-READ-AS-UNMEASURED** — предикат `_is_unmeasured` (`src/agentmarshal/journal/report.py:192-212`) ошибочно читает как unmeasured backfill-записанную сессию: `session_record_from_stat` (`src/agentmarshal/journal/backfill.py:150-171`) не пишет блок `usage` вообще, поэтому импортированный host-stat, у которого `input_tokens`, `output_tokens` и оба cache-поля равны нулю (cache-поля даже не входят в `_REQUIRED_STAT_FIELDS`, `backfill.py:52-63`, и дефолтятся в 0 через `_require_int`), будет показан как `tokens=unmeasured` и выкинут из token-сумм, хотя журнал держит доказательство измерения — `source: imported` и artifact-ref `host-stat:<ref>`. Это же делает неточным утверждение design.md «the only trace is the missing `usage` block a measured session carries». Advisory, а не blocking: предикат реализован ровно так, как его задаёт AC2 контракта, так что это ограничение самого контракта, а не отклонение от него.

**ADV-SPEC-COST-UNMEASURED-SELF-CONTRADICTION** — в заархивированном нормативном тексте требование «an unmeasured session counts in no cost sum or measured-session count» противоречит себе: `openspec/specs/session-activity/spec.md:829-831` утверждает про любую unmeasured-сессию «no `Cost` line's `unmeasured=<n>` counts it», а строки 834-837 того же абзаца требуют, чтобы unmeasured-сессии без `cost` именно этим `unmeasured=<n>` и назывались — первое предложение верно только для unmeasured-сессии, несущей `cost` (сценарий на строках 850-855). Поведение кода однозначно и следует сценариям, расхождение только в прозе требования, поэтому advisory.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "cb1fa8eac6dedc67a798c96c2c261916c9308309",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-IMPORTED-ZERO-TOKENS-READ-AS-UNMEASURED",
    "ADV-SPEC-COST-UNMEASURED-SELF-CONTRADICTION"
  ],
  "classes": {
    "ADV-IMPORTED-ZERO-TOKENS-READ-AS-UNMEASURED": "correctness",
    "ADV-SPEC-COST-UNMEASURED-SELF-CONTRADICTION": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"token\" openspec/specs/ (excluding session-activity)", "result": "only reviewer-adapter/spec.md:36,40 — no pre-existing requirement states how token totals are summed, so the contract's MODIFIED clause does not trigger there"},
      {"what": "grep -n \"tokens\" src/agentmarshal/journal/report.py", "result": "two token sums only — report.py:421-424 (per task, now filtered by `not _is_unmeasured`) and report.py:511 (`sum(task.tokens for task in tasks)`)"},
      {"what": "grep -rn \"\\.sessions\\b|sessions_without_cost|\\.tokens\\b|build_report|format_report\" src/ --include=*.py", "result": "only cli.py:1376-1378 and journal/__init__.py re-exports consume the report — no other command reads the changed fields"},
      {"what": "grep -rn \"_RECORD_RENDERERS\" src/ tests/", "result": "single consumer at status_view.py:827; adding the \"session\" key affects nothing else"},
      {"what": "grep -rn \"0, 0, 0\" tests/ and inspection of the hits", "result": "only tests/test_journal.py:694 (record-validation, no view output) and the new test file — no existing status/report test asserts output for a zero-token no-usage session"},
      {"what": "grep -rn \"create_session_record(\" tests/test_report.py tests/test_report_cost_checks_findings.py tests/test_status_view.py", "result": "helpers write 10/5/0, 1/2/3, 4/5/6 — measured, so existing expectations are unaffected"},
      {"what": "grep -rn docstring scenario names in tests/ for the five restated MODIFIED scenarios", "result": "found at tests/test_status_candidate_session.py:298, tests/test_report_lead_time.py:405, tests/test_report_cost_checks_findings.py:245,359,501"},
      {"what": "ls openspec/changes/ and openspec/changes/archive/", "result": "only `archive/`, holding 2026-10-25-unmeasured-session-usage — the live change directory is gone and the delta is merged into openspec/specs/session-activity/spec.md"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py (dataclasses, _is_unmeasured, _cost_sums, _task_report, build_report, _cost_lines, format_report)",
      "src/agentmarshal/journal/status_view.py (renderer table, _render_session_line, record print loop at 824-835, _implementer_session_line)",
      "src/agentmarshal/journal/records.py:2272-2346 (create_session_record — `usage` omitted when no flags, `tokens` always a three-int dict)",
      "src/agentmarshal/journal/backfill.py:40-195 (session_record_from_stat — no `usage` block, source imported, host-stat artifact)",
      "src/agentmarshal/cli.py:1365-1385, 407-409",
      "openspec/specs/session-activity/spec.md (requirement list and the new/modified requirements)",
      "openspec/changes/archive/2026-10-25-unmeasured-session-usage/{proposal.md,design.md,tasks.md,specs/session-activity/spec.md}",
      "docs/adr/ADR-0019-accounting-time-quota-resets-money.md (decision 4)",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "tests/test_unmeasured_session_usage.py",
      "tests/test_report_cost_checks_findings.py, tests/test_status_view.py, tests/test_journal.py (session helpers)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "no uv in this read-only review environment; the coordinator states the full sequence passed on the reviewed commit"},
      {"what": "openspec archive / openspec validate", "why": "no npx/node available; archive was verified by its result instead — the change directory moved under archive/ and the delta is present in openspec/specs/session-activity/spec.md"}
    ]
  },
  "evidence": {
    "ADV-IMPORTED-ZERO-TOKENS-READ-AS-UNMEASURED": "src/agentmarshal/journal/backfill.py:150-171 builds a session record with `source: SOURCE_IMPORTED` and a `host-stat:` artifact ref but no `usage` key; `cache_read_input_tokens`/`cache_creation_input_tokens` are absent from _REQUIRED_STAT_FIELDS (backfill.py:52-63) and default to 0 in `_require_int` (backfill.py:69-74); src/agentmarshal/journal/report.py:205-212 therefore returns True for such an all-zero imported record, and openspec/changes/archive/2026-10-25-unmeasured-session-usage/design.md:5-7 claims the missing `usage` block is 'the only trace'",
    "ADV-SPEC-COST-UNMEASURED-SELF-CONTRADICTION": "openspec/specs/session-activity/spec.md:829-831 ('An unmeasured session SHALL be no counted member of the `Cost` sums' scope: it is no `sessions_without_cost` session and no `Cost` line's `unmeasured=<n>` counts it.') against spec.md:834-837 ('Only an unmeasured session carrying no `cost` is left out of these sums — wherever `Cost` lines print, such sessions SHALL be named by `unmeasured=<n>` …'); the narrower reading is the one the scenario at spec.md:850-855 fixes, and the one src/agentmarshal/journal/report.py:366-372 and 716-735 implement"
  }
}
AGENTMARSHAL_VERDICT_END
