Ревью CR-105 готово: коммит одобрен, блокирующих замечаний нет, есть два рекомендательных. Тесты я не запускал: в этой сессии мне не разрешили запускать `pytest`. Поэтому о том, что тесты проходят, я сужу только по чтению кода.

**Что соответствует контракту:**
- **Admitted set не дублируется.** В `gate.py` больше нет своего списка admitted suffixes: base-state check спрашивает `status.record_type_is_admitted_after_terminal`. Оставшийся кортеж суффиксов в `gate.py:735` только находит lifecycle-записи и не решает, что допускается.
- **Reopening в diff кандидата.** Тест `test_gate_allows_reopening_only_append_to_completed_task` коммитит в base только completion. Reopening создаётся командой `reopen` на ветке кандидата, и тест проверяет, что diff — ровно один файл `-reopened.json`. Проекция кандидата после этого `open`.
- **Transcript.** Строка "measurements-only append" осталась прежней, у reopening своя строка, как решено в design.md. Байт-в-байт тесты transcript я не менял и не запускал.
- **Сценарии.** Каждому из четырёх сценариев соответствует тест с docstring `Scenario: …`.
- **Остальное.** Рефакторинг `load_task_for_record` сохраняет прежнее поведение. Sidecar не затронут: там `added_records` пуст, а `terminal_state_at_base` равен None. С ADR-0005 противоречий нет: в его статусной заметке уже сказано, что reopening заменяет исторический immutability rule из Decision 3.

**Рекомендательные замечания:**

CR105-A1: тесты на отказ (`test_gate_refuses_reopening_only_append_to_abandoned_task` и `test_gate_refuses_review_only_append_to_closed_task` в `tests/test_gate.py`) проходят не благодаря новому base-state check. Отказ случается раньше, в `load_task_status` в `gate.py:643`, и они прошли бы и до этого изменения. Ветка `terminal_state == "done"` в новом предикате этими тестами не зафиксирована.

CR105-A2: правило «reopening только из `done`» по-прежнему записано в `status.py` дважды. Одна копия — новая `record_type_is_admitted_after_terminal` (строки 52-63), другая — в `project_status` (строки 90-99). Сама проекция новую функцию не вызывает, так что внутри `status.py` правила ещё могут разойтись, хотя цель задачи — одно правило.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a45bdda87ef9bf5a9b5746a679d761bf0c7135ed", "verdict": "approved", "findings": [], "advisory_findings": ["CR105-A1", "CR105-A2"]}
AGENTMARSHAL_VERDICT_END

Коннекторы Gmail, Google Calendar и Google Drive требуют авторизации в настройках коннекторов на claude.ai. Для этого ревью они не были нужны.
