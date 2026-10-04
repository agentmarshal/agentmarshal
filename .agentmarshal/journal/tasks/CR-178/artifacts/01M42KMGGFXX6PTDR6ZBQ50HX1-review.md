## Что я проверил

**Выполнить не удалось:** `uv run pytest`, `ruff`, `mypy` — sandbox отклонил запуск (`This command requires approval`). Поэтому проверка статическая; по полной CI-последовательности опираюсь на утверждение координатора.

**Прочитал:** `records.py` (`_SCHEMA_7_REVIEW_FIELDS` и запись в `_FIELD_FAMILIES:419`, `_check_fields:541`, `_validate_review_record:1542`, `_check_review_fields_7:1042`, `_minimum_schema:1991`, `create_review_record:2245`, таблицы `_FORGEABLE_TEXT_FIELDS:485`, `_RULE_FROM_SCHEMA:1441`), новый `tests/test_review_verification_and_evidence.py` целиком, добавленные кейсы в `tests/test_record_schema.py`, правку `tests/test_review_links_and_classes.py:434`, архивную папку изменения (proposal / design / tasks / delta), `openspec/specs/review-evidence/spec.md`, `openspec/specs/record-text-safety/spec.md`, ADR-0017 решения 4–5, ADR-0022 раздел 2 (строки 124–125), `attestation.py`.

**Сходится:** форма обоих полей совпадает с ADR-0022 строками 124–125 и ADR-0017; все 20 сценариев delta имеют тест, чей docstring их называет; регистрация идёт через тот же `_FIELD_FAMILIES`-вход, то же `_minimum_schema`-условие и то же правило `review-fields-7` (второго механизма нет); ниже 7 оба поля ловит правило `fields`, привязанное к 1, — на запись и на чтение; в `src/` ничего, кроме `records.py`, не изменилось, fixtures не тронуты; MODIFIED действительно не нужен — требование «The link, the classes and the reviewer actor are fields of schema 7» не утверждает, что семейство исчерпывается этими полями, и остаётся верным. Ключи `evidence` безопасны по построению: они обязаны присутствовать в `findings`/`advisory_findings`, а те уже проходят `_reject_control_characters` в правиле `review`, которое выполняется раньше.

## Замечания (не блокирующие)

**ADV-CLASSES-REFUSAL-DRIFT** — вынос проверки ключей в `_check_review_keyed_field` (`src/agentmarshal/journal/records.py:1121`, вызов для `classes` на `:1060`) незаявленно изменил уже отгруженное поведение `classes`: текст отказа был `review record 'classes' key must name a finding id…`, стал `review record 'classes' key '<id>' must name a finding id…`, и порядок отказов перевернулся — раньше цикл шёл ключ-значение попарно, теперь все ключи проверяются до всех значений, поэтому для `classes` вида `{валидный_id: 5, невалидный_id: "x"}` вместо отказа по значению теперь приходит отказ по ключу. Ни в proposal, ни в design, ни в delta это не объявлено.

**ADV-VERIFICATION-SECTION-TABLE-SPLIT** — `_VERIFICATION_SECTIONS` (`src/agentmarshal/journal/records.py:267`) дублирует набор секций, который уже назван в `_VERIFICATION_ENTRY_KEYS:268`, а `_validate_verification_section:1146` берёт `_VERIFICATION_ENTRY_KEYS[section]` без защиты: секция, допущенная frozenset'ом, но отсутствующая в словаре и не равная `"read"`, даст `KeyError` вместо `JournalRecordError` — то есть падение вместо отказа, тогда как весь модуль построен на fail-closed. Сегодня это недостижимо (секций ровно три), но шов остаётся; `frozenset({"read", *_VERIFICATION_ENTRY_KEYS})` его закрывает.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5014c4ebf5dbf5e6900f2fb13eb5a60a93f1d901", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-CLASSES-REFUSAL-DRIFT", "ADV-VERIFICATION-SECTION-TABLE-SPLIT"]}
AGENTMARSHAL_VERDICT_END
