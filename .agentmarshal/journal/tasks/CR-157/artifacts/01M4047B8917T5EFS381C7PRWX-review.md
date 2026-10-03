Разобрал контракт, дельту спеки, архив и код. Прогнать `pytest`/`ruff`/`mypy` в этой песочнице не удалось — команды требуют подтверждения, а сессия неинтерактивная, так что проверка статическая: я вручную сверил длины строк (всё ≤ 88 символов), импорты, аннотации под `mypy --strict` и каждый сценарий дельты с docstring'ом теста. Выполнение CI-последовательности не подтверждено мной — это заявление реализатора, которое я не смог проверить.

Что сошлось:

- Архив на месте (`openspec/changes/archive/2026-10-03-step-commands/` с proposal, design, tasks и дельтой), `openspec/changes/step-commands/` отсутствует, `openspec/specs/process-log/spec.md` выглядит как чистый вывод `openspec archive`: MODIFIED-заголовок «A writer appends events to a file of its own under the log directory» совпадает дословно, три ADDED-требования дописаны в конец.
- Все 12 сценариев дельты (2 новых в MODIFIED + 7 + 3 + 2 в ADDED) имеют тест с docstring'ом «Scenario: …».
- Поля событий совпадают с ADR-0022 §7, строки 219–223 (`step`, `activity`, `pid`, `pid_started_at`, `deadline`, опционально `actor`/`run_dir`; `step-ended` — `step`, `outcome`). ADR называет для `outcome` словарь §4, но контракт явно требует «non-empty word» — реализация следует контракту, это не расхождение.
- Разбор `/proc/<pid>/stat` корректен: `rfind(b")")`, затем индекс 19 — это поле 22, и чтение байтами действительно снимает проблему non-ASCII `comm`.
- Переполнения `datetime` закрыты: и `timedelta`, и `astimezone` поднимают `OverflowError`, он перехвачен.
- Все строки, попадающие в событие, либо нормализованы (`deadline`), либо из закрытого множества (`activity`), либо проверены (`task`, `step`, `outcome`, `actor`, `run_dir`) — подделать отрисованный текст через событие нельзя.
- `_writer_for` вызывается только после валидации, поэтому отказ не создаёт файл лога; `local_state(resolve_placement(root))` без `require_host` действительно резолвит git common dir репозитория журнала, host не затрагивается.

Две не блокирующие заметки ниже.

`open_writer` в `src/agentmarshal/process_log.py:78` перехватывает у `path.open("xb")` только `FileExistsError`, а `_writer_for` в `src/agentmarshal/steps.py:124` ловит лишь `LocalStateError`, `PlacementError` и `ProcessLogError` — поэтому `EACCES` на уже существующем, но закрытом на запись `log/` (там `mkdir(exist_ok=True)` проходит молча) или `ENOSPC` на забитом диске выходит из `main()` голым traceback'ом, ровно тем, что эта задача убрала на пути append. Критерий приёмки говорит про «an OSError **while appending**», так что формально он выполнен, но design.md в Goals заявляет «Every failure reaches the caller as a named error, never a traceback», и это место ему противоречит.

`_run_start` в `src/agentmarshal/steps.py:133-153` проверяет `--actor` и `--run-dir` только на `forges_rendered_text`, поэтому `--actor ""` проходит и ложится в событие как `"actor": ""` — при том что для одноимённого поля journal-записи правило `_check_session_fields` (`src/agentmarshal/journal/records.py:417-422`) требует непустую строку; будущий рендер в `status`/`doctor` получит пустое поле, которое «given», но ничего не называет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "47f66b69a61e84f8cfb91a99e081a75861b03b54", "verdict": "approved", "findings": [], "advisory_findings": ["open-writer-oserror-escapes-as-traceback", "empty-actor-or-run-dir-recorded"]}
AGENTMARSHAL_VERDICT_END
