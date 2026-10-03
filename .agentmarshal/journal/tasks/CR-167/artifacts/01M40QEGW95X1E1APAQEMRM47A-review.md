Я прочитал код целиком вокруг диффа (реестр типов записей, таблицу правил, путь записи/чтения, проекцию и gate), сверил его с ADR-0017 decision 1 / ADR-0022 §3 и §8, и сверил delta-спеки с живыми спеками.

## Что проверено по критериям контракта

**Тип записи объявлен один раз.** `RECORD_TYPES["check"]` (`attestation.py:94-99`) даёт predicate type, `projects_to=None`, `admitted_after_terminal={"done","abandoned"}`, `writable` по умолчанию и `requires_recorded_by=True`. Все производные таблицы (`PREDICATE_TYPES`, `_RECORD_TYPE_STATES`, `_TERMINAL_RECORD_TYPES`, `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, `_WRITABLE_RECORD_TYPES`) выводятся из него; две рукописные точки (`_RECORD_FIELDS["check"]`, `WritableRecordType`) обновлены и закреплены пинами в `tests/test_attestation.py`.

**Поля и правила.** Семейство `(7, "check", _SCHEMA_7_CHECK_FIELDS)` в `_FIELD_FAMILIES`; `check-fields-7` (bound 7) проверяет 40-hex `commit`, непустой `name`, `result` из четырёх значений и непустоту опциональных строк после `strip()`. `_TEXT_BYTE_LIMITS[("check","excerpt")] = 4096` — измерение по UTF-8, отказ без усечения. В `_FORGEABLE_TEXT_FIELDS` ровно четыре ключа, которые называет контракт; `commit` и `result` не регистрируются, и это корректно — их форма не допускает ни одного символа, который отверг бы forgeable-text.

**Отказ ниже схемы 7 с двух сторон.** Правило `check`, привязанное к 1, — единственный способ выполнить «refused at write **and on read**»: правило, привязанное к 7, не достало бы schema-6 запись на чтении вообще. Привязка к 1 здесь безопасна именно потому, что типа `check` не существовало раньше, так что никакая легальная история его не несёт. Запись с полями семейства ловится раньше правилом `fields` («unsupported fields»), «пустая» — правилом `check`. Оба пути покрыты тестами.

**Ничего не меняется для других типов.** `_minimum_schema` добавляет одну ветку по `record_type`; обе новые таблицы ключуются на `("check", …)` и фильтруются по типу записи в `_check_text_limits` / `_check_forgeable_text`. Проекция и gate читают допуск через `record_type_is_admitted_after_terminal` (`gate.py:815`) — второго списка нет, суффиксный список в `gate.py:777` касается только lifecycle-записей и расширения не требовал. Формулировка строки measurements (`gate.py:831`) оставлена прежней — это заявленный non-goal.

**Спеки и архив.** MODIFIED-заголовки в record-lifecycle совпадают дословно с живыми (`### Requirement: A closed task admits only what its projection admits`, `### Requirement: The merge gate admits what the projection admits after a terminal record`); все 12 ADDED-сценариев review-evidence и 4 новых сценария record-lifecycle имеют тесты с называющими их docstring'ами. `openspec/changes/` содержит только `archive`, так что change архивирован. Фикстуры gate диффом не затронуты.

Расхождений с ADR-0022 §3 (имена и словарь `result`) и §8 (4 KiB на `excerpt`, лимит `reason` только для типов, где это поле есть — у `check` его нет) не нашёл.

## Advisory

CHK-001 — комментарий-шапка таблицы `_RULE_FROM_SCHEMA` в `src/agentmarshal/journal/records.py:794-801` перечисляет shape-правила схемы 7 по именам («The session-fields-7 and contract-hash-7 shape rules take the same binding for the same reason») и после этого изменения перечисление неполно: `check-fields-7` получил ту же привязку, но не назван, и новая категория — type-gate `check`, привязанный к 1, — у таблицы тоже не упомянута, хотя обоснование есть у самого правила (`records.py:500-506`) и в архивном design.md. Соседний блок комментариев про таблицы валидаторов (`records.py:330-339`) в том же диффе обновлён, так что расхождение именно здесь.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "4783ce19d9cd51f6646caea80bc4882172a0e085", "verdict": "approved", "findings": [], "advisory_findings": ["CHK-001"]}
AGENTMARSHAL_VERDICT_END
