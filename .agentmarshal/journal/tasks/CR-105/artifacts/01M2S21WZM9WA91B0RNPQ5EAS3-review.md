Ревью CR-105 на коммите `4e0f6aa`. Тесты запустить не удалось: `uv run pytest` требует подтверждения, которого в этом режиме нет. Всё ниже проверено только чтением кода.

**Что проверил:**
- **Контракт.** Гейт теперь берёт допустимые после terminal-записи типы из `status.py` через `record_type_is_admitted_after_terminal` и `projected_state_of`. Списка суффиксов `-session.json` в `gate.py` больше нет.
- **Главный сценарий.** В `test_gate_allows_reopening_only_append_to_completed_task` reopen-запись попадает только в diff кандидата, а completed-запись лежит в базе. Тест проверяет новую PASS-строку и то, что состояние после кандидата — `open`.
- **Сценарии delta spec.** Каждый из четырёх покрыт тестом, у которого docstring называет сценарий. Для abandoned-reopen и review тесты честно пишут, что отказ даёт проекция кандидата, а не base-state ветка. Сам rule закреплён отдельным unit-тестом.
- **Рефакторинг `status.py`.** В `project_status` и `load_task_for_record` поведение и тексты ошибок сохранены: abandoned-reopen, reopen в состоянии open, работа после terminal-записи.
- **Transcript-тесты.** Их ожидания в диффе не изменены. У существующего теста на sessions только комментарий стал docstring'ом.
- **Sidecar.** Поведение не изменилось: `terminal_state_at_base` там `None`, как и раньше.
- **Design.md и ADR-0005.** Реализация следует решениям из design.md. С ADR-0005 противоречия нет: ADR сам отмечает, что reopening отменяет правило неизменяемости из Decision 3.

**Одно замечание (advisory, не блокирует):**

`gate-lifecycle-suffixes-still-duplicated`: в `src/agentmarshal/journal/gate.py:671-679` гейт по-прежнему сам решает, какие записи считаются lifecycle-записями. Для этого там жёстко прописаны суффиксы `-completed.json`/`-abandoned.json`/`-reopened.json`, а «закрытость» определяется через `endswith("-reopened.json")`. Это дублирует `_RECORD_TYPE_STATES`/`_TERMINAL_RECORD_TYPES` из `status.py`, хотя docstring `projected_state_of` утверждает, что у гейта нет собственной таблицы суффиксов. Критерий приёмки это не нарушает, он говорит только про допустимый набор. Но это тот же вид расхождения, который CR-102 называл «drift in waiting».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "4e0f6aafc518a5f6bb9f25c190680c2d339f4bdf", "verdict": "approved", "findings": [], "advisory_findings": ["gate-lifecycle-suffixes-still-duplicated"]}
AGENTMARSHAL_VERDICT_END
