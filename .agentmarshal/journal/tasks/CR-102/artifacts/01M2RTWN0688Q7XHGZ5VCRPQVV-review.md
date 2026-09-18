Разобрал диф целиком плюс окружающий код: все места записи (`write_record`) в существующую задачу, обработчики исключений в CLI, оба пути лаунчера ревью и существующие тесты, которые могли сломаться о новый текст отказа.

Что проверил по критериям:

- **Гвард один и в нужном месте.** `load_task_for_record` (`src/agentmarshal/journal/status.py:105`) читает тот же `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, что и `project_status`; второго списка в дереве нет (grep по `session`+`reopened` даёт единственную строку `status.py:29`). Условие `state != "open"` эквивалентно `has_terminal_record` проекции — переходы состояний это подтверждают.
- **Все писатели закрыты.** Каждый `write_record` в существующую задачу теперь идёт за гвардом: `submit_review.py:55`, `acceptance.py:34`, `session.py:50`, `complete.py:53/74/104`, `cli.py:881/955/988/1012`. Остальные вызовы `load_task_status` — читатели (`status`, `report`, `brief`, `validate`, `gate`, `prune`) и `migrate`, который строит новый журнал.
- **Исходный сценарий порчи закрыт:** `abandon` → `submit-review` теперь отказывает до записи, и запись до `run_gate`/до запуска ревьюера во всех путях.
- **Совместимость по сообщениям.** Новый текст — надмножество старого, поэтому существующие проверки подстрок живы: `tests/test_journal.py:1001` («is not open (state: abandoned)»), `tests/test_acceptance.py:182` («terminal record»), `tests/test_reopen.py:94` (своя проверка `state != "done"` в `_run_reopen` сохранена).
- **Оба лаунчера** отказывают до `_run_reviewer` и до записи prompt-файла.

Две необязательные заметки ниже.

Сценарий record-lifecycle «a launched review on a closed task runs no reviewer» назван для задачи, которая «has completed **or** been abandoned», но оба теста лаунчера (`tests/test_review_launcher.py:925` и новый `test_a_closed_commit_review_is_refused_before_running`) закрывают задачу через `abandon`; состояние `done` не проверено ни для одной привязки, и в отличие от тестов прямых писателей ни один из них не утверждает, что `validate` всё ещё проходит.

Текст отказа в `src/agentmarshal/journal/status.py:121` подставляет внутреннее имя типа записи в пользовательский вывод, из-за чего `complete` на закрытой задаче отвечает «terminal record prevents completed», а `accept` — «prevents acceptance», то есть называет тип записи, а не команду, которую человек набрал.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "79eff88bdaeb66a81fe36183e79ef972729af1e4", "verdict": "approved", "findings": [], "advisory_findings": ["launcher-closed-task-tests-cover-only-abandoned", "refusal-message-names-internal-record-type"]}
AGENTMARSHAL_VERDICT_END
