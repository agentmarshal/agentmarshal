Прошёл по диффу, по обоим спекам, по `capture.py`/`gate.py`/`review.py`/`cli.py`/`project.py` и по тестам, которые они трогают.

Что проверил и что сходится:

- `scan_diff_for_leaks` разбирает `+++`-заголовки по счётчикам ханков, поэтому `+++`-строка внутри тела ханка по-прежнему считается добавленным контентом (`test_scan_diff_catches_added_line_starting_with_plus` сохраняет путь `f`), а заголовок между патчами — нет.
- Подавление self-match работает по-индексно и по-файлово: `elsewhere` пуст только когда единственные вхождения marker'а лежат в `config_path`; в sidecar-режиме оба call site передают `""`, то есть не подавляют ничего — безопасное направление, и оно совпадает у гейта (`gate.py:1145`) и у команды (`cli.py:1292`).
- `render_leak_hits` — один рендерер на оба call site, строка гейта запинена байт-в-байт в `tests/test_gate.py:1783`, и тот же тест сверяет stdout standalone-команды. Секрет отсутствует в обоих выводах.
- `safe_path` закрывает обе дыры из design.md (путь с marker'ом и путь-ключ), и `LeakHit` нигде не носит совпавший текст.
- Цикла импорта нет: `capture` → `project` → `agentmarshal/__init__` (там только `__version__`).
- `_keep_diagnostics` вызывается после `_run_reviewer` в обоих путях; `diagnostics_note` всегда связан к моменту использования после `with`-блока, `_with_diagnostics` протянут по всем поздним отказам, а `monkeypatch.setattr(review, "_preserve_reviewer_diagnostics", ...)` в тесте перехватывает нужный глобал. Запинённый транскрипт 0.3.0 (`tests/test_gate.py:409`) использует контент `"code\n"` — WARN-строки там нет, так что он не задет.
- Pathspec в README outbox'а валиден: `_scaffold_outbox` кладёт outbox в `.agentmarshal/upstream`, а `:(exclude)` без `glob`-магии матчит `**` через слэши.

Дальше — то, что нашлось.

`openspec/specs/leak-scan/spec.md:4` уехал в релиз с заглушкой архиватора вместо Purpose: «TBD - created by archiving change adopter-small-defects. Update Purpose after archive.» — при том что все шесть остальных capability-спеков в `openspec/specs/` несут написанный Purpose, а этот файл контракт называет документом задачи и держит в scope.

`tests/test_capture.py:376` — docstring пересказывает сценарий («a path that matches a built-in signature is described, not printed») вместо того, чтобы назвать его так, как он записан в спеке (`openspec/specs/leak-scan/spec.md:37`: «a path that is itself a key is described, not printed»), хотя первый acceptance-критерий требует именно «a test whose docstring names it»; трассировка спасается только именем функции.

`docs/sidecar.md:248` всё ещё описывает строку гейта как «with the markers it matched» — теперь она несёт `файл: что совпало`, и для built-in signature это вообще не marker; файл вне scope этой задачи, поэтому только advisory.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "06a9a5674ca875594daa3cc9892e45f3cb36f202",
  "verdict": "changes_required",
  "findings": ["leak-scan-spec-purpose-left-as-archiver-tbd"],
  "advisory_findings": [
    "path-is-key-scenario-docstring-does-not-name-it",
    "sidecar-doc-still-says-markers-it-matched"
  ]
}
AGENTMARSHAL_VERDICT_END
