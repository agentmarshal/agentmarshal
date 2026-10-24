Проверил диф по файлам в снапшоте. Ниже — проза по находкам и по каждому acceptance criterion.

**Находки (обе advisory, не блокирующие)**

- **ADV-1 — записанная стоимость unmeasured-сессии исчезает из `report` целиком, не только из суммы.** `_cost_sums` в `src/agentmarshal/journal/report.py:357-359` пропускает такую сессию до чтения `cost`, а `_cost_lines` (`report.py:713`) печатает блок только при `sessions` > 0 — значит задача, у которой все сессии unmeasured, не печатает ни одной строки `Cost`, хотя журнал держит сумму: ровно это и закрепляет новый тест `tests/test_unmeasured_session_usage.py:246-268` (записана `1.00 USD`, в выводе нет ни одной `Cost`-строки). Сценарий достижим прямо из CLI: токен-флаги по умолчанию нулевые (`src/agentmarshal/cli.py:407-409`), флаги `--cost-amount/--cost-currency/--cost-source` независимы (`cli.py:441-453`), и ни одно record rule не связывает `cost` с токенами или `usage` (`src/agentmarshal/journal/records.py:887-930`) — а ADR-0019 решение 6 как раз описывает запись стоимости после завершения задачи через `record-session --if-missing`, т.е. сессию, у которой токенов может не быть. Это напряжение с ADR-0019 решением 4 («сумма в одной валюте — это цифра, которую журнал держит»): читатель видит `unmeasured=<n>` и ни слова о потраченных деньгах. Не блокирую, потому что исключение из cost-сумм прямо предписано контрактом (критерий 2) и зафиксировано в delta spec («an unmeasured session's cost is left out of the sums»); решение принадлежит автору контракта, а не исполнителю.
- **ADV-2 — на стороне `status` осталось не согласованное требование.** Изменение правит строку record-а в `status` для unmeasured-сессии, но требование `openspec/specs/session-activity/spec.md:730-734` («the session line leaves today's output unchanged…: Every line `agentmarshal status <task>` prints today SHALL print unchanged») осталось без MODIFIED, тогда как два его аналога на стороне `report` автор как раз и поправил ради той же оговорки (`spec.md:485-498` и `spec.md:638-652`). По собственному стандарту дифа этот пункт тоже следовало переписать: буквально он теперь запрещает то, что предписывает новое требование `spec.md:775-792`. Тот же буквальный конфликт есть в `openspec/specs/contract-governance/spec.md:941-947` («Nothing else `status` prints SHALL change — the record lines…»), но эта capability вне scope контракта, так что править её без departure было нельзя.

**Acceptance criteria**

1. **Change, delta, архив** — выполнено: `proposal.md`, `design.md` и delta на `session-activity` с ADDED и MODIFIED (заголовки MODIFIED совпадают байт в байт с теми, что в `openspec/specs/session-activity/spec.md:485`, `:515`, `:563`, `:638`; текст требований приведён целиком со всеми сценариями), change лежит под `openspec/changes/archive/2026-10-24-unmeasured-session-usage/`, в `openspec/changes/` не осталось ничего (проверил `ls`), делта влита в `openspec/specs/session-activity/spec.md:747-852` без дублей (`grep "^### Requirement"` — по одному вхождению). Каждый новый сценарий демонстрирует тест, чей docstring его называет: `test_zero_tokens_and_no_usage_is_unmeasured`, `test_a_session_with_a_usage_block_reads_as_today`, `test_a_session_with_a_non_zero_token_reads_as_today`, `test_an_unmeasured_sessions_tokens_show_as_unmeasured`, `test_a_measured_sessions_line_is_unchanged`, `test_the_task_line_names_the_unmeasured_sessions_it_left_out`, `test_the_summary_names_the_unmeasured_sessions_it_left_out`, `test_a_task_holding_only_unmeasured_sessions_prints_no_cost_lines`, `test_an_unmeasured_sessions_cost_is_left_out_of_the_sums`, `test_every_cost_line_names_the_sessions_left_out`, `test_the_aggregate_leaves_unmeasured_sessions_out_and_names_them`, `test_the_unmeasured_field_joins_a_sum_line_and_the_new_lines_still_follow`, `test_unmeasured_field_joins_sum_line_and_cost_check_lines_follow`, `test_with_no_unmeasured_session_nothing_changes`; переформулированные сценарии MODIFIED-требований остаются за прежними тестами (`tests/test_report_cost_checks_findings.py:228`, `:245`, `:501`, `:543`, `tests/test_report_lead_time.py:405`), и они по-прежнему их демонстрируют, потому что их хелпер `_session` пишет токены `10/5/0` (`tests/test_report_cost_checks_findings.py:70-81`), то есть measured-сессии.
2. **Чтение unmeasured** — выполнено: один предикат `_is_unmeasured` (`report.py:185-204`), `status` печатает ` tokens=unmeasured` через новый renderer (`status_view.py:302-333`), токен-суммы исключают такие сессии (`report.py:406-410`), cost-суммы и счётчики — тоже (`report.py:354-359`), а `unmeasured=<n>` идёт последним полем на строке задачи (`report.py:747-748`), на `Summary` (`report.py:777-778`) и на каждой `Cost`-строке (`report.py:704-716`); сессия с `usage` или любым ненулевым счётчиком читается как раньше. Демонстрируют `test_zero_tokens_and_no_usage_is_unmeasured`, `test_a_session_with_a_usage_block_reads_as_today`, `test_a_session_with_a_non_zero_token_reads_as_today`, `test_every_cost_line_names_the_sessions_left_out`.
3. **Ничего не пишется и правила записи не меняются** — выполнено: `records.py` и писатели дифом не затронуты (в дифе только `report.py`, `status_view.py`, тесты и openspec), предикат — чистое чтение; существующие status- и report-тесты не правились ни в одной строке, плюс `test_with_no_unmeasured_session_nothing_changes` показывает, что без unmeasured-сессии слова `unmeasured` в выводе нет.
4. **Escaping, прочие команды, CI** — выполнено: новая строка `status` escape-ится диспетчером, который оборачивает весь результат renderer-а (`status_view.py:835`, прокомментировано на `status_view.py:40-45`), новое поле `report` — производное целое; единственные потребители `build_report`/`format_report` — `report` в `cli.py:1376-1379`, а `_is_unmeasured` импортируется только в `status_view.py:24`, так что другие команды не меняются (проверил `grep` по `src/`). Прогон CI-последовательности сам не делал — sandbox отказал в запуске `uv run pytest`; опираюсь на факт координатора, что полная последовательность прошла на `9de3f9fb7e5a664ffc13aaab7b5009bed3095923`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9de3f9fb7e5a664ffc13aaab7b5009bed3095923",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1", "ADV-2"],
  "classes": {
    "ADV-1": "correctness",
    "ADV-2": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn 'build_report|format_report|_cost_sums|_is_unmeasured' src/ (all consumers of the report builders)", "result": "only cli.py:1376-1379 and status_view.py:24,316 — no other command reads the predicate or the sums"},
      {"what": "grep -n 'tokens' over src/agentmarshal/journal/*.py and cli.py outside report.py/records.py", "result": "no other surface prints a token sum; only status_view.py:307-317 (the new mark) and the record-session flags"},
      {"what": "grep -n '^### Requirement' openspec/specs/session-activity/spec.md", "result": "29 requirements, the four ADDED ones appended once at :747-852, no duplicate of a MODIFIED heading"},
      {"what": "ls openspec/changes/ and ls openspec/changes/archive", "result": "only archive/ remains; 2026-10-24-unmeasured-session-usage present beside the other archived changes"},
      {"what": "grep -rn 'session-tokens|\"cost\"' src/agentmarshal/journal/records.py (write rules for tokens and cost)", "result": "records.py:778-793 fixes tokens to three non-negative ints; records.py:887-930 validates cost with no tie to tokens or usage, so a cost-only zero-token session is a valid record"},
      {"what": "grep -rn docstrings of the pre-existing cost/prefix scenarios in tests/", "result": "test_report_cost_checks_findings.py:228,245,501,543 and test_report_lead_time.py:405 still name them; their _session helper writes 10/5/0 tokens, i.e. measured"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py (lines 60-520, 600-830)",
      "src/agentmarshal/journal/status_view.py (lines 1-50, 290-340, 818-907)",
      "src/agentmarshal/cli.py (lines 400-460, 1330-1390)",
      "src/agentmarshal/journal/records.py (lines 770-810, 880-935, 2038-2345)",
      "tests/test_unmeasured_session_usage.py",
      "tests/test_report_cost_checks_findings.py (lines 1-120, 220-260)",
      "openspec/specs/session-activity/spec.md (lines 380-410, 480-700, 725-852)",
      "openspec/specs/record-lifecycle/spec.md (lines 95-135)",
      "openspec/specs/contract-governance/spec.md (lines 925-965)",
      "openspec/specs/review-evidence/spec.md (lines 45-80)",
      "openspec/changes/archive/2026-10-24-status-candidate-session/specs/session-activity/spec.md (structure)",
      "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/quickstart.md (lines 520-620)",
      "pyproject.toml (ruff and mypy configuration)",
      "AGENTS.md, CHANGELOG.md (head)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the sandbox refused the command (approval required); the coordinator states the full sequence passed on this commit, so no check is claimed to fail"}
    ]
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/journal/report.py:357-359 skips an unmeasured session before reading its 'cost'; report.py:713 prints the Cost block only when measured sessions exist; tests/test_unmeasured_session_usage.py:246-268 records 1.00 USD on a zero-token session and asserts `not any(line.startswith('Cost\\t'))`; src/agentmarshal/cli.py:407-409 (token flags default 0) with cli.py:441-453 (independent cost flags) and src/agentmarshal/journal/records.py:887-930 (no rule ties cost to tokens or usage) make the record reachable; docs/adr/ADR-0019-accounting-time-quota-resets-money.md:102-109 (decision 4) and :120-127 (decision 6, cost recorded after completion)",
    "ADV-2": "openspec/specs/session-activity/spec.md:730-734 still reads 'Every line `agentmarshal status <task>` prints today SHALL print unchanged', while the new requirement at openspec/specs/session-activity/spec.md:775-792 changes an unmeasured session's record line (src/agentmarshal/journal/status_view.py:315-318); the analogous report-side clauses were MODIFIED for exactly this exception at openspec/specs/session-activity/spec.md:485-498 and :638-652; openspec/specs/contract-governance/spec.md:941-947 carries the same literal clause but is outside the contract's scope"
  }
}
AGENTMARSHAL_VERDICT_END
