## Что проверил

Прочитал `src/agentmarshal/journal/report.py` (предикат, `_cost_sums`, `_task_report`, `build_report`, `_cost_lines`, `format_report`), `src/agentmarshal/journal/status_view.py` (новый renderer и dispatch), `tests/test_unmeasured_session_usage.py`, delta-спеку и её посадку в `openspec/specs/session-activity/spec.md`, ADR-0019 и ADR-0022, `records.py`/`backfill.py`/`cli.py` на стороне записи. CI не запускал — опираюсь на твою записку.

## Приёмочные критерии

**AC1 — выполнен.** Change лежит архивом в `openspec/changes/archive/2026-10-24-unmeasured-session-usage/` с тем же набором файлов, что и соседние архивированные changes (`proposal.md`, `design.md`, `specs/session-activity/spec.md`, `tasks.md`), а delta села в `openspec/specs/session-activity/spec.md:747-851`. MODIFIED даны полным текстом с байт-в-байт заголовками и всеми сценариями для четырёх требований (`spec.md:485`, `515`, `563`, `638`). Требования, которое формулировало бы суммирование token-итогов, в `openspec/specs/` до этого не существовало (`tokens=` нигде, кроме этой delta), так что MODIFIED там и не был должен. Каждый сценарий закрыт тестом, чей docstring его называет: 12 ADDED-сценариев — `tests/test_unmeasured_session_usage.py:81,107,136,163,183,205,225,246,271,304,343,434`; два новых MODIFIED-сценария — `:371` и `:398`; переформулированные старые сценарии держат прежние тесты в `tests/test_report_cost_checks_findings.py:124-384`, и их `_session` даёт 10/5/0 токенов (`:71-83`), так что оговорка «measured» в них действительно верна.

**AC2 — выполнен по букве.** `status`: `test_an_unmeasured_sessions_tokens_show_as_unmeasured` (`:163`) и `test_a_measured_sessions_line_is_unchanged` (`:183`). Token-суммы: `:205` (строка задачи) и `:225` (`Summary`). Cost-суммы: `:271`, `:304`, `:343`. Ненулевой счёт и `usage`-блок читаются как раньше: `:107`, `:136`. Finding F1 ниже — именно о цене этого буквального чтения.

**AC3 — выполнен.** Диффа на стороне записи нет: `records.py` и правила записи не тронуты, ни один существующий тест не изменён, а `test_with_no_unmeasured_session_nothing_changes` (`:434`) вместе с неизменными `tests/test_report_cost_checks_findings.py` и `tests/test_report.py` показывают, что журнал без таких сессий печатает то же, что и раньше.

**AC4 — выполнен.** Escaping сохранён: строка записи в `status` целиком проходит `escape_for_display` в dispatch (`status_view.py:835`), а `unmeasured=<n>` — целое число, выведенное инструментом, не значение записи; в `format_report` экранирование не менялось. Других команд change не затрагивает — `build_report`/`format_report` имеют единственного вызывающего, `cli.py:1376`.

## Findings

**CR-229-F1 (blocking).** `report` молча выбрасывает записанную цену из всех сумм, если у сессии нулевые токены и нет `usage`-блока. В `report.py:357-359` `_cost_sums` делает `continue` до чтения `record.get("cost")`. Флаги `--cost-amount/--cost-currency/--cost-source` (`cli.py:441-453`) независимы и от token-флагов, и от `--usage-provider/--usage-method` (`cli.py:410-411`), то есть журнал может держать сессию, которая называет реальную сумму денег и не называет токенов — ровно тот adopter из digest 044, у которого нет измерения токенов. ADR-0019 decision 4 говорит: «`report` sums cost per currency and converts nothing — a sum in one currency is a figure the journal holds»; после change эта сумма не суммируется вовсе, а если у задачи нет других сессий, строка `Cost` не печатается совсем, и ничто в выводе не говорит, что цену отбросили — против собственного решения change'а «Exclusion is silent nowhere a sum prints» (`design.md:39-43`). Тест `:271-301` это и закрепляет: `9.99` исчезает, остаётся только `unmeasured=1`. Критерий AC2 предписывает предикат именно так, поэтому конфликт — между контрактом и ADR-0019 decision 4, и решать его автору контракта; узкая правка — считать `cost`-блок маркером измерения наравне с `usage` (сессия 0/0/0 без `usage` и без `cost` остаётся unmeasured).

**CR-229-F2 (advisory).** Предикат читает как unmeasured и backfill-импортированную сессию. `backfill.py:150-171` строит imported session record с `tokens` из host-stat export и никогда не пишет ключ `usage` (слова `usage` в модуле нет вообще), а `_require_int` подставляет 0 вместо отсутствующего поля (`backfill.py:69-73`). Stat с тремя нулями даёт запись, которая измерена и несёт провенанс (`source: imported`, `artifacts: host-stat:…`), но `report` её выбросит, а `status` пометит `tokens=unmeasured`. Сегодня ни одна CLI-команда маппер не вызывает (`backfill` в `cli.py` не встречается), так что дефект латентный.

**CR-229-F3 (advisory).** Delta вырезала исключение для unmeasured в оба output-pin'а `report` (`spec.md:485`, `spec.md:638`), но оставила pin для `status` в той же capability безусловным: `openspec/specs/session-activity/spec.md:730-734` по-прежнему требует «Every line `agentmarshal status <task>` prints today SHALL print unchanged», чему новое поле ` tokens=unmeasured` на строке session-записи прямо противоречит.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9de3f9fb7e5a664ffc13aaab7b5009bed3095923",
  "verdict": "changes_required",
  "findings": ["CR-229-F1"],
  "advisory_findings": ["CR-229-F2", "CR-229-F3"],
  "classes": {
    "CR-229-F1": "contract-mismatch",
    "CR-229-F2": "correctness",
    "CR-229-F3": "contract-mismatch"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/report.py:80-520,650-795",
      "src/agentmarshal/journal/status_view.py:1-50,280-335,820-845",
      "src/agentmarshal/journal/backfill.py:60-195",
      "src/agentmarshal/journal/records.py:2272-2347",
      "src/agentmarshal/cli.py:405-455,1300-1380",
      "tests/test_unmeasured_session_usage.py",
      "tests/test_report_cost_checks_findings.py:71-110,120-400,495-560",
      "openspec/specs/session-activity/spec.md:380-560,630-851",
      "openspec/changes/archive/2026-10-24-unmeasured-session-usage/design.md",
      "openspec/changes/archive/2026-10-24-unmeasured-session-usage/proposal.md",
      "openspec/changes/archive/2026-10-24-unmeasured-session-usage/tasks.md",
      "openspec/changes/archive/2026-10-24-unmeasured-session-usage/specs/session-activity/spec.md",
      "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/sidecar.md:320-360",
      "AGENTS.md",
      "CHANGELOG.md:1-40"
    ],
    "executed": [
      {
        "what": "grep -rn 'build_report|format_report|TaskReport|JournalReport' src/ --include=*.py (excluding journal/report.py)",
        "result": "only src/agentmarshal/cli.py:1376 and journal/__init__.py re-exports — no other command reads the report"
      },
      {
        "what": "grep -rn 'tokens=' openspec/specs/",
        "result": "only openspec/specs/session-activity/spec.md (this delta's own requirements) — no pre-existing requirement states how token totals are summed"
      },
      {
        "what": "grep -n 'usage' src/agentmarshal/journal/backfill.py",
        "result": "no match — imported session records never carry a usage block"
      },
      {
        "what": "find openspec/changes/archive/2026-10-24-unmeasured-session-usage -type f, compared with 2026-10-24-status-shows-switches",
        "result": "identical file shape (proposal.md, design.md, specs/<capability>/spec.md, tasks.md) — archived with the archive command"
      },
      {
        "what": "grep -rn 'Scenario:' tests/test_report_cost_checks_findings.py and grep -n 'def _session' -A 12 of the same file",
        "result": "every re-stated MODIFIED scenario has a test; its _session helper writes 10/5/0 tokens, so those tests are unaffected by the predicate"
      },
      {
        "what": "grep -rn '} session |\" session \"' tests/*.py",
        "result": "only tests/test_unmeasured_session_usage.py pins a status session record line — no existing status test is affected by the new renderer"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "read-only review in a snapshot with no virtualenv and no git repository; the coordinator states the sequence passed on this commit"
      }
    ]
  },
  "evidence": {
    "CR-229-F1": "src/agentmarshal/journal/report.py:357-359 — `if _is_unmeasured(record): unmeasured += 1; continue` runs before `cost = record.get(\"cost\")` at :361, so a recorded cost is summed nowhere; src/agentmarshal/cli.py:441-453 (cost flags) are independent of :407-411 (token and usage flags), so the record shape is reachable from the shipped CLI; tests/test_unmeasured_session_usage.py:271-301 pins it (`assert not any(\"9.99\" in line for line in lines)`); contradicts ADR-0019 decision 4 (docs/adr/ADR-0019-accounting-time-quota-resets-money.md, '### 4. A session can carry a cost': '`report` sums cost per currency and converts nothing — a sum in one currency is a figure the journal holds') and the change's own design decision at openspec/changes/archive/2026-10-24-unmeasured-session-usage/design.md:39-43 ('Exclusion is silent nowhere a sum prints'), since tests/test_unmeasured_session_usage.py:246-269 shows a task whose only sessions are unmeasured prints no Cost line at all",
    "CR-229-F2": "src/agentmarshal/journal/backfill.py:150-171 builds the imported session record with `tokens` from the host stat and no `usage` key (`grep -n usage src/agentmarshal/journal/backfill.py` → no match), and src/agentmarshal/journal/backfill.py:69-73 `_require_int` returns `stat.get(field, 0)`, so a zero-token stat yields a record `_is_unmeasured` (src/agentmarshal/journal/report.py:198-204) calls unmeasured despite `source: imported` and the `host-stat:` artifacts ref at backfill.py:165-171; `grep -rn backfill src/agentmarshal/cli.py` → no match, so no shipped command writes it yet",
    "CR-229-F3": "openspec/specs/session-activity/spec.md:730-734 — 'Every line `agentmarshal status <task>` prints today SHALL print unchanged, the session line appended after' was left unmodified, while the two analogous report pins at spec.md:485-492 and spec.md:638-648 did gain the 'A journal holding an unmeasured session admits the one exception…' carve-out; src/agentmarshal/journal/status_view.py:315-318 appends ' tokens=unmeasured' to a session record line"
  }
}
AGENTMARSHAL_VERDICT_END
