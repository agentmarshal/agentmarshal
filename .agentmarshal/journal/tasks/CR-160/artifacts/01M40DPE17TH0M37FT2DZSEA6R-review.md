Я прошёл по диффу, по реализации в `records.py`, по обоим опубликованным спекам и по дельте архива, и проверил ключевые инварианты на месте, а не на слово.

Что проверил предметно:

**Порядок правил и admission.** `fields` зарегистрировано в `records.py:356`, `session-fields-7` — в `records.py:536`, то есть в `_RULES` (dict, порядок вставки) field-admission идёт раньше shape-правила. Поэтому семейное поле на сессии со schema 6 даёт именно «unsupported fields», и на записи (где применяются все правила), и на чтении (`fields` привязано к 1, `_allowed_fields("session", 6)` семейство не включает). Тесты `..._refused_at_write` / `..._refused_on_read` пинят это через `match="unsupported fields"` — зависимость от порядка закреплена, а не случайна.

**`commit` без записи в `_FORGEABLE_TEXT_FIELDS`.** Аргумент design.md проверяется: `_REVIEWED_COMMIT_PATTERN.fullmatch` не пропускает ни одного символа, который отвергает forgeable-text (в т.ч. нет обхода через хвостовой `\n` — `fullmatch` требует, чтобы матч покрыл всю строку, а `$` нулевой ширины). Путь, при котором на диске лежит сессия с подделываемым `commit`, отсутствует: при schema ≥ 7 его отвергает `session-fields-7` (привязано к 7, применяется и на чтении), при schema < 7 — `fields`. Регистрация действительно никогда не могла бы сработать.

**`report_ready`.** `type(...) is not bool` отвергает `1`/`0` (в Python `isinstance(True, int)` истинно, так что `isinstance` здесь был бы дырой) — тот же приём, что у `session-tokens`. `_minimum_schema` смотрит на наличие ключа (`record.keys() & _SCHEMA_7_SESSION_FIELDS`), а `create_session_record` ставит поле по `is not None`, поэтому `report_ready=False` пишется и штампует 7; это закреплено отдельным тестом.

**Границы и длины.** ADR-0022 §8 действительно ограничивает только `excerpt` (4 KiB), `payload` (64 KiB) и `reason` новых типов — ни одно из шести полей там не названо, так что три таблицы лимитов остаются пустыми от семейства корректно. Утверждение design.md, что «non-empty после `strip()`» — та же проверка, что у `reopened`/`amendment`/`acceptance`, подтверждается: `records.py:441`, `451`, `902` используют ровно `not value.strip()`.

**Спеки.** Текст MODIFIED-требований в дельте совпадает с опубликованным в `openspec/specs/session-activity/spec.md` и `openspec/specs/record-schema/spec.md`, заголовки требований сохранены дословно. Поиск по `openspec/specs/` показывает, что schema 7 упоминается только в этих двух capability, и оба изменены; требование «Shared field validators apply from schema 7» остаётся истинным, `record-text-safety` — тоже, поскольку ни `status_view.py`, ни `report.py` не рендерят эти поля (читатели — отдельная задача по Non-Goals). Полнота таблицы правил закрыта существующим `set(_RULES) == set(_RULE_FROM_SCHEMA)` (`tests/test_record_schema.py:77`), и `session-fields-7` присутствует в обеих.

**Ничего не сломано рядом.** Шесть новых параметров keyword-only (после `*`), так что ни один существующий вызов `create_session_record` не затронут; `session_record_schema` идёт через ту же производную и остаётся на 3/6; коллизий имени `commit` с другими типами записей нет (`_FIELD_FAMILIES` ключуется на `"session"`); фикстуры гейта диффом не тронуты. Монкейпатчи в существующих тестах схемы используют `setitem`/`setattr`, поэтому непустой теперь `_FORGEABLE_TEXT_FIELDS` их не ломает, и ни один тест не утверждал пустоту таблиц.

Единственное место, где я ослабление всё же заметил — в `test_each_writer_stamps_the_minimum_schema_its_record_needs` вместо `record["schema"] < 7` осталось `type(record["schema"]) is int`; но каждая параметризация по-прежнему сверяет точное ожидаемое число (3/4/5/6/7), а сценарий «no writer stamps a schema no field needs» вынесен в отдельный тест, так что покрытие не потеряно. Блокирующих или advisory-дефектов не нашёл.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cde5766d4fa2338726b782873206bcb843173d0e", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
