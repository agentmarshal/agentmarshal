Разобрал diff, прочитал `steps.py`, `process_log.py`, `records.py`, `localstate.py`, `project.py`, `placement.py`, `cli.py` и оба тестовых файла, сверил delta-spec с `openspec/specs/process-log/spec.md`.

## Что проверено и сходится

- **Заголовки MODIFIED.** `### Requirement: A writer appends events to a file of its own under the log directory` в delta совпадает дословно с `openspec/specs/process-log/spec.md:14`; новые три requirement'а идут под `## ADDED Requirements`. Change заархивирован в `openspec/changes/archive/2026-10-03-step-commands/` с proposal, design, tasks и delta — `openspec/changes/step-commands/` не осталось.
- **Покрытие сценариев.** Все 9 сценариев MODIFIED-требования и все 13 ADDED-сценариев имеют тест с docstring'ом, называющим сценарий (`tests/test_process_log.py:611,625` — два новых; `tests/test_steps.py` — остальные).
- **`/proc` parsing корректен.** `stat_bytes.rfind(b")")` + `fields[19]` — это именно field 22 (`starttime`), поскольку после закрывающей скобки `comm` поля начинаются с field 3; guard `len(fields) <= 19` правильный, `SC_CLK_TCK <= 0` отсечён, файл читается байтами, так что non-ASCII `comm` не даёт decode-ошибки (`steps.py:298-327`).
- **«no event lands» на отказах.** Все валидации (`validate_task_id`, `_parse_deadline`, `_refuse_unclean_text`, `_is_ulid`, `_is_word`) выполняются до `_writer_for`, так что при отказе даже writer-файл не создаётся.
- **Никакой traceback не уходит наружу по step-пути.** `find_project_root` может бросить только `OSError`, `resolve_placement` — `PlacementError`, `local_state` оборачивает `GitNotAvailableError` в `LocalStateError`, `ensure_directory` — в `LocalStateError`, `open_writer` — `OSError`/`ProcessLogError`; все четыре типа перечислены в `except` на `steps.py:132`.
- **Overflow deadline.** `timedelta(seconds=...)` и `.astimezone(UTC)` бросают `OverflowError`, он перехвачен (`steps.py:271`) — тест `test_a_deadline_that_overflows_is_refused` проверяет оба случая.
- **Surrogate-щель закрыта на уровне CLI:** argv на Linux декодируется через `surrogateescape`, но `forges_rendered_text` включает категорию `Cs` (`records.py:816`), поэтому ни `--actor`, ни `--run-dir`, ни `--outcome` не могут пронести одиночный surrogate до writer'а.
- **`cli.py` — только хук** (два добавленных места), импорт `steps` не затрагивает `journal.gate`, так что сценарий «importing the gate does not import the process log» не ломается.
- Утверждение design.md про «the journal's own `actor` field follows the same non-empty rule» проверено — `records.py:417-422` действительно требует non-empty строку.

## Advisory

В `src/agentmarshal/process_log.py:132-140` шаг кодирования `line.encode("utf-8")` стоит внутри `try`, который ловит только `OSError`, поэтому строковое поле с одиночным surrogate — `json.dumps(..., ensure_ascii=False)` его пропускает, а UTF-8 закодировать не может — выйдет наружу как голый `UnicodeEncodeError`, а не как обещанный `ProcessLogError`; из двух нынешних step-вызовов это недостижимо (категория `Cs` отсекается раньше), так что дефект латентный, но он противоречит цели design.md «every failure reaches the caller as a named error, never a traceback».

В `src/agentmarshal/process_log.py:182-209` граница каталога считается только в байтах: `_bound_directory` ничего не удаляет, пока `total <= DIRECTORY_CAP_BYTES`, а step-событие — это файл примерно на 250 байт, так что до срабатывания cap'а в `log/` успевает скопиться порядка 200 000 файлов, и при этом каждый запуск `step start`/`step end` делает `iterdir()` + `stat()` по всему каталогу, то есть стоимость команды растёт линейно по числу накопленных файлов; design.md утверждает, что «the process log bounds the directory as a whole by bytes … which is where the bound belongs», но байтовый cap не ограничивает число файлов, а эта задача — первый производитель событий с частотой «файл на команду».

Ни то, ни другое не блокирует: оба пункта лежат вне буквы acceptance criterion 5 («NaN, infinity, an unsupported type») и вне non-goals этой задачи.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ffca6170d04e71a8a6e9fafe3e6ef992f45f9f1c", "verdict": "approved", "findings": [], "advisory_findings": ["process-log-encode-step-escapes-as-unicodeencodeerror", "log-directory-bound-counts-bytes-not-files"]}
AGENTMARSHAL_VERDICT_END
