Проверил диff статически по файлам в snapshot (`src/agentmarshal/journal/contracts.py`, `tests/test_journal.py`, архив change и опубликованный spec), сверил словарь правил и имена полей с ADR-0018 решение 3 и ADR-0022 раздел 5, и сопоставил все 12 сценариев delta-спеки с docstring'ами тестов.

Что сошлось:

- Поля `implementers`/`reviewers`/`independence` и четыре правила (`reviewer-not-writer`, `distinct-actor`, `distinct-vendor`, `distinct-model`) совпадают с ADR-0022 §5 дословно; порядок сохраняется (`tuple` из TOML-массива).
- `_optional_unique_nonempty_array` (`contracts.py:66`) даёт ровно заявленные отказы: отсутствует → `()`, пустой список → «must name at least one entry», повтор → «repeats entry», пустая запись → «entry '' is empty», не-строка → «must be an array of strings» из `_require_string_array`, и каждая запись проходит `reject_control_characters`, то есть тот же предикат `forges_rendered_text`, что и записи журнала. U+2028 (Zl) и U+200F (bidi) действительно в наборе `records.py:498-509`, так что оба параметра control-char теста отказываются там, где тест ожидает.
- Лестница схем держится: `{1, 2, 3}` в `contracts.py:190`, блок `schema < 3` наследует стиль schema-2-отказа и включает `: {source}`, существующий пример неизвестной схемы переехал на 4 (`tests/test_journal.py:166`), а других мест, где 3 считалась неизвестной, в `tests`/`src` нет.
- Все 12 сценариев спеки имеют тест с называющим их docstring; change архивирован под `openspec/changes/archive/2026-10-03-contract-header-schema-3/` вместе с `proposal.md`, `design.md`, `tasks.md` и delta, а `openspec/specs/contract-governance/spec.md` опубликован с заполненным Purpose (не placeholder), как требует AGENTS.md для новой capability.

Чего я не смог проверить: полную CI-последовательность — в этой песочнице `uv run pytest`, `uv run agentmarshal validate` и даже `python3` требуют одобрения, так что прогон не состоялся. Статически ничего, что завалило бы pytest/ruff/mypy, я не нашёл (строки в пределах 88, типы параметризаций аннотированы, новые импорты не нужны), но это вывод по чтению, а не по запуску.

Два advisory-замечания, оба в тестах/читаемости, ни одно не блокирует:

`test-relies-on-check-order-for-independence-duplicates` — `tests/test_journal.py:363` параметризует тест на повтор записи полем `independence` со значениями `['devin', 'other', 'devin']`, то есть заголовок невалиден сразу по двум причинам, и тест зелёный только потому, что проверка повтора в хелпере выполняется раньше проверки словаря в `parse_contract_text:207`; реальные имена правил (`['distinct-actor', 'distinct-vendor', 'distinct-actor']`) проверяли бы то же самое, не завися от порядка проверок.

`duplicated-schema-gate-loops` — `src/agentmarshal/journal/contracts.py:195-206` вводит второй почти дословный цикл «поле требует схему N», причём один записан как `schema == 1`, другой как `schema < 3`; при схеме 4 появится третья копия, и таблица `{2: (...), 3: (...)}` выразила бы правило ADR-0015 один раз.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "63138c550689c85175e93efcfc3bd82adce9a754", "verdict": "approved", "findings": [], "advisory_findings": ["test-relies-on-check-order-for-independence-duplicates", "duplicated-schema-gate-loops"]}
AGENTMARSHAL_VERDICT_END
