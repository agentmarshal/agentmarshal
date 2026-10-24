Разобрал диф по файлам в снапшоте: прочитал `src/agentmarshal/journal/report.py`, `status_view.py`, `display.py`, правила записи в `records.py`, новый тест и существующие pinned-тесты `status`/`report`, delta-спеку и ADR-0019/ADR-0022. Запустить проверки не смог — sandbox отклонил выполнение `uv`/`python3`, поэтому про CI опираюсь на твою констатацию и помечаю это как не проверенное мной.

**Как диф выполняет acceptance criteria.**

Критерий 1 выполнен: change лежит архивом в `openspec/changes/archive/2026-10-25-unmeasured-session-usage/` с `proposal.md`, `design.md`, `tasks.md` и delta на `session-activity`, а delta применена в `openspec/specs/session-activity/spec.md:731-905`; пять MODIFIED-требований повторены полным текстом с байт-в-байт теми же заголовками (`report --task shows the task's cost per currency`, `report aggregates cost per currency`, две «leave today's output first and unchanged» и `the session line leaves today's output unchanged…`), а других требований про суммирование токенов в `openspec/specs/` нет — `grep -rn "tokens" openspec/specs/` даёт только `session-activity`. Все 16 сценариев delta имеют по тесту с называющим их docstring в `tests/test_unmeasured_session_usage.py` (например «zero tokens and no usage is unmeasured» → `test_zero_tokens_and_no_usage_is_unmeasured`, «a task holding only unmeasured sessions carrying no cost prints no cost lines» → `test_a_task_holding_only_unmeasured_sessions_carrying_no_cost_prints_no_cost_lines`).

Критерий 2 выполнен: предикат один — `_is_unmeasured` в `report.py:192-211`, и он точен для любой валидной записи, потому что правило `session-tokens` (`records.py:778-793`) требует ровно `input/output/cache` целыми ≥ 0; `isinstance(tokens, dict)` оставляет синтетические записи без `tokens` измеренными. Токенные суммы исключают такие сессии в `report.py:424` (и агрегат через `sum(task.tokens)` в `report.py:511`), поля `unmeasured=` печатаются последними на строке задачи (`report.py:766-767`) и на `Summary` (`report.py:796-797`) — демонстрируют `test_the_task_line_names_the_unmeasured_sessions_it_left_out` и `test_the_summary_names_the_unmeasured_sessions_it_left_out`. Cost-часть соответствует поправке контракта: в `report.py:364-376` unmeasured-сессия с `cost` попадает и в `sessions`, и в сумму валюты, а без `cost` — выпадает и считается отдельно (`test_an_unmeasured_sessions_recorded_cost_joins_the_per_currency_sums`, `test_a_lone_unmeasured_session_with_a_cost_prints_its_cost_lines_as_today`, `test_an_unmeasured_session_carrying_no_cost_is_left_out_of_the_cost_sums_and_named`). `status` помечает строку записи в `status_view.py:302-318` (`test_an_unmeasured_sessions_tokens_show_as_unmeasured`), а сессия с `usage` или с ненулевым счётчиком читается как сегодня (`test_a_session_with_a_usage_block_reads_as_today`, `test_a_session_with_a_non_zero_token_reads_as_today`, `test_a_measured_sessions_line_is_unchanged`).

Критерий 3 выполнен: диф трогает только `report.py`, `status_view.py`, `tests/` и `openspec/` — ни `records.py`, ни писатели, ни правила записи; ни один существующий тест не изменён, и их session-хелперы дают измеренные сессии (`tests/test_status_base.py:87-90` — 1/2/3; `tests/test_status_view.py:191-201` — 1/2/3 и 4/5/6; `tests/test_report_cost_checks_findings.py:71-83` — 10/5/0) либо вообще не несут ключа `tokens` (`tests/test_status_candidate_session.py:56-66`), так что пины остаются байт-в-байт; дополнительно это пинует `test_with_no_unmeasured_session_nothing_changes`.

Критерий 4 выполнен в части, которую можно прочитать: новый renderer сессии возвращает сырую строку, а экранирует её целиком dispatch в `status_view.py:835`, причём повторное экранирование идемпотентно (`display.py:17-42` — `\n` → `\\n`, и backslash с `n` правилом не запрещены), поэтому строка измеренной сессии совпадает с прежним generic-fallback’ом; новые поля `report` — целые числа. Других команд изменение не касается: `build_report` вызывается только из `_run_report` (`cli.py:1376`), `--findings` идёт своим билдером, а больше нигде в `src/` токенных сумм нет.

**F-1 (advisory, неподтверждено прогоном):** одно и то же поле `unmeasured=` несёт в одном выводе два разных числа — на строке задачи и `Summary` это все unmeasured-сессии (`report.py:766`, `report.py:796`), а на `Cost`-строках только те, что без `cost` (`report.py:723`); на журнале из `tests/test_unmeasured_session_usage.py:449-487` это даёт `Summary … unmeasured=3` рядом с `Cost … unmeasured=2`, и тест фиксирует только вторую цифру, так что расхождение ничем не пинуется. Поведение сознательно описано в delta, поэтому это замечание, а не блок.

**F-2 (advisory):** `_cost_sums` вернул 5-элементный кортеж из четырёх безымянных `int` (`report.py:386-391`) в порядке `without_cost, sessions, …`, тогда как `_cost_lines` принимает их в обратном порядке `sessions, sessions_without_cost, …` (`report.py:706-709`); оба вызова сейчас верны, но перепутанный unpack или аргумент пройдёт и mypy, и ruff молча — небольшой dataclass снял бы ловушку.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "cb1fa8eac6dedc67a798c96c2c261916c9308309",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["F-1", "F-2"],
  "classes": {
    "F-1": "style",
    "F-2": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"tokens\" openspec/specs/", "result": "matches only in openspec/specs/session-activity/spec.md — no other capability states how token totals are summed"},
      {"what": "grep -rn \"tokens\" --include=*.py src/", "result": "only report.py:421-424 (task line sum) and report.py:511 (aggregate) sum session tokens; status_view.py:315-317 is the new mark; no other command sums tokens"},
      {"what": "grep -rn \"build_report|format_report\" --include=*.py src/", "result": "single caller: cli.py:1376 in _run_report; --findings uses build_findings_report"},
      {"what": "grep -rn \"TaskReport(|JournalReport(\" tests/ src/", "result": "all five construction sites pass the new fields by keyword; tests construct with keywords only, so inserting fields before rejected_commits breaks nothing"},
      {"what": "grep -n \"def _session\" -A 25 on tests/test_status_base.py, tests/test_report_cost_checks_findings.py, tests/test_status_candidate_session.py and sed on tests/test_status_view.py:188-245", "result": "every pinned session record carries non-zero tokens (1/2/3, 4/5/6, 10/5/0) or no 'tokens' key at all, so _is_unmeasured leaves them measured and the pins stay byte-for-byte"},
      {"what": "grep -rn \"sessions_without_cost|tokens=\" docs/ README.md CHANGELOG.md", "result": "only docs/sidecar.md:335 and docs/adr/ADR-0019 line 43 — both describe a measured session, so no doc transcript goes stale"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/display.py",
      "src/agentmarshal/journal/records.py (session field set at 110-126, _check_session_tokens at 778-793, _check_session_usage, create_session_record at 2272-2346)",
      "tests/test_unmeasured_session_usage.py",
      "tests/test_report.py",
      "tests/test_report_cost_checks_findings.py",
      "tests/test_status_view.py",
      "tests/test_status_base.py",
      "tests/test_status_candidate_session.py",
      "tests/test_display.py",
      "openspec/specs/session-activity/spec.md",
      "openspec/changes/archive/2026-10-25-unmeasured-session-usage/ (proposal.md, design.md, tasks.md, specs/session-activity/spec.md)",
      "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "CONTRIBUTING.md",
      "docs/quickstart.md (record-session section)",
      "docs/sidecar.md (status/report transcripts)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the sandbox refused every command that executes uv or python3, so no check could be run; the coordinator states the full sequence passed on this commit and I report no tool failure"},
      {"what": "observing the aggregate Summary line of the journal built in tests/test_unmeasured_session_usage.py:449-487", "why": "pytest could not be executed; the Summary=3 vs Cost=2 figure behind F-1 is derived from reading report.py:723 and report.py:796"}
    ]
  },
  "evidence": {
    "F-1": "src/agentmarshal/journal/report.py:766 and :796 append unmeasured=task.unmeasured / report.unmeasured (every unmeasured session), while src/agentmarshal/journal/report.py:723 builds the Cost lines' field from unmeasured_without_cost; for the journal in tests/test_unmeasured_session_usage.py:449-487 (three unmeasured sessions, one of them carrying a cost) the Cost lines are pinned at unmeasured=2 (tests/test_unmeasured_session_usage.py:496-497) and the Summary line, which the same code path gives unmeasured=3, is not asserted",
    "F-2": "src/agentmarshal/journal/report.py:386-391 returns (costs, without_cost, sessions, unmeasured, unmeasured_without_cost); src/agentmarshal/journal/report.py:706-709 declares _cost_lines(costs, sessions, sessions_without_cost, unmeasured) — positions 2 and 3 are swapped between the two signatures and all four values are plain ints, so a mis-ordered unpack or call type-checks"
  }
}
AGENTMARSHAL_VERDICT_END
