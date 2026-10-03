Разобрал контракт, ADR-0015, весь `records.py`, новые тесты и пути чтения/записи. Блокирующих дефектов не нашёл.

Что проверил по существу:

- **Порядок правил идентичен старому** `_validate_record` — все 23 проверки на месте, 21 правило в реестре в том же порядке, что и в if/elif-цепочке; сессионные проверки разрезаны ровно по старым границам, так что первое сообщение об ошибке у битой записи не меняется.
- **Write-side эквивалентен прежнему**: `for_write=True` отключает фильтр по таблице, внутренние guard'ы (`schema >= 2` в provenance, `< 4` / `< 5` / `< 6` в гейтах) сохранены, поэтому ни одна запись, которая писалась раньше, не отвергается, и ни одна, которая отвергалась, не проходит.
- **Read-side только ослаблен** (подмножество правил), значит `agentmarshal validate` на журнале репозитория не может сломаться, а все проверки на forgeable-text (`_reject_control_characters` внутри правил `review`/`acceptance`/`finding`, привязанных к 1) по-прежнему применяются на чтении — регрессии безопасности из риска design.md нет.
- **Все пути записи** (`write_record` → `validate_record_for_write`, gate → `validate_record_content`, backfill, migrate) — write-side; единственный read-путь — `read_records` (status, gate'овое чтение журнала). Прямых `json.load` по записям вне `records.py` нет.
- **Штампы схем совпадают с прежними** для всех девяти `create_*` и `session_record_schema`; `write_record` пишет с `sort_keys=True`, так что перенос `"schema"` в конец словаря не меняет байты файлов.
- Все 7 сценариев дельта-спеки покрыты тестами, чьи docstring их называют; архив и `openspec/specs/record-schema/spec.md` соответствуют конвенции остальных изменений.

Запустить `pytest`/`ruff`/`mypy` в этой песочнице не смог (нет `uv`, запуск интерпретатора заблокирован), поэтому прохождение CI проверено только статически — об этом говорю прямо.

Замечания, не блокирующие:

Утверждение `assert "schema-version" not in records_module._RULES` в `tests/test_record_schema.py:72` проверяет строку-имя, которой в production-коде нет ни в одном месте, поэтому обещание design.md «the completeness test asserts it stays out of both structures» выполнено лишь номинально: регистрация schema-проверки как правила под её настоящим именем тест не поймает.

В `tests/test_record_schema.py:86-88` ветка `AssertionError` недостижима — у записи `{"record_type": "opened"}` ключа `schema` нет, так что `data["schema"]` упадёт `KeyError`, и заявленный режим отказа «a rule read the schema before it was checked» никогда не срабатывает (сам тест регрессию порядка всё же ловит, но посторонним исключением).

Сообщение на пути чтения для review-записи с `reviewed_contract` ниже схемы 5 меняется с «requires schema 5» на «record has unsupported fields: reviewed_contract»; design.md это фиксирует осознанно, но сценарий «the field requires the schema that allows it … with a message naming the field and the schema it requires» в `openspec/specs/review-evidence/spec.md:124-128` теперь верен только для write-side, и это сужение нигде, кроме архивного design.md, не записано.

`read_records` продолжает делать read-time проверки над полями записи, у которых нет записи в таблице — `validate_task_id`, `_RECORD_FILENAME_PATTERN`, сверка `record["task"]` с каталогом и `record["record_type"]` с именем файла (`src/agentmarshal/journal/records.py:1291-1336`); критерий 2 формулировкой «each check that record validation makes on a record type, a field or a field's value» их в принципе задевает, и, в отличие от schema-проверки, design.md не объясняет, почему они остаются вне таблицы.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "078551b1c58250e2c60805668e10bbcf979f13cb", "verdict": "approved", "findings": [], "advisory_findings": ["vacuous-schema-version-assertion-in-completeness-test", "unreachable-assertion-branch-in-schema-ordering-test", "read-side-reviewed-contract-message-divergence-not-recorded-in-review-evidence-spec", "read-time-checks-in-read-records-outside-the-rule-table"]}
AGENTMARSHAL_VERDICT_END
