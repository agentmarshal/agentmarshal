Изменение соответствует контракту. Блокирующих и advisory замечаний нет. Тесты, ruff и mypy запустить не удалось: sandbox не дал разрешения на их выполнение. Поэтому всё ниже проверено только чтением кода, а критерий «все существующие тесты проходят» я не подтвердил запуском.

- **Общий хвост (критерий 1):** оба пути лаунчера теперь идут через `_launch_review_tail` (`src/agentmarshal/journal/review.py:810`). Ни в одном из них не осталось своей копии последовательности: запуск reviewer'а, разбор verdict, `submit_review`, ветка с `artifact_ref`, сборка результата.
- **Поведение commit-пути не изменилось:**
  - В `_parse_verdict` теперь передаются `subject_fields={"reviewed_commit"}` и `expected_field="reviewed_commit"`, раньше подставлялись значения по умолчанию. Разница только в тексте сообщения «must name …», но эта ветка для commit-пути недостижима: `reviewed_commit` входит в `_VERDICT_REQUIRED`, поэтому раньше срабатывает проверка обязательных полей.
  - Добавленная проверка `subject_field != "reviewed_commit"` при единственном subject field всегда ложна.
  - В `submit_review` уходит `resolved_commit`, и это то же значение, что раньше передавалось как разобранный `reviewed_commit`. Явный `reviewed_finding=None` совпадает с умолчанием.
  - Порядок шагов сохранён: снимок, затем чтение контракта из него и сборка prompt внутри временного каталога.
- **Поведение finding-пути не изменилось:** prompt, как и раньше, строится до временного каталога. Сообщение о несовпадении subject и то, что передаётся в `submit_review`, остались прежними.
- **Правило идентичности (критерий 2):** `_actor_git_identities` и `finding_reviewer_identity_refusal` перенесены в `actors.py` слово в слово. Строковые литералы заменены на `SOURCE_GIT_IDENTITY`, `SOURCE_ACTORS_TABLE` и `SOURCE_OVERRIDE`, их значения те же. В `gate.py` копии не осталось. Gate (`gate.py:173`) и лаунчер (`review.py:943`) импортируют правило из `actors`, лаунчер больше не импортирует gate. Циклического импорта нет: `agentmarshal.project` зависит только от `agentmarshal.__version__`. В `gate.py` по-прежнему нужен `read_project_file` (строка 474), так что неиспользуемых импортов не осталось.
- **Строка transcript (критерий 4):** gate вызывает правило без `launching`. Текст «declared reviewer identity differs from the finding recorder's declared git identities» побайтно прежний.
- **Тесты:** существующие ожидания не менялись. В `tests/test_findings.py` добавлен один тест на правило из `actors`, файл входит в scope.
- **ADR-0006 / ADR-0009:** правило теперь живёт в модуле, который отвечает за ADR-0006. Логика ADR-0009 Decision 3 не изменилась.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ae7a497aa57b67f2570a4f2e087552ffb1ff2250", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
