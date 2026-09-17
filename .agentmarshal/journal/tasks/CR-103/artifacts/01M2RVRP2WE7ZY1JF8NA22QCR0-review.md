Проверил diff против контракта, ADR-0005, delta-спеки и кода в снапшоте.

**Что сходится.**

- Оба новых сценария из `openspec/changes/archive/2026-09-18-bounded-leak-scan-output/specs/leak-scan/spec.md` закрыты тестами, чьи docstring их называют: `tests/test_gate.py:1806` и `tests/test_leak_scan.py:63`. Остальные сценарии того же MODIFIED-требования уже имели такие тесты (`tests/test_capture.py:242,336,354,375,488`, `tests/test_gate.py:1774`), и текст требования в архивной дельте посимвольно совпадает с `openspec/specs/leak-scan/spec.md:11-67`.
- Граница действительно переехала к вызывающему: `_LEAK_HIT_RENDER_LIMIT = 20` живёт в `src/agentmarshal/journal/gate.py:62`, `_RENDER_LIMIT` из `capture.py` удалён без остатка (`grep` даёт только новую константу), `src/agentmarshal/cli.py:1309` передаёт `limit=None`. Гейтовый тест на 21 файле пинит именно двадцатку поведенчески (`, and 1 more not shown`), а `test_the_merge_boundary_reports_the_same_detail` по-прежнему пинит строку гейта байт-в-байт для одного попадания — то есть 20 нельзя поменять молча.
- Рендерер один (`render_leak_hits` в `src/agentmarshal/journal/capture.py:324`), формат попадания ни у гейта, ни у команды своей копии не имеет — единственное, что различается, это `limit`.
- `docs/sidecar.md:245-253` описывает строку ровно так, как её ждёт `tests/test_gate.py:1797` (`(advisory, not blocking): <file>: <what matched>`), включая `leak-scan skipped (<reason>)` из `gate.py:1181`. Других мест в `docs/`, описывающих старую форму, не осталось.
- `LaunchedReview` в `__all__` (`src/agentmarshal/journal/__init__.py:45`, порядок сортировки не нарушен) и пинится `tests/test_journal.py:94`.
- Противоречий с ADR-0005 нет: ADR говорит о том, что скан best-effort и advisory, про объём вывода не высказывается; всё изменённое лежит внутри scope контракта.

Одно необязательное замечание: `render_leak_hits` в `src/agentmarshal/journal/capture.py:337` теперь принимает произвольный `limit`, но не проверяет его — при `limit=0` `rendered` пустая, и функция возвращает строку, начинающуюся с запятой (`", and 25 more not shown"`). Ни один текущий вызывающий так не делает, поэтому это скрытая, а не живая, шероховатость публичного уже-параметризованного хелпера.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "0ca8c9de586dc34434d9651f84dbc58524721c06", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-RENDER-LIMIT-ZERO-LEADS-WITH-A-COMMA"]}
AGENTMARSHAL_VERDICT_END
