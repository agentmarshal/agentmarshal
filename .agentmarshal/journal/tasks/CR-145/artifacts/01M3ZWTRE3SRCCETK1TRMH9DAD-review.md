Проверил контракт, delta-спеку, архив и реализацию. Запустить CI-последовательность в этой сессии не удалось (выполнение команд не разрешено), поэтому `pytest`/`ruff`/`mypy` проверены чтением, а не прогоном — об этом ниже.

## Что сходится

**Критерий 1 (change + архив).** `openspec/changes/archive/2026-10-03-read-rules-by-schema/` содержит `proposal.md`, `design.md`, `tasks.md`, `specs/record-schema/spec.md` и `.openspec.yaml` в том же формате, что соседние архивы; `openspec/changes/read-rules-by-schema/` не остался. Все восемь сценариев delta-спеки названы в docstring'ах тестов: четыре в `tests/test_record_schema.py:68,123,153,169,180`, `tests/test_record_schema.py:274,291`, `tests/test_record_schema.py:330` и «a record a candidate adds…» в `tests/test_gate.py:1410`.

**Критерий 2 (таблица).** `_RULES` (`src/agentmarshal/journal/records.py:243`) и `_RULE_FROM_SCHEMA:559` — две структуры, как и решено в design.md; полнота проверяется `set(_RULES) == set(_RULE_FROM_SCHEMA)` (`tests/test_record_schema.py:75`), привязки пины́тся в `tests/test_record_schema.py:131-135`: всё на 1, кроме provenance 2, finding-binding 4, reviewed-contract 5, coordination 6. Порядок регистрации правил совпадает с прежним порядком проверок в `_validate_record` вплоть до позиции coordination-гейта внутри разобранного `_validate_session_record`, так что первое сообщение об ошибке для испорченной записи не поехало.

**Критерий 3 (разделение по сторонам).** Чтение стало строго слабее прежнего: раньше `read_records` применял весь набор, теперь — подмножество по схеме записи плюс те же placement-проверки. Запись осталась ровно той же: `validate_record_for_write` (`:1000`) добавляет `task`/`task_label`/`finding_ids`, `validate_record_content` (`:1357`) — `filename`/`filename_record_type`, и сообщения совпадают с прежними дословно, включая обёртку `f"{error}: {path}"` в `read_records`. Provenance сохранил внутренний guard `schema >= 2` (`:497`), без которого `tests/test_journal.py:651` (schema-1 session на запись) сломался бы.

**Критерий 4 (минимальная схема).** `_minimum_schema` (`:1055`) используется всеми девятью `create_*` и `session_record_schema`; литералов `schema` у писателей не осталось (единственный вне `records.py` — `backfill.py:151`, и он идёт через `session_record_schema`). Параметризованный тест покрывает все девять писателей и все четыре значения.

**Критерий 5.** Ни один существующий тест не ослаблен и не удалён; `test_gate.py` только дополнен.

## Замечания (не блокирующие)

ADV-rule-granularity-hides-later-tightenings — правила `review`, `acceptance`, `finding`, `session-fields`, `session-tokens` (`src/agentmarshal/journal/records.py:357,363,377,413,444`) каждое упаковывает по десятку отдельных проверок поля и значения под одну запись таблицы со схемой 1. Сегодня это безвредно (решение 6 ADR-0015 всё равно привязывает существующие проверки к 1), но завтрашнее ужесточение, дописанное внутрь `_validate_review_record`, применится от схемы 1 ко всей истории: запись в таблице уже есть, забыть её нельзя, и completeness-тест такой случай не поймает — то есть ровно та гарантия, ради которой решение 7 требует таблицу, на этих правилах не работает. design.md обосновывает укрупнение только через сегодняшние привязки, не через будущие добавления.

ADV-minimum-schema-duplicates-field-families — `_minimum_schema` (`src/agentmarshal/journal/records.py:1061`) зашивает `"reviewed_contract" → 5` вторым экземпляром того знания, которое уже лежит в `_FIELD_FAMILIES:263` как `(5, "review", _SCHEMA_5_FIELDS)`, и ничто не связывает две таблицы. Схема 4 и coordination разделяют константы (`_SCHEMA_4_FIELDS`, `_COORDINATION_SESSION_SCHEMA`), а семейство поля — нет, так что следующая схема должна быть прописана в двух местах. Отказ будет громким (писатель получит отказ от собственного правила admission на записи), но задача просила «одну производную», а здесь их две.

## Чего я не смог подтвердить

`uv run pytest`, `ruff check`, `ruff format --check`, `mypy` и `agentmarshal validate` в этой сессии не запускались — выполнение команд не разрешено. Форматирование и типы я проверил чтением (длины строк под 88, magic trailing comma удерживает развёрнутые литералы, контравариантность `_context: object` в тестовых правилах против `_RuleCheck` корректна), но это не замена прогону.

**Вердикт: approved** — блокирующих находок нет, оба замечания советующие.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "f91952eba8bec831846c9cb693671c8261099b88", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-rule-granularity-hides-later-tightenings", "ADV-minimum-schema-duplicates-field-families"]}
AGENTMARSHAL_VERDICT_END
