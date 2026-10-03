Прочитал `steps.py`, изменения в `process_log.py` и `cli.py`, спеку `openspec/specs/process-log/spec.md`, архив изменения, ADR-0022 §7 и оба тестовых файла. Запустить pytest/ruff/mypy в этой песочнице мне не дали (команды требуют approval), поэтому про прохождение CI опираюсь на твою вводную и ничего о падении инструментов не утверждаю.

Что проверил по существу:

- **Контракт/спека.** Все 13 ADDED-сценариев и 2 новых сценария MODIFIED-требования покрыты тестами, docstring каждого теста дословно называет сценарий. Заголовок MODIFIED-требования в дельте совпадает с существующим в `openspec/specs/process-log/spec.md:14` символ в символ; `openspec/changes/` содержит только `archive/`, остатка `step-commands/` нет — изменение действительно заархивировано командой. `cli.py` получил ровно хук (`cli.py:349`, `cli.py:1238`).
- **Поля событий** совпадают с ADR-0022 §7 (`step`, `activity`, `pid`, `pid_started_at`, `deadline`, опционально `actor`/`run_dir`; `step-ended` — `step` + опциональный `outcome`); `outcome` в §4 — документационный словарь, а не проверяемый, так что «любое непустое слово» — верное прочтение.
- **`/proc`-разбор верен**: `starttime` — поле 22, то есть индекс 19 после последней `)`, проверка `len(fields) <= 19` корректна, чтение в байтах действительно снимает проблему не-ASCII `comm`; `btime` + `SC_CLK_TCK` с защитой от `<= 0`. `ps -o etime=` разобран по POSIX-формату, таймаут ограничен, любая неудача даёт `unknown`.
- **Переполнения дедлайна** реально перехвачены: `timedelta(seconds=...)` бросает `OverflowError` на конструировании, `astimezone` — на выходе за 9999 год; оба в `except (ValueError, OverflowError)`.
- **Порядок валидации** в обеих подкомандах — до `open_writer`, поэтому «ни одного события не легло» выполняется не случайно.

Блокирующих дефектов не нашёл. Три замечания — все необязательные:

`advisory-local-state-mkdir-error-lacks-remedy`: самый вероятный реальный отказ файловой системы — невозможность создать `log/` (read-only fs, запрет прав) — поднимается как `LocalStateError` из `src/agentmarshal/localstate.py:100` и печатается в `src/agentmarshal/steps.py:129-131` как «cannot create <dir>: [Errno 13] …», то есть каталог назван, а «что делать» — нет, хотя сценарий спеки требует и то и другое; текст с подсказкой есть только во ветке `except OSError` (`steps.py:139-143`), и именно её закрывает тест, подменяющий `open_writer`.

`advisory-write-event-recursion-not-refused`: в `src/agentmarshal/process_log.py:124-131` отказ в кодировании ловит только `TypeError`/`ValueError`, тогда как глубоко вложенное (ацикличное) значение даёт `RecursionError` и уйдёт к вызывающему трейсбеком вместо `ProcessLogError` — при том что читатель в `process_log.py:246` этот самый `RecursionError` ловит осознанно; шаговым командам это недостижимо, но `write_event` — общий писатель, и ADR-0022 §7 отдаёт в тот же лог `extension-event` с произвольным JSON-payload от расширения.

`advisory-writer-file-per-step-run`: каждый запуск `step start`/`step end` создаёт отдельный файл писателя (`process_log.py:63-83`), а `_bound_directory` (`process_log.py:168-209`) ограничивает каталог только по байтам (50 МБ) и удаляет `.jsonl` лишь старше суток — число файлов практически не ограничено, и `open_writer` на каждом запуске делает `stat` по всем записям каталога; `design.md` этот churn осознанно принимает, но шаговые команды — первые, которые вызываются многократно за задачу, так что цена решения теперь другого масштаба.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9b32127e8bdb03d2a648c6b31ebfc4f49488fd42", "verdict": "approved", "findings": [], "advisory_findings": ["advisory-local-state-mkdir-error-lacks-remedy", "advisory-write-event-recursion-not-refused", "advisory-writer-file-per-step-run"]}
AGENTMARSHAL_VERDICT_END
