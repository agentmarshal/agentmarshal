Провёл review: прочитал `status.py`, все писатели (`cli.py`, `complete.py`, `acceptance.py`, `submit_review.py`, `session.py`, `review.py`), gate, спеки, ADR-0004/0005 и новые тесты. Прогнать pytest в этой песочнице не дали (команда требует approval), поэтому проверка тестов — статическая: сверил хелперы, имена аргументов CLI, типы возвратов (`read_records` → `list`, сравнение с `before` корректно) и строки refusal'ов против существующих ассертов.

**Что проверено по существу**

- Guard `load_task_for_record` читает `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` — ту же константу, что и `project_status`; второй копии набора типов записей в дереве нет (AC3 выполнен для пути записи).
- Все 12 точек записи в существующую задачу проходят через guard: `cli.py:881,955,988,1008`, `complete.py:53,74,104`, `acceptance.py:34`, `submit_review.py:55`, `session.py:50`, `review.py:822,999`. Оставшиеся `write_record` — `open_task.py` (новый id) и `migrate.py` (перестройка журнала, вне scope, сам себя проверяет через `load_task_status` на `migrate.py:428`).
- Guard в обеих ветках лаунчера стоит до `tempfile.TemporaryDirectory`/`_extract_snapshot`/`_run_reviewer`, то есть reviewer действительно не запускается и prompt не пишется (AC5).
- `session` и `reopened` не сломаны: `record_session` допускает любое состояние, `reopen` сохранил единственный предикат `state != "done"` — теперь в одном месте, и он же чинит прежний дрейф (раньше `reopen` после `abandon` отлавливался только проекцией).
- Обратная совместимость сообщений: `"is not open (state: X)"` и `"cannot be reopened (state: X)"` сохранены как подстроки, так что `test_complete.py:163`, `test_reopen.py:82,94`, `test_journal.py:1001` не ломаются. Изменилось только `"is already closed (state: …)"` в finding-лаунчере — соответствующий тест обновлён в том же диффе; в gate (`test_findings.py:485`) старая формулировка живёт отдельно и не тронута.
- ADR-0005 Decision 3 и его status-note («reopening makes the historical immutability rule in Decision 3 no longer the current lifecycle rule») процитированы в спеке корректно; противоречия с ADR-0004 нет.
- Все шесть сценариев дельта-спеки имеют тест, чей docstring их называет; оба терминальных состояния параметризованы.

Блокирующих дефектов не нашёл. Две необязательные заметки ниже.

`gate-lane-keeps-its-own-post-terminal-list`: в `src/agentmarshal/journal/gate.py:745-751` measurements-only лента решает, что может быть добавлено к закрытой на base задаче, по суффиксу имени файла `-session.json`, а не по `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` — критерий «no second list of it exists in the tree» выполнен для писателя, но это третье независимое кодирование того же вопроса, и расширение константы молча не дойдёт до gate (gate.py вне scope этой задачи, поэтому только advisory).

`contract-names-an-unarchived-change-path`: контракт называет документ `openspec/changes/writer-refuses-a-closed-task/`, а дифф создаёт каталог изменения только как `openspec/changes/archive/2026-09-18-writer-refuses-a-closed-task/` — по названному пути в дереве нет ничего; содержательно критерий выполнен (сценарии есть и в архивной копии, и в `openspec/specs/record-lifecycle/spec.md`, и это единая конвенция репозитория — все changes лежат в archive/), а проверка gate «named documents touched» проходит за счёт второго названного документа, так что отсутствие первого ничем не ловится.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "0be1f658bb2124517360ef2b6adb9860e92941e5", "verdict": "approved", "findings": [], "advisory_findings": ["gate-lane-keeps-its-own-post-terminal-list", "contract-names-an-unarchived-change-path"]}
AGENTMARSHAL_VERDICT_END
