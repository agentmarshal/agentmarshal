Я изучил патч, спеку, контракт, ADR-0013/0022 и конфигурацию CI. Выполнить тесты и mypy в этой песочнице не удалось (`uv`, `mypy`, `ruff` недоступны, запуск `python3` заблокирован), поэтому проверка статическая — но один пункт разбирается однозначно по типам.

## Разбор

Парсер в целом точно повторяет пример манифеста из ADR-0013 (строки 311–342 ADR-а) — секции, имена полей и форма `runtime` совпадают до символа. Лестница схем сделана в том же стиле, что и у contract header (`contracts.py:198,204` — та же формулировка «requires schema N»). Все 26 сценариев delta-спеки действительно покрыты тестами с docstring-ами, имена совпадают один-в-один. Архив (`.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`, `specs/extension-manifest/spec.md`) и собранная спека по структуре совпадают с прочими 22 архивами. Читатели новых полей не появились: во всём `src/` `install`/`remove`/`artifacts`/`record_kinds` не читает никто, `gate.py` берёт из манифеста только `footprint` и `documents`, так что смена типа `install: str` → `str | None` ничего не ломает, а fixtures гейта не тронуты. Форматирование тоже сходится: самая спорная строка (`lock = _require_directory_file(...)` в `_parse_wraps`) в одну строку даёт 89 символов при `line-length = 88`, то есть `ruff format` её корректно оставляет разбитой.

Ниже — то, что я считаю проблемой.

**mypy-strict-rejects-str-to-literal** — в `src/agentmarshal/journal/extensions.py:238` в `ExtensionStage(phase=phase, ...)` передаётся `phase`, полученный из `_require_string` (строка 230) и имеющий тип `str`, тогда как поле объявлено как `ExtensionPhase = Literal["post-gate", "pre-gate-warn", "pre-gate-stop"]`; то же в строке 342, где `writes` из `_require_string` (строка 327) идёт в поле типа `ExtensionWrites`. Сужение делается проверкой `phase not in _STAGE_PHASES` / `writes not in _WRITES_MODES`, а mypy для оператора `in` сужает только `None` (в `checker.py` это прямо закомментировано как «we only try and narrow away 'None' for now») и никогда не сужает `str` до `Literal` — тем более когда правый операнд не литеральный tuple, а переменная типа `tuple[ExtensionPhase, ...]`. При `strict = true` и шаге CI `uv run mypy` это два `arg-type` error, то есть последний пункт acceptance («the full CI sequence passes») не выполняется. Показательно, что в этом же репозитории ровно такой переход делается через `cast`: `tests/test_journal.py:2728` — `cast(WritableRecordType, "sessions")`. Лечится либо `cast(ExtensionPhase, phase)` / `cast(ExtensionWrites, writes)`, либо явным сравнением с литералами, либо словарём `dict[str, ExtensionPhase]`.

**wraps-runtime-name-unconstrained** (advisory) — в `src/agentmarshal/journal/extensions.py:268-274` поле `[wraps].runtime` проверяется только на control characters и на «три whitespace-разделённых токена с `>=` посередине», поэтому `runtime = "../../bin/sh >= 1"` или `runtime = "a/b >= 20"` проходит. ADR-0013 (строка 331) называет runtime единственным исключением для `PATH`, то есть первый токен позже уйдёт именно в PATH-lookup, и сейчас он может быть путём с `..`, а не именем программы. Для текущей задачи это не нарушение спеки (она требует только форму), но ограничить `<name>` алфавитом вроде `_PLAIN_PATH` без `/` и `.` дешевле сейчас, чем в задаче про запуск stage-ов.

Остальное, что я проверял и считаю корректным: `bin/` и `lock/` закрывают абсолютный путь, `..`, пустой компонент, bare program name, пробелы и shell-метасимволы (`validate_scope_entry` + `_PLAIN_PATH` + проверка первого компонента); `network`/`timeout_seconds` сужаются через `type(x) is bool`/`is int`, поэтому `network = 1` и `timeout_seconds = true` отвергаются; `_RECORD_KIND` с `fullmatch` допускает ровно один `/` и один `@`; порядок проверок для schema 1 сохранён, так что сообщения об ошибках для старых манифестов не поехали.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "e16cfd3e6b96ed2265434407f8c617f18983ea9d",
  "verdict": "changes_required",
  "findings": ["mypy-strict-rejects-str-to-literal"],
  "advisory_findings": ["wraps-runtime-name-unconstrained"]
}
AGENTMARSHAL_VERDICT_END
