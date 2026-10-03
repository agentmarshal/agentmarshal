Разобрал контракт, дифф, ADR-0013/0022, спеку и окружающий код. Выполнить `uv run pytest / ruff / mypy` в этой сессии не удалось (запуск команд не разрешён), поэтому критерий «полная CI-последовательность проходит» я проверял чтением, а не исполнением — об этом ниже.

Что сошлось:

- Архив на месте: `openspec/changes/archive/2026-10-03-extension-manifest-schema-2/` (proposal + design + tasks + дельта) и `openspec/specs/extension-manifest/spec.md` в формате остальных спек, Purpose не заглушка.
- Все 21 сценарий дельты покрыты тестом с docstring «Scenario: …» — проверил один к одному.
- Поля, сообщения и форма секций совпадают с примером манифеста из ADR-0013 (`phase`, `command`, `[dependencies].lock`, шесть полей `[wraps]`, `[records].kinds`, четыре поля `[isolation]`), лестница схем работает: `schema in {1,2}`, схема-2 поля под схемой 1 отбиваются до остальных проверок, `install`/`remove` опциональны только под 2.
- Новые поля никто не читает: в `brief.py`, `review.py`, `gate.py` используются только `.documents` и `.footprint`, `.install`/`.remove` не читаются нигде в `src`, фикстуры гейта не тронуты, собственный манифест репозитория остался schema 1 и парсится как раньше. Логику всех негативных тестов прогнал вручную — они должны падать именно на том поле, которое заявлено.

Блокирующее:

`mypy-literal-narrowing` — в `src/agentmarshal/journal/extensions.py:197` в `ExtensionStage(phase=phase, …)` и в `extensions.py:298` в `ExtensionIsolation(writes=writes, …)` передаётся `str` в поля типа `Literal[...]`: `_require_string` возвращает `str`, а проверка `if phase not in _STAGE_PHASES` / `if writes not in _WRITES_MODES` тип не сужает — mypy сужает левый операнд `in` только убирая `Optional`, до `Literal` он `str` не доводит (тем более что `_STAGE_PHASES`/`_WRITES_MODES` аннотированы как `tuple[..., ...]`, то есть структура кортежа литералов стёрта). В этом же репозитории ограничение уже видно: в `tests/test_journal.py:2728` строка передаётся в `WritableRecordType` только через `cast`. Значит `uv run mypy` (strict, обязательный шаг в AGENTS.md и gitflic-ci.yaml) даёт две ошибки `arg-type`, и критерий «полная CI-последовательность проходит» не выполняется. Лечится `cast(ExtensionPhase, phase)` после проверки или `TypeGuard`-хелпером. Оговорка: исполнить mypy здесь я не мог, вывод статический — проверяется одной командой.

Advisory:

`wraps-kinds-text-safety` — в `_parse_wraps` для `runtime` явно вызывается `reject_control_characters` (`extensions.py:231`), а `product`, `version`, `ecosystem`, `license` (`extensions.py:219-221,240`) и элементы `[records].kinds` такой проверки не получают: регексп `_RECORD_KIND` (`extensions.py:43`) исключает только `\s`, поэтому `\x00`, `\x1b`, bidi-控制 вроде U+202E в `<kind>`/`<version>` проходят. Границу манифеста это оставляет слабее, чем правило forgeable-text в остальном журнале (для `version`/`install` пробел унаследован от схемы 1, так что это не регрессия, а незакрытая щель, которую унаследует следующая задача).

`command-allows-spaces-and-metacharacters` — `_require_directory_file` (`extensions.py:143-164`) опирается на `validate_scope_entry`, который не отбивает пробелы и шелл-метасимволы, так что `command = "bin/x.py; rm -rf /"` или `command = "bin/validate.py --strict"` считаются валидным «файлом под `bin/`». Спеке это не противоречит (там только absolute/`..`/bare name), но заявленный смысл поля — путь, а не строка команды, и запрет дешевле добавить на границе, чем надеяться на будущий раннер.

`schema-2-still-requires-artifacts` — design.md сознательно сохраняет `artifacts` обязательным в схеме 2, но в примере wrapper-манифеста ADR-0013 (`docs/adr/ADR-0013-...md:311-341`) `artifacts` нет вовсе, то есть манифест, скопированный из ADR, этим парсером будет отвергнут. Решение задокументировано, но стоит сверить его с задачей, которая будет писать настоящий `openspec/manifest.toml`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8b41fe4b93c1148730990063d89351f55ea19898",
  "verdict": "changes_required",
  "findings": ["mypy-literal-narrowing"],
  "advisory_findings": ["wraps-kinds-text-safety", "command-allows-spaces-and-metacharacters", "schema-2-still-requires-artifacts"]
}
AGENTMARSHAL_VERDICT_END
