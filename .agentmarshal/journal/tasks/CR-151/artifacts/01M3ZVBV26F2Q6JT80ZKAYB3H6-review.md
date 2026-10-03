Проверил контракт, delta spec, published spec, реализацию и тесты. Запустить CI не смог — выполнение `uv run pytest` / `ruff` / `mypy` в этой сессии заблокировано разрешениями, поэтому acceptance «the full CI sequence passes» я проверить не мог; разбор ниже статический (по совпадению сообщений, счётчиков проверок doctor и правил ruff/mypy из `pyproject.toml` всё сходится).

Что сделано корректно:
- `openspec/changes/archive/2026-10-03-project-settings-0-5-0/` содержит proposal, design, tasks, delta spec и `.openspec.yaml` — по той же конвенции, что и соседние архивы; published `openspec/specs/project-settings/spec.md` совпадает по формату с остальными (`# <cap> Specification` / `## Purpose` / `## Requirements`), в `openspec/changes/` не осталось неархивированного каталога.
- Все 11 сценариев delta spec покрыты тестами, чьи docstring называют сценарий дословно (7 в `tests/test_settings.py`, 4 в `tests/test_doctor.py`).
- Дефолты совпадают с ADR-0016 decision 3/4 и ADR-0022 §6 посимвольно; `other` разрешён и обоснован в design.md, как и требует контракт.
- `bool` отсекается до `int` (`src/agentmarshal/settings.py:116`), control-characters проверяются общим `forges_rendered_text` (TAB — категория `Cc`, так что тест-кейс `tab-entry` действительно сработает).
- Настройки читает только `doctor` — больше ни один модуль не импортирует `agentmarshal.settings`; счётчики проверок doctor обновлены согласованно (10 OK; 6 FAIL + 2 TODO в decode-error тесте), `tests/test_cli.py:35` на новое число не опирается.

Блокирующее:

JSON-значение `null` трактуется как отсутствующее: `_section` в `src/agentmarshal/settings.py:69` и три проверки `value is None` (`:82`, `:115`, `:129`) используют `None` как признак отсутствия ключа, поэтому `{"review": null}`, `{"review": {"finding_classes": null}}` и `{"contract": {"require_agreement": null}}` молча отдают дефолт вместо ошибки — то есть present-but-malformed значение подменяется дефолтом, что acceptance-критерий запрещает прямо, а delta spec требует «a section that is not an object is named» (JSON `null` — не объект) и «review.finding_classes is present and is not a non-empty list → raises». Это противоречит и собственному design.md: «Absent — no section, or a section without the key — returns the default», тогда как `"review": null` — ни то, ни другое. Отличать нужно по `name not in project` / `key not in section`, а не по `is None`; ни один тест этот случай не покрывает, поэтому дыра и не всплыла.

Советами:

design.md (строка 46) утверждает «The malformed value itself is never printed», но `_finding_classes` подставляет само значение в два сообщения — `src/agentmarshal/settings.py:90` и `:95` (`entry!r`); подделать вывод это не даёт, потому что `repr` экранирует `Cc`/`Cf`, но заявление в design расходится с кодом.

В `tests/test_settings.py:65` ключ `require_agreement` положен внутрь секции `review`, а не `contract`, и флаг в этом сценарии не проверяется (`:70` утверждает только threshold), так что вторая половина сценария «an absent key falls back beside present ones» не проверяет fallback флага и документирует несуществующее размещение ключа.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "fbf6fae52a919ebde6680a0b297de0aaf47e89b1", "verdict": "changes_required", "findings": ["settings-json-null-read-as-absent"], "advisory_findings": ["design-claims-malformed-value-never-printed", "fallback-test-misplaces-require-agreement"]}
AGENTMARSHAL_VERDICT_END
