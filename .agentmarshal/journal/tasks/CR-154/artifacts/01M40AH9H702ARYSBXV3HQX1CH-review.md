Прошёл по диффу и по файлам на ревьюируемом коммите: `records.py`, `attestation.py`, `status.py`, оба теста, дельта-спек и смёрженный `openspec/specs/record-schema/spec.md`, плюс ADR-0022 §2/§3/§8 и все call-site'ы реестра (`gate.py`, `complete.py`, `status_view.py`, `test_journal.py`, `test_gate.py`).

Что проверил по критериям приёмки:

- **Схема 7 известна, но не штампуется.** `_SUPPORTED_SCHEMAS = {1..7}`; `_minimum_schema` не тронут (топ — 6), и `max(_SUPPORTED_SCHEMAS)` нигде в продакшене не используется как штамп — грепнул, единственный потребитель `_HIGHEST_SCHEMA` это тесты. `test_unknown_schema_is_rejected` переехал на 8 и теперь пинит отказ и на write, и на read.
- **Один реестр.** `PREDICATE_TYPES`, `_RECORD_TYPE_STATES`, `_TERMINAL_RECORD_TYPES`, `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, `_WRITABLE_RECORD_TYPES` — все comprehension'ы над `RECORD_TYPES`; `WritableRecordType` остался `Literal` и пинится через `get_args`. Все пять атрибутов реально запинены литералами (включая per-type множества через цикл по парам `(тип, терминальное состояние)`), так что синхронный дрейф реестра и вывода тест не пропустит.
- **Поведение 1–6 не изменилось.** Единственный содержательный сдвиг — требование recorder'а у `finding` переехало с правила `finding` (позиция 11) на `recorded-by` (позиция 20). Оба правила привязаны к схеме 1 и применяются и на read, и на write, так что множество принимаемых/отвергаемых записей то же; меняется только, какое сообщение выигрывает, если запись падает ещё и на более раннем правиле. Текст сообщения для `finding` побайтово тот же (f-строка даёт `finding record requires ...`). Флаг `writable` у всех девяти типов `True`, поэтому новая проверка в `_validate_record` и смена `_RECORD_TYPE_STATES` → `_WRITABLE_RECORD_TYPES` в `load_task_for_record` ничего не отвергают заново. `record_type_is_admitted_after_terminal` сохраняет отказ для неизвестного типа вместо `KeyError` за счёт предварительной проверки членства.
- **Четвёртый валидатор** (`bounded-text-bytes`) идёт сверх трёх, перечисленных в строке acceptance, но ровно совпадает с четырьмя лимитами из Context контракта и из ADR-0022 §8 (`excerpt` 4 KiB — байтовая мера), так что это не расширение объёма.
- Все сценарии дельты имеют тест, чей docstring их называет; `MODIFIED`-заголовок и три прежних сценария сохранены дословно, новый добавлен.

Блокирующих дефектов не нашёл. Три замечания по качеству, не блокирующие:

Комментарий над `_RULES` в `src/agentmarshal/journal/records.py:216` всё ещё утверждает, что «every rule that exists today applies from schema 1 … except the field gates already bound to schemas 2, 4, 5 and 6» — после этой задачи четыре правила привязаны к 7; спек обновлён («Every rule that existed before schema 7 …»), а этот комментарий — нет, хотя второй блок на строке 650 про 7 говорит.

Предикат выборки регистраций `if (only_type is not None and record_type != only_type) or field not in data: continue` продублирован дословно в трёх телах правил — `_check_text_limits` (`src/agentmarshal/journal/records.py:591`), `_check_bounded_json` (:621) и `_check_forgeable_text` (:639); один генератор `(field, limit)` по таблице объединил бы все четыре правила так же, как `_check_text_limits` уже объединил две текстовые границы.

Docstring `_validate_recorded_by` (`src/agentmarshal/journal/records.py:1042`) по-прежнему описывает функцию как «check the pair is well-formed and never half-present», хотя теперь она же несёт перенесённое из `_validate_finding_record` требование recorder'а по флагу типа — то есть самую интересную часть своей новой ответственности не документирует.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "f0507981fd8a709a290f907a86d557956f5b1ebd", "verdict": "approved", "findings": [], "advisory_findings": ["stale-rules-comment-omits-schema-7-bindings", "duplicated-registration-filter-across-three-rules", "validate-recorded-by-docstring-omits-type-flag"]}
AGENTMARSHAL_VERDICT_END
