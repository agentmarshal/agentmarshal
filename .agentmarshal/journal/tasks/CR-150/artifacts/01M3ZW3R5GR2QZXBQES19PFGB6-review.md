Проверил контракт, delta-спеку, `openspec/specs/outbox/`, модуль и тесты по файлам в снапшоте. Выполнить CI-последовательность не смог — в этой сессии запуск `python`/`uv`/`ruff` не разрешён, так что про «full CI sequence passes» сужу только статически.

Что сошлось:

- Все 21 сценария delta-спеки имеют ровно один тест, docstring которого называет сценарий (`tests/test_outbox.py`, порядок совпадает со спекой). Опубликованная `openspec/specs/outbox/spec.md` содержит Purpose и три требования; change лежит в `openspec/changes/archive/2026-10-03-outbox-new-and-check/` с `.openspec.yaml`, как и прочие архивные changes.
- Пять полей и их подсказки дословно совпадают с блоком «Reporting a finding» в `CONTRIBUTING.md:38-42`; `--version` в `cli.py:88-90` печатает ровно `__version__`, так что Version в черновике действительно verbatim.
- `cli.py` получил только хук: импорт (`cli.py:13`), `outbox.register(subparsers)` (`cli.py:348`), ветка dispatch (`cli.py:1235`).
- Словарь находок совпадает с merge-границей: `private-marker #N` формируется так же, как в `scan_diff_for_leaks` (`capture.py:660-665`), сигнатуры идут через общий `scan_for_leaks`, рендер — общий `render_leak_hits(..., limit=None)`.
- Маскировка: каждое печатаемое имя в `check` проходит `safe_path`, путь outbox при сбое `iterdir` тоже; текст OSError сводится к `strerror`/errno, `GateError` описывается через `__cause__`. Non-UTF-8 декодируется лоссово, и `\b` в сигнатурах выживает рядом с U+FFFD — тест с `ghp_` между `\xff\xfe` и `\x80` действительно должен проходить.
- Exit status: `refused` выставляется из non-regular entry, из проблем конформности и из непустых hits; 0 печатается только в конце без них.

Ниже — непреграждающие замечания.

Содержимое `README.md` в outbox не попадает под leak scan вообще: в `src/agentmarshal/outbox.py:349-350` файл пропускается до сканирования имени и текста, хотя `outbox send` (ADR-0020, решение 4) застейджит весь каталог, то есть отредактированный адоптером README уедет с батчем непросканированным. Критерий 3 контракта сам выводит README из проверки, поэтому это не блок, но поправка к контракту («anything else in the outbox») этим местом не покрыта.

Счётчик номеров слеп к черновику, чей slug начинается с даты: `_DRAFT_NAME` (`src/agentmarshal/outbox.py:58-60`) отбрасывает `0001-12-07-crash.md` по lookahead `(?!\d{2}-\d{2}-)`, так что `outbox new "12-07 crash"` затем `outbox new "other bug"` даёт два файла с номером `0001` — перезаписи нет (O_EXCL), но заявление design.md «name order stays creation order» в этом случае не держится, тогда как design.md называет цену нулевой.

В ветке `except CaptureError` (`src/agentmarshal/outbox.py:325-327`) печатается `{error}` — текст исключения, чего design.md обещает не делать («no exception's text is printed»); пути там нет (сообщения `private_markers_from_project` фиксированные), поэтому утечки нет, но инвариант в документе и код расходятся.

В `src/agentmarshal/outbox.py:265` условие `body == "" or body == _placeholder(field)` — это пара сравнений одного и того же имени; `body in ("", _placeholder(field))` короче и гарантированно вне подозрений ruff SIM109 (включён через `select = ["SIM"]`). Проверить `ruff check` я не смог; идентичный паттерн уже живёт в `tests/test_review_launcher.py:1355` без noqa, так что это скорее упрощение, чем падение линтера.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "86df95385a263b87ad97a36c2b6e2e4cdcd69402", "verdict": "approved", "findings": [], "advisory_findings": ["A1-readme-content-not-leak-scanned", "A2-date-shaped-slug-duplicates-draft-number", "A3-capture-error-text-printed", "A4-equality-pair-simplification"]}
AGENTMARSHAL_VERDICT_END
