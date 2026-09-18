Ревью CR-105 на `a45bdda87ef9bf5a9b5746a679d761bf0c7135ed` (только чтение). Прогнать тесты не получилось: запуск `pytest` требует одобрения, а его в этой сессии не дали. Всё ниже основано на чтении кода.

Все четыре acceptance-критерия выполнены:
- **Reopening в diff кандидата.** Тест `test_gate_allows_reopening_only_append_to_completed_task` коммитит completion в base, а reopening добавляет только в candidate. Он проходит через `admitted_records_only` и проверяет, что projection кандидата — `open`.
- **Правило берётся из `status.py`.** В `gate.py` больше нет списка допустимых suffix-ов: `-session.json` убран. Остался только кортеж lifecycle-suffix-ов, по которому определяется «closed at base», а это не допустимый набор.
- **Разбор имени файла надёжен.** `_record_type_from_record_path` полагается на то, что тип в имени файла — `[a-z]+`. Кривое имя файла всё равно даёт FAIL позже, в проверке добавленных records.
- **Transcript-тесты не тронуты.** Строка про measurements не изменилась, а тест с ней поменялся только тем, что комментарий стал docstring-ом.
- **Сценарии и design.md.** Каждый сценарий delta spec назван в docstring-е теста. Реализация следует решениям design.md.
- **Рефакторинг `load_task_for_record`.** Сообщения об ошибках и поведение сохранились.
- **ADR-0005.** Противоречия нет: в статусе 0.3.0 ADR прямо сказано, что reopening меняет правило Decision 3.

Советы, которые мёрж не блокируют:

- **CR105-A1:** в `tests/test_gate.py` тесты `test_gate_refuses_reopening_only_append_to_abandoned_task` и `test_gate_refuses_review_only_append_to_closed_task` получают отказ ещё от начального `load_task_status` в `run_gate`, до проверки base-state. Они прошли бы и на старом коде. Новая ветка `record_type_is_admitted_after_terminal(..., "abandoned")` в gate ими не проверяется.
- **CR105-A2:** в `src/agentmarshal/journal/status.py` `project_status` по-прежнему сам проверяет «reopen только из done» (`if state != "done"`) и не вызывает новый `record_type_is_admitted_after_terminal`. В `status.py` остаются две записи одного правила, и gate читает не ту, которую применяет сама projection.
- **CR105-A3:** в `src/agentmarshal/journal/gate.py` `terminal_state_at_base` вычисляет состояние по suffix-у имени файла. Получается локальная для gate копия `_RECORD_TYPE_STATES`. Когда последний lifecycle-record — `-reopened.json`, значение становится `"abandoned"`. Сейчас это безвредно, потому что `closed_at_base` там ложно, но значение вводит в заблуждение.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a45bdda87ef9bf5a9b5746a679d761bf0c7135ed", "verdict": "approved", "findings": [], "advisory_findings": ["CR105-A1", "CR105-A2", "CR105-A3"]}
AGENTMARSHAL_VERDICT_END
