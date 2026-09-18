Прошёлся по реализации статически (запустить pytest в этой песочнице не дали — команда требует approval, так что выводы ниже основаны на чтении кода и тестов, а не на зелёном прогоне).

Что сделано корректно:
- Все девять call-site'ов `write_record` в `src/` проверены: `session.py`, `complete.py` (×3), `cli.py` (×4), `submit_review.py` (×2), `acceptance.py` — каждый теперь проходит через `load_task_for_record`; `open_task.py` создаёт задачу и к делу не относится. Ни одного обходного пути не осталось.
- Критерий про единственный список выполнен: `grep` по дереву даёт ровно одно вхождение `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` (`status.py:29`), и `project_status` читает ту же константу. Второго списка нет.
- Guard в обоих launcher'ах стоит до `tempfile.TemporaryDirectory`/`_run_reviewer` (`review.py:822` и `review.py:1001`), так что reviewer действительно не запускается и prompt-файл не пишется.
- Совместимость сообщений проверена: `tests/test_journal.py:1000` («task CR-001 is not open (state: abandoned)») и `tests/test_acceptance.py:182` («terminal record») остаются подстроками нового текста; `reopen` и `gate` формулировки не трогает.

Теперь замечания.

F-1 — в `tests/test_journal.py:2656` параметризованный тест `test_every_writing_command_refuses_a_closed_task` гоняет все шесть команд только против `_terminal_task(...)` с дефолтным `record_type="completed"`. Терминальное состояние `abandoned` покрыто ровно одной командой — `submit-review` (`tests/test_journal.py:2553`). Для `accept`, `amend`, `finding`, `complete` и `abandon` ветка `state == "abandoned"` не закреплена ни одним тестом, хотя хелпер `_terminal_task` (`tests/test_journal.py:2499`) уже принимает нужный аргумент. Критерий контракта говорит «for each terminal state, every command … — one test per command», и вторая ось параметризации просто не добавлена.

A-1 — `load_task_for_record` (`src/agentmarshal/journal/status.py:105`) принимает `record_type` как свободную строку и нигде не сверяет её с `_RECORD_TYPE_STATES`. Опечатка в литерале допущенного типа на call-site (`"session"` / `"reopened"`) молча превращает разрешающий вызов в отказывающий, а модуль, который по design.md владеет правилом, этого не заметит. Все восемь текущих литералов совпадают с ключами проекции, но ничто это не удерживает.

A-2 — текст отказа в `src/agentmarshal/journal/status.py:116-117` подставляет внутреннее имя record type в пользовательскую фразу: для `complete` уже завершённой задачи получается «task CR-001 is not open (state: done); terminal record prevents completed», для `abandon` — «prevents abandoned». Состояние названо, как требует спека, но вторая половина предложения читается как мусор для оператора.

Мнение по сути: реализация правильная и дыру закрывает, не хватает только второй оси в параметризации тестов.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "65b664fe1d10d12ac240865795a629af4286f7d7", "verdict": "changes_required", "findings": ["F-1"], "advisory_findings": ["A-1", "A-2"]}
AGENTMARSHAL_VERDICT_END
