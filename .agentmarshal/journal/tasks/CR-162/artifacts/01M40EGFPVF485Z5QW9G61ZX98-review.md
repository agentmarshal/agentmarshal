Я прочитал реализацию (`steps.py`, `status_view.py`, `_run_status`), спеку `openspec/specs/process-log/spec.md`, архив change-а, новые и изменённые тесты, а также ADR-0014 (решения 8, 9, 13), `localstate.py`, `process_log.py`, `journal/status.py` и `journal/display.py`.

**Что сходится с контрактом.** Все 18 сценариев обеих новых requirements имеют тест, чей docstring называет сценарий (проверил по списку один к одному). `open_steps` — одна функция для обеих форм команды, и это действительно проверено подменой `steps.open_steps` в `tests/test_status_steps.py:293`; оба вызова идут через модуль, так что spy срабатывает. Правило закрытия шага совпадает с acceptance: `step-ended` того же task-а, `review`-запись для review-шага, `session` той же activity для остальных, строгое `created_at > started_at` (`steps.py:530`). Деградация при неразрешимом local state не ломает команду, отсутствующий `log/` читается как пустой (`read_events` возвращает `[]`), в sidecar пути берутся из `placement.project_root`/`journal_root`, и хост в вывод не попадает — это закреплено тестом. Два байт-точных пина изменились ровно на одну строку `Paths:`. Блокирующих расхождений с контрактом я не нашёл.

Ниже — непрепятствующие замечания.

Строка `Paths:` печатается в stdout (`src/agentmarshal/journal/status_view.py:232`), а документация обещает обратное: `docs/sidecar.md:401` утверждает «`status`, `report` … stdout unchanged», `docs/quickstart.md:479` — «their stdout stays exactly as anything parsing it expects», и транскрипт `docs/sidecar.md:310` теперь устарел; `docs/` вне scope контракта, поэтому это departure для отдельной задачи (альтернатива, тоже удовлетворяющая контракту — stderr, как у `Placement:`).

`_moment` (`src/agentmarshal/steps.py:504`) ловит только `ValueError`, тогда как `parsed.astimezone(UTC)` на корректно разобранном, но крайнем aware-времени (`"0001-01-01T00:00:00+05:00"`, `"9999-12-31T23:00:00-05:00"`) даёт `OverflowError`, который в `_run_status` не попадает в `except (OSError, TaskStatusError, ValueError)` (`src/agentmarshal/cli.py:1010`) и выходит голым traceback-ом — при том что `_parse_deadline` в этом же модуле `OverflowError` уже перехватывает, а `read_events` нечитаемый `at` сознательно терпит.

Нечитаемый каталог `log/` (права на сам каталог) роняет `status` в exit 1: `read_events` не оборачивает `state.log.iterdir()` (`src/agentmarshal/process_log.py:161`), и `status`, который раньше о логе ничего не знал, теперь отвечает ошибкой — ровно тот сценарий деградации, который для git в этом же change-е сделан аккуратно.

Экранирование строки overdue-шага не покрыто тестом: `print_overdue_steps` (`src/agentmarshal/journal/status_view.py:239`) в тестах напрямую не вызывается, проверяется только префикс строки на уровне CLI, хотя пункт 2.1 в `tasks.md` помечен выполненным со словами «the escape included» — снятие `escape_for_display` там пройдёт CI незамеченным.

Список задач пересканирует весь журнал событий на каждую задачу: `open_steps` вызывается в цикле по задачам (`src/agentmarshal/cli.py:986`) и каждый раз дважды проходит полный список событий (2×N×E), а `read_events` разбирает весь каталог лога целиком, который ограничен лишь `DIRECTORY_CAP_BYTES` = 50 МБ.

Docstring `format_overdue` (`src/agentmarshal/steps.py:477`) и design.md заявляют, что спан печатается «in the duration units `step start --deadline` already accepts», и приводят `2h5m`, `1d3h`, `1h30m` — но `_DURATION = ^(\d+)([smhd])$` (`src/agentmarshal/steps.py:53`) принимает только одну единицу, так что эти написания `--deadline` не примет; поведение корректно, неверно утверждение в комментарии.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5df0e150218be734b5c0f886b845dcafa994153c", "verdict": "approved", "findings": [], "advisory_findings": ["paths-line-on-stdout-contradicts-docs", "moment-overflow-error-traceback", "unreadable-log-dir-now-fails-status", "overdue-line-escape-untested", "status-list-rescans-every-event-per-task", "format-overdue-docstring-misstates-deadline-units"]}
AGENTMARSHAL_VERDICT_END
