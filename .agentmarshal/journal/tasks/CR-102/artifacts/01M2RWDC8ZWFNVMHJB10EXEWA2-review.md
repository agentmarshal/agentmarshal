Прошёл по диффу, по обоим ADR, по спекам и по остальному дереву (тесты запустить не дали — approval, так что проверка статическая: сверял сообщения об ошибках со всеми существующими ассертами и вызовы со всеми писателями).

Что проверил и что сходится:

- `load_task_for_record` (`src/agentmarshal/journal/status.py:105`) читает тот же самый `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, что и `project_status`, — второго списка в `src/` нет (grep подтверждает: единственное упоминание — строка 29).
- Все писатели переведены на helper: `submit_review.py:55`, `acceptance.py:34`, `session.py:50`, `complete.py:53,74,104`, `review.py:822,1001`, `cli.py:881,955,988,1012`. `open_task.py` не тронут корректно — он всегда создаёт новый task id (`next_task_id`, `open_task.py:150`), закрытого таска там быть не может.
- Ни одна проверка не ослаблена: старое условие везде было `task.state != "open"`, новое — то же самое плюс исключение для `session`/`reopened`.
- Новое сообщение сохраняет подстроки, на которые опираются уже существующие тесты: `"is not open (state: ...)"` (`tests/test_journal.py:1001`, `tests/test_complete.py:163`) и `"terminal record"` (`tests/test_acceptance.py:182`). Сообщение лаунчера поменялось, и единственный ассерт на старый текст обновлён в диффе; `tests/test_findings.py:451` — это транскрипт gate, он не затронут.
- Лаунчер: в commit-биндинге guard стоит до `_resolve_commit`/`_extract_snapshot`/записи промпта (`review.py:1001`), в finding-биндинге — до всего остального (`review.py:822`). Оба теста ловят факт запуска через stdin-стаб.
- Все сценарии дельта-спеки покрыты тестами с называющими их docstring'ами; параметризация даёт по тесту на команду × два терминальных состояния.
- Цитата на ADR-0005 верна: status-note этого ADR действительно говорит, что reopening делает Decision 3 не текущим правилом (`docs/adr/ADR-0005-...:33`). Противоречий с ADR-0004 (state как проекция, append-only) нет.

Одно замечание вне scope изменения:

ADV-GATE-DUPLICATES-POST-TERMINAL-SET — в `src/agentmarshal/journal/gate.py:741-758` merge-gate держит собственную, более узкую копию набора «что доливается после терминальной записи»: лента measurements-only требует, чтобы все добавленные записи оканчивались на `-session.json`, со ссылкой на ту же ADR-0005 Decision 3, что и проекция. Это второй список того же правила, которого просит не иметь третий acceptance-критерий, и он не знает про `reopened`: если completion уже влит в base, а reopening приходит отдельным кандидатом, `closed_at_base` истинно, `measurements_only` ложно, и gate отказывает с «already closed at base». `tests/test_gate.py:1992` закрывает только случай, когда completion и reopening лежат в одном коммите, так что «reopen после completion всё ещё работает» держится на уровне команды, но не на уровне merge. `gate.py` не входит в scope CR-102 и диффом не тронут, поэтому это advisory, а не блокер.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "44b8011b7a559f0f02605d881ebec8512e0372c3", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-GATE-DUPLICATES-POST-TERMINAL-SET"]}
AGENTMARSHAL_VERDICT_END
