Проверил диff целиком: прочитал `records.py`, `status.py`, `attestation.py`, оба затронутых тест-файла, `openspec/specs/record-schema/spec.md`, архивный delta, ADR-0022 и всех потребителей реестра (`gate.py:760`, `test_gate.py:1940`, `test_journal.py:2728`). Запустить `pytest`/`ruff`/`mypy` в этой песочнице не удалось — Bash отказал в доступе к интерпретатору и к `uv`, так что результаты проверок из `tasks.md` 4.2 я не подтверждал исполнением, только статическим разбором.

По существу контракта всё сходится. Схема 7 добавлена только в `_SUPPORTED_SCHEMAS` (единственный потребитель — `_check_schema_version`), `_minimum_schema` не тронут, так что ни один `create_*` 7 не ставит. Производные таблицы в `status.py` дают ровно прежние значения: `_TERMINAL_RECORD_TYPES == {completed, abandoned}`, `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL == {session, reopened}`. Новая реализация `record_type_is_admitted_after_terminal` расходится со старой лишь при `terminal_state` вне `{done, abandoned}` (ветка `state or ""` в `project_status:111`), а она недостижима: `has_terminal_record` поднимается только на `completed`/`abandoned`, каждый из которых тут же проставляет `state`. Перенос требования recorder'а с `_validate_finding_record` на флаг даёт идентичный текст ошибки и идентичный accept/refuse — меняется только приоритет сообщения у записи, сломанной ещё и по `provenance`, что design.md признаёт прямо. Все 14 сценариев delta покрыты тестами, чьи docstring их называют.

Теперь то, что стоит отметить.

Таблицы регистрации валидаторов в `src/agentmarshal/journal/records.py:285-287` ключуются только именем поля, без измерения «для какого типа записи» — в отличие от `_FIELD_FAMILIES:265`, у которого слот `only_type` есть именно для этого. ADR-0022 §8 требует `reason` в 1000 символов **только в новых типах записей** («The existing `reason` fields are untouched»), а `reason` — существующее поле `abandoned`, `reopened`, `amendment` и `acceptance`. Зарегистрировать `_TEXT_CHAR_LIMITS["reason"] = 1000` для `acknowledgement` не получится, не ограничив попутно существующие `reason` на write-пути (там применяются все правила независимо от схемы), так что обещание «каждая следующая задача только регистрирует поле и больше ничего» для `reason` не выполнится.

Флаг `writable` в `src/agentmarshal/journal/attestation.py:46` объявлен, но в продакшене его никто не читает: рантайм-страж в `src/agentmarshal/journal/status.py:159` по-прежнему проверяет членство в `_RECORD_TYPE_STATES`, а не в наборе writable-типов. Сегодня это эквивалентно (все девять типов writable), но тип с `writable=False` страж пропустит — ровно та щель, которую реестр должен был закрыть.

Проверки производных таблиц в `tests/test_attestation.py:91-115` тавтологичны: `expected_predicates`, `expected_states`, `expected_terminal` и `expected_after_terminal` вычисляются тем же comprehension, что и сами таблицы в продакшене, поэтому пройдут при любом общем сдвиге. Силу имеют только пин `WritableRecordType` (строка 116) и цикл по `record_type_is_admitted_after_terminal` (117-121). Утверждение design.md, что «the pinning test asserts the exact values, not just the keys», для производных таблиц преувеличивает.

`_check_forgeable_text` в `src/agentmarshal/journal/records.py:602` обходит `_FORGEABLE_TEXT_FIELDS` — frozenset, порядок итерации которого по строкам меняется от процесса к процессу. Когда зарегистрируют два и более поля и запись нарушит оба, текст отказа станет невоспроизводимым между запусками. Остальной код здесь аккуратен (`", ".join(sorted(...))` в `_check_fields`, `_check_session_fields`, `_validate_recorded_by`), а соседние `_TEXT_CHAR_LIMITS`/`_JSON_BYTE_LIMITS` — dict'ы с детерминированным порядком.

Ни одна из четырёх не блокирует: явные пункты acceptance выполнены, поведение схем 1–6 не меняется, фикстуры гейта не тронуты.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "1355e7ba80cd11f3847b0df5441df02b7d1ae599",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "validator-tables-lack-record-type-scope",
    "writable-flag-has-no-production-reader",
    "registry-derivation-test-is-tautological",
    "forgeable-text-field-order-nondeterministic"
  ]
}
AGENTMARSHAL_VERDICT_END
