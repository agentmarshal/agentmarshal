Прошёлся по контракту, дельта-спеке, ADR-0005 и коду в снапшоте. Исполнить тесты в этой песочнице нельзя (`python`/`pytest` требуют approval), поэтому проверка — статическая: чтение кода, тестов и документов.

Что сходится:

- `render_leak_hits` (`src/agentmarshal/journal/capture.py:324`) берёт `limit: int | None`, форма хита осталась одна на обоих вызывающих; ни gate, ни CLI своей копии `f"{path}: {identification}"` не заводят — критерий 3 выполнен.
- Число двадцать переехало в `src/agentmarshal/journal/gate.py:62` как `_LEAK_HIT_RENDER_LIMIT` с комментарием, объясняющим, почему бод принадлежит транскрипту; `_run_leak_scan` (`src/agentmarshal/cli.py:1309`) передаёт `limit=None` — критерий 2 выполнен, и это ровно то, что записано в design.md как принятое решение.
- Все восемь сценариев дельта-спеки закрыты тестами с называющими docstring: шесть прежних в `tests/test_capture.py` и `tests/test_gate.py:1779`, два новых — `tests/test_gate.py:1809` и `tests/test_leak_scan.py:66`. Критерий 1 выполнен.
- Дельта-требование перенесено в `openspec/specs/leak-scan/spec.md:25` дословно, включая оба новых сценария; архив лежит по той же конвенции, что и соседние (`.openspec.yaml`, `design.md`, `proposal.md`, `specs/`, `tasks.md`).
- `LaunchedReview` добавлен в импорт и в `__all__` журнального пакета на алфавитной позиции, пин — `tests/test_journal.py:94`. Критерий 5 выполнен.
- Противоречия с ADR-0005 нет: скан остаётся advisory и не блокирует, секрет по-прежнему не попадает ни в одну из веток вывода.
- Все затронутые пути внутри scope; `render_leak_hits` не экспортируется из `agentmarshal.journal`, так что обязательный параметр не ломает публичный API.

Advisory-замечание одно: в `docs/sidecar.md:249-251` строка гейта описана так, будто суффикс присутствует всегда — «shows the first twenty hits and ends `, and N more not shown`», тогда как `render_leak_hits` добавляет его только при `remaining > 0`, и собственный тест гейта `test_the_merge_boundary_reports_the_same_detail` (`tests/test_gate.py:1779`) ожидает строку с одним хитом и без этого хвоста. Форма самого предупреждения (`<file>: <what matched>`) описана верно, поэтому критерий 4 по существу выполнен — не хватает только слова «если хитов больше двадцати».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "4a97254fe0fbbc36f20d24e1900204bae4ea7abd", "verdict": "approved", "findings": [], "advisory_findings": ["sidecar-doc-states-the-count-suffix-unconditionally"]}
AGENTMARSHAL_VERDICT_END
