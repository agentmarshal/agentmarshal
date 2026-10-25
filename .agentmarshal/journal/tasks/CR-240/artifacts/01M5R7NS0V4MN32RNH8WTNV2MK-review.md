Прочитал `gate.py` целиком вокруг изменения, `records.py` (`read_records`, `validate_task_id`, `validate_record_content`), CLI-обёртку `_run_gate`, `complete.py`, ADR-0004, фикстуры транскриптов и новые тесты. Выполнить pytest/mypy в этой песочнице не смог — нет venv, а `uv run` заблокирован разрешениями, так что результаты CI беру из заметки координатора.

**Что по критериям приёмки**

Критерий 1 (отказ любому добавленному пути под `tasks/<id>/records/`, у которого остаток содержит `/`, — и для судимой задачи, и для любой другой). Выполнен: `_record_path_task` (`src/agentmarshal/journal/gate.py:404-423`) принимает ровно форму `tasks/<id>/records/<file>` — ровно ту, что принимает `read_records` (`src/agentmarshal/journal/records.py:2725-2755`), — и держит сегмент задачи на том же `validate_task_id`; проверка добавленных записей (`gate.py:2152-2168`) отказывает по имени до чтения байтов, одной строкой `FAIL: invalid added records: <path>: only tasks/<id>/records/<file> is a record path`. `_is_record_path` намеренно оставлен шире, поэтому вложенный путь не ускользает из `evidence_changes`/append-only. Демонстрируют `test_gate_refuses_a_record_nested_below_another_tasks_records` (другая задача, journal-only) и `test_gate_refuses_the_judged_tasks_nested_record_on_the_implementation_lane` (судимая задача). Побочно закрыта и более широкая дыра: `tasks/cr-2/records/<ULID>-session.json` с полем `task = "cr-2"` раньше проходил проверку целиком (старый `expected_task` брался тем же `split`, и совпадал), теперь отказывается — `test_gate_refuses_a_record_below_a_directory_that_is_not_a_task_id`.

Критерий 2 (вложенный путь под собственной records/ судимой задачи даёт FAIL-строку, а не безымянную ошибку или traceback). Выполнен: отказ `load_task_status` теперь удерживается (`gate.py:1259-1272`), а не поднимается сразу, и при `task is None` с непарсящимся добавленным путём печатается `NOT EXAMINED: …` плюс та же FAIL-строка с возвратом `passed=False` (`gate.py:1349-1372`). Порядок сохранён в двух местах: пустой диапазон по-прежнему уступает ошибке журнала (`gate.py:1288-1293`), а необъяснимая диффом ошибка поднимается как раньше (`gate.py:1372`). Это ровно сценарий trusted-checkout из ADR-0004 («The merge-authority wrapper checks out the merge candidate and runs the gate there») — противоречия с решением нет. Демонстрирует `test_gate_fails_a_record_nested_below_the_judged_tasks_records`: гейт запускается через `main()` на чекауте кандидата, проверяется код 1, FAIL-строка в stdout, отсутствие traceback и отсутствие голого `record path is not a file` в stderr.

Критерий 3 (тесты на реальных временных git-репозиториях, обе полосы, фикстуры байт-в-байт, CI). Выполнен: пять новых тестов используют существующие хелперы `_gate_repo`/`_candidate_head`/`_run`/`_approve`, покрывая journal-only и implementation для чужой и для судимой задачи. Фикстуры не тронуты, и строки, которые они фиксируют (`PASS: added records are valid`, `PASS: added records are valid (none examined: …)`), не меняются: для плоского валидного пути `_record_path_task` возвращает ровно тот же id, что давал прежний `removeprefix(...).split("/", 1)[0]`, а все существующие сценарии (`test_gate_refuses_invalid_added_records`, `test_the_gate_checks_added_records_by_the_current_rules`) кладут записи плоско. Отдельно проверил, что в sidecar `added_records` обнуляется раньше новой ветки, так что поведение sidecar не меняется, и что ни одна journal-директория проекта не имеет `records/` вне `tasks/CR-*/` — легитимных путей новая проверка не ловит. Прохождение самого CI не воспроизводил — беру из заметки координатора.

**Advisory**

ADV-WORDING-1 — текст отказа неточен для одного из случаев, которые сам же диф добавляет. В `gate.py:415-419` `_record_path_task` возвращает `None`, когда сегмент задачи не проходит `validate_task_id`, а вызывающий код (`gate.py:2158-2160`) печатает для этого единственную причину `_NON_RECORD_PATH_REASON` = «only tasks/<id>/records/<file> is a record path» (`gate.py:87-91`). Для пути `.agentmarshal/journal/tasks/cr-2/records/01…-session.json` человек читает отказ, утверждающий, что путь не имеет формы `tasks/<id>/records/<file>`, — хотя визуально он её имеет; настоящая причина в том, что `cr-2` не является task id. Новый тест `test_gate_refuses_a_record_below_a_directory_that_is_not_a_task_id` прямо фиксирует это расхождение в докстринге и всё равно утверждает общее сообщение. Это не блокирует: отказ верный и fail-closed, но в проекте, который так тщательно формулирует транскрипт, отдельная причина вида «task segment is not a task id» читалась бы честнее.

Блокирующих находок нет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "396ff3c8d26fb3269c13827217adc4a5a4190e6e",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-WORDING-1"],
  "classes": {
    "ADV-WORDING-1": "style"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/gate.py (lines 60-95, 380-435, 1200-1400, 1425-1530, 2140-2330, 2415-2432)",
      "src/agentmarshal/journal/records.py (validate_task_id 331-335, validate_record_content 2696-2722, read_records 2725-2780, create_session_record 2330-2354)",
      "src/agentmarshal/journal/status.py (load_task_status 144-152)",
      "src/agentmarshal/cli.py (_run_gate 910-1010)",
      "src/agentmarshal/journal/gate_context.py (derive_gate_context 105-125)",
      "src/agentmarshal/journal/complete.py (50-78)",
      "tests/test_gate.py (imports 1-45, helpers 87-200, 300-430, 1857-1865, existing added-record tests 1984-2056, new tests 2060-2230)",
      "tests/fixtures/gate/embedded-journal-only.stdout and the other three fixture triples",
      "docs/adr/ADR-0004-journal-data-model.md",
      "CONTRIBUTING.md (Releases section), CHANGELOG.md (0.6.0 section), AGENTS.md"
    ],
    "executed": [
      {"what": "grep -rn 'added records' tests/fixtures/gate", "result": "only the four unchanged PASS lines; no fixture carries an invalid-added-records transcript, so the new reason string changes no fixture"},
      {"what": "find .agentmarshal/journal -type d -name records -not -path '*/tasks/CR-*/records'", "result": "no output - every records/ directory in the project journal is tasks/<id>/records/, so _record_path_task refuses no legitimate path"},
      {"what": "grep -rn 'does not match its directory' tests/ src/", "result": "tests/test_gate.py:2010 and tests/test_record_schema.py:695 only, both on flat tasks/CR-001/records/<file> paths whose behaviour is unchanged"},
      {"what": "grep -rn 'run_gate(' src/", "result": "callers are cli.py:965, cli.py:1089 and complete.py:64; all treat passed=False as a refusal, so the new early return is handled"}
    ],
    "not_run": [
      {"what": "uv run pytest / ruff / mypy", "why": "no .venv in the snapshot and uv invocation was denied by the sandbox permission prompt; CI results taken from the coordinator's note"}
    ]
  },
  "evidence": {
    "ADV-WORDING-1": "src/agentmarshal/journal/gate.py:415-419 returns None when validate_task_id rejects the segment, and gate.py:2158-2160 reports the single reason defined at gate.py:87-91 ('only tasks/<id>/records/<file> is a record path'); tests/test_gate.py:test_gate_refuses_a_record_below_a_directory_that_is_not_a_task_id asserts that message for .agentmarshal/journal/tasks/cr-2/records/<ULID>-session.json, a path that does have that shape"
  }
}
AGENTMARSHAL_VERDICT_END
