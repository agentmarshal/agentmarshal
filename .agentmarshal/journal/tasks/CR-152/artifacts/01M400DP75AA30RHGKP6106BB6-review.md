Разобрал контракт, дельту спеки, опубликованную спеку и код парсера. Запустить CI не смог: в снапшоте нет `.venv`, а `pytest`/`mypy`/`python -c` требуют подтверждения, которое в неинтерактивной сессии не выдаётся. Поэтому проверка статическая — читал `src/agentmarshal/journal/extensions.py`, `tests/test_extensions.py`, `contracts.py`, `records.py` и ADR-0013/0022 целиком.

Что сошлось:

- Все 26 сценариев дельта-спеки имеют тест с docstring, дословно повторяющим заголовок сценария. Проверил поимённо.
- Парсер совпадает с примером манифеста ADR-0013 (`docs/adr/ADR-0013-...:311-341`) по всем полям, включая `runtime = "node >= 20"` и `kinds = ["openspec/change-archived@1"]`; форма kind соответствует ADR-0022:162.
- Лестница схем: `schema not in {1, 2}` → unknown; пять schema-2 ключей в schema 1 → `requires schema 2`; порядок вычисления schema-1 полей (`version`, `install`, `remove` после scope-валидации) сохранён ровно как раньше, так что «schema 1 парсится как прежде» держится.
- Контрольные символы: `\u202e`, `\u200e`, `\u2028`, `\u000b`, `\u001b` все попадают в `_FORGEABLE_CATEGORIES`/`_BIDIRECTIONAL_CONTROLS` (`records.py:816-827`), так что тесты на free-text реально что-то ловят, а не проходят вхолостую.
- `_PLAIN_PATH` и `_ENV_NAME` собраны корректно (дефис в конце класса — литерал, диапазона не образуется); `_RECORD_KIND` не пропускает ни `openspec/@1`, ни `openspec/change@1@2`.
- Новые поля никто не читает: `brief.py:232`, `review.py:1071,1247`, `gate.py:820` берут только `.documents`/`.footprint`; фикстуры gate в диффе не тронуты. `install`/`remove`, ставшие `str | None`, нигде вне парсера не используются.
- Архив оформлен как у соседних изменений (`design.md`, `proposal.md`, `tasks.md`, `specs/`, `.openspec.yaml`), Purpose в опубликованной спеке написан, а не оставлен placeholder'ом.

Теперь по замечаниям.

**mypy-literal-narrowing-unverified** — в `src/agentmarshal/journal/extensions.py:236` `phase` имеет тип `str` (результат `_require_string`), и после `if phase not in _STAGE_PHASES: raise` он передаётся в поле `ExtensionStage.phase: ExtensionPhase`; то же самое в `_parse_isolation` (`extensions.py:340` → `ExtensionIsolation.writes: ExtensionWrites`). Исторически mypy сужает тип по оператору `in` только для отбрасывания `None`, а `str` → `Literal[...]` не сужает — в этом случае `uv run mypy` под `strict = true` упал бы с `arg-type`, и acceptance-критерий про прохождение CI не выполнился бы. Проект пинит mypy 2.3.0 (`uv.lock:152`), поведение которого я подтвердить не могу: исходников mypy в окружении нет, запуск заблокирован. Помечаю как advisory — нужно просто показать вывод `uv run mypy`; если он чистый, замечание снимается, а если нет, лечится `cast(ExtensionPhase, phase)` или сравнением через явные литералы.

**adr-example-ellipsis-in-footprint** — в `tests/test_extensions.py:333` тест `test_adr_0013s_manifest_example_parses` копирует из ADR строку `footprint = ["openspec/", "..."]`, где `"..."` — это многоточие-заглушка в документации, а не путь. Запись проходит `validate_scope_entry` (три точки не равны `.` или `..`), так что тест зелёный, но он заодно фиксирует как ожидаемое поведение приём литерального `"..."` в качестве scope-entry. Тест не ломается, просто фикстура вводит в заблуждение — лучше подставить второй настоящий путь.

Блокирующих дефектов не нашёл.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e16cfd3e6b96ed2265434407f8c617f18983ea9d", "verdict": "approved", "findings": [], "advisory_findings": ["mypy-literal-narrowing-unverified", "adr-example-ellipsis-in-footprint"]}
AGENTMARSHAL_VERDICT_END
