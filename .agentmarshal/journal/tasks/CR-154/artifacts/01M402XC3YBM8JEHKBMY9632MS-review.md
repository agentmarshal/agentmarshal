Разобрал диф против контракта: прочитал `records.py`, `attestation.py`, `status.py`, оба теста, дельту спеки и применённую спеку, а также затронутые читатели реестра (`gate.py`, `validate.py`, `test_journal.py`, `test_findings.py`). Запустить `pytest`/`ruff`/`mypy` в этой песочнице нельзя (Bash зарезан, `uv` отсутствует), поэтому пятый критерий про «полный CI проходит» проверен статически, а не прогоном.

Что сошлось:

- Схема 7 в `_SUPPORTED_SCHEMAS`, `_minimum_schema` не тронут — ни один `create_*` не ставит 7; `test_unknown_schema_is_rejected` переехал на 8 и теперь пинует отказ и на записи, и на чтении.
- Реестр `RECORD_TYPES` в `attestation.py` объявляет все пять атрибутов; `PREDICATE_TYPES`, `_RECORD_TYPE_STATES`, `_TERMINAL_RECORD_TYPES`, `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, `_WRITABLE_RECORD_TYPES` выведены из него, `WritableRecordType` пинуется тестом против литералов. Направление импортов цикла не даёт.
- Эквивалентность поведения `record_type_is_admitted_after_terminal` я проверил по вызовам: в `project_status` фолбэк `state or ""` недостижим при `has_terminal_record` (терминальная запись всегда ставит `state`), в `load_task_for_record` и в `gate.py` аргумент всегда `done`/`abandoned`. Старая и новая формулы совпадают на этом домене.
- Перенос `finding` на `requires_recorded_by`: сообщение байт-в-байт то же (`f"{record_type} record ..."` для `finding` даёт прежнюю строку), проверка стоит перед shape-проверками пары, так что полуприсутствующая пара даёт прежнюю ошибку; `test_findings.py:322` ищет подстроку и продолжит совпадать. Правило `recorded-by` привязано к 1, как и прежнее `finding` — множество отказываемых записей не изменилось, меняется только порядок сообщения на записи, уже падающей по более раннему правилу.
- `RECORD_TYPES[record_type]` в `_validate_recorded_by` не может дать KeyError: правила `record-type` и `record-type-predicate` привязаны к 1 и стоят раньше, а `PREDICATE_TYPES` теперь выводится из реестра.
- Три валидатора — отдельные записи `_RULES`/`_RULE_FROM_SCHEMA` со схемой 7, последние в порядке регистрации, таблицы в проде пусты. Все 14 сценариев дельты имеют тест, чьё docstring их называет. Строк длиннее 88 в изменённых файлах нет.

Два замечания — незблокирующие, оба про будущие регистрации, а не про сегодняшнее поведение.

`src/agentmarshal/journal/records.py:698` — `_canonical_json` вызывает `json.dumps` с дефолтным `allow_nan=True`, поэтому «значение, которое JSON не кодирует» на самом деле кодируется: `float("nan")` внутри поля даёт `NaN` (3 байта), проходит байтовую границу, и `write_record` затем пишет `NaN` в файл — невалидный JSON, который питоновский `json.loads` примет обратно, а сторонний парсер нет. Docstring теста `test_bounded_json_refuses_a_value_over_its_canonical_byte_bound` («A value JSON cannot encode is refused rather than crashing the rule») этот случай переобещает. Лечится `allow_nan=False` — тогда `ValueError` уже ловится существующим `except` и превращается в «must be a JSON value». Сейчас это латентно: ни одно продакшн-поле в `_JSON_BYTE_LIMITS` не зарегистрировано, но `payload` из ADR-0022 §3 придёт именно сюда.

`src/agentmarshal/journal/records.py:611` — `_check_forgeable_text` молча пропускает нестроковое значение, тогда как соседний `_check_bounded_text` нестроку отказывает. Для полей ADR-0022, которые несут отображаемые строки внутри структуры (`verification`, `evidence`, `classes`, `advisory_dispositions`), регистрация в `_FORGEABLE_TEXT_FIELDS` даст ноль проверок и ноль сигнала об ошибке регистрации — fail-open на уровне регистрации, а не записи. Решение задокументировано в design («the field's own shape rule owns the type refusal»), но у этих четырёх полей такого shape-правила ещё нет, и два родственных валидатора, введённых одним изменением, расходятся в позиции по fail-closed.

Блокирующего не нашёл: все пять критериев приёмки выполнены, поведение схем 1–6 на приём/отказ не изменилось, фикстуры гейта не тронуты.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1ee5272abc944e00f17e7524ea5552184d91a8af", "verdict": "approved", "findings": [], "advisory_findings": ["bounded-json-canonical-encoding-accepts-nan", "forgeable-text-silently-skips-non-string-registration"]}
AGENTMARSHAL_VERDICT_END
