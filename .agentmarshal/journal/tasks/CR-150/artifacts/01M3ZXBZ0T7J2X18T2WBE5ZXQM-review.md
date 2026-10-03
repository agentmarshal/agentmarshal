Проверил весь diff против контракта, спеки, ADR-0020, CONTRIBUTING и существующих helpers в `capture.py`/`gate.py`. Запустить тесты в этой песочнице нельзя (`python3` заблокирован), поэтому прошёл логику статически — пересчитал каждый сценарий руками.

**Что сходится**

- Все 21 сценарий delta-спеки имеют тест, docstring которого называет сценарий дословно; change заархивирован в `openspec/changes/archive/2026-10-03-outbox-new-and-check/`, `openspec/specs/outbox/spec.md` содержит Purpose и три требования, stale `openspec/changes/outbox-new-and-check/` не остался.
- `cli.py` получил ровно hook: import, `outbox.register(subparsers)` (`cli.py:348`), ветку dispatch (`cli.py:1235`). Никакого shadowing имени `outbox` в модуле нет.
- Нумерация: прогнал `_DRAFT_NAME`/`_DATE_NAME` на всех случаях из тестов — `2026-10-03-note.md` действительно не читается как 2026, `0001-10-03-note.md` читается как 1, `0009-placed-by-hand.md` даёт 0010, `12 34 widget` → `0001-12-34-widget.md`. `O_EXCL` + монотонный счётчик не могут перезаписать файл.
- Пять полей и их hints совпадают с `CONTRIBUTING.md:38-42` символ в символ; `__version__` = то, что печатает `agentmarshal --version` (`cli.py:88-90`).
- Маскирование: каждый печатаемый `check`'ом name идёт через `safe_path` (`outbox.py:372`, `406`, и внутри `_name_hits`); `_os_error_text`/`_config_error_text` не цитируют текст исключения. `markers_from_config` оставляет `CaptureError` незавёрнутым (вызов вне `try`), поэтому порядок `except CaptureError` / `except GateError` корректен, а `JSONDecodeError` действительно доезжает как `__cause__`.
- Лossy-декод: `\ufffd` — не word-символ, поэтому `\b` в `github-token` держится вокруг токена в бинарном `blob.md`. CRLF-черновики тоже разбираются верно (`\s*$` съедает `\r` в heading, `.strip()` — в body).

**Advisory 1 — `marker-identification-format-duplicated`**

`outbox.py:289` собирает строку `f"private-marker #{index}"` заново, хотя `capture.py:661-663` уже строит её же в `scan_diff_for_leaks`. Docstring `_scan_hits` утверждает «written once here so the two callers cannot drift», и design.md в Risks пишет «there is nothing to drift» — это неточно: литерал формата живёт в двух модулях, ничего его не связывает, и ни один тест не сверяет identification `outbox check` с identification merge-боundary. При этом в `capture.py:340-341` зафиксирован прямо противоположный принцип («warning detail therefore cannot silently diverge between their two call sites»). Если формат в `capture.py` поменяют, словарь двух команд разойдётся молча. Правильнее вынести построение identification в `capture.py` рядом с `_signature_hits` и вызывать его из обоих мест, либо хотя бы добавить тест-замок.

**Advisory 2 — `non-utf8-filename-crashes-check`**

Имена в outbox приходят из `outbox.iterdir()` и на Linux декодируются через surrogateescape. Файл с именем `b"\xff.md"` даёт строку `"\udcff.md"`; `safe_path` её не меняет, и `print(f"{safe_path(entry.name, markers)}: ...")` (`outbox.py:372`/`406`) падает с `UnicodeEncodeError` на strict-UTF-8 stdout — вместо того, чтобы назвать запись. Отказ по exit status при этом формально сохраняется (uncaught exception → non-zero), но вместо отчёта оператор получает traceback, а остальные файлы батча остаются неназванными. Это расхождение с уже зафиксированной в этом же репозитории конвенцией: `openspec/specs/leak-scan/spec.md:96-97` требует, чтобы «a path whose own bytes are not UTF-8 SHALL be named in an escaped printable form». Спека `outbox` такого пункта не несёт, поэтому по контракту это не нарушение — но команда этот класс дефектов трактует как настоящий (ср. `docs/proposals/037-review-crashes-on-a-diff-that-is-not-utf-8.md`). Лечится прогоном имени через `os.fsencode(...).decode("utf-8", "backslashreplace")` перед `safe_path`.

Оба замечания не блокируют: контракт выполнен по всем пяти acceptance criteria, поведение соответствует спеке, и ни один сценарий не остался без теста.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1381fd13cd435ec4be0ace67509ca50d1db35ba8", "verdict": "approved", "findings": [], "advisory_findings": ["marker-identification-format-duplicated", "non-utf8-filename-crashes-check"]}
AGENTMARSHAL_VERDICT_END
