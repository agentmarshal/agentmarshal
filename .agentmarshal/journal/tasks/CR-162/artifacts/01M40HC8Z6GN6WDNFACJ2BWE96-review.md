Прочитал всё: `steps.py`, `status_view.py`, `_run_status`, `localstate.py`, `process_log.py`, ADR-0014 D9/D13, дельту и живой спек, оба набора тестов.

## Что проверил и что сходится

**Логика `open_steps`** соответствует критерию 2 построчно: `step-ended` закрывает по `step` id; `implementation`-шаг — session с той же activity; `review`-шаг — только record `review` (session активности `review` не закрывает — это сознательное решение, зафиксированное и в design, и в тесте); `coordination`/`other`/неизвестная — session той же activity; `completed`/`abandoned` — любой шаг. `created_at > started_at` строгое, нечитаемый `created_at` не закрывает, нечитаемый `at` даёт `_START_OF_TIME`, `OverflowError` на краю диапазона пойман в `_moment` и покрыт тестом. Дедуп по `seen`, фильтр по task — на месте.

**Пути**: `local_state` ничего не создаёт (`localstate.py:104`), `git_common_dir` поднимает только `GitNotAvailableError` → `LocalStateError`, так что деградация до `unavailable (...)` полная и `status` без git не падает — раньше он git не требовал, это аккуратно сохранено. Непрочитываемый лог: `exists()`/`is_dir()` на EACCES самого `log/` поднимают `PermissionError`, `read_events` — на `iterdir()`; оба ловятся в `_read_process_events` (`cli.py:968`). Сообщение об ошибке git может быть многострочным (stderr git), и оно проходит через `escape_for_display` — подделать строку нельзя.

**Экранирование**: вся строка `Overdue step …` идёт через `escape_for_display`, а `\t` входит в категорию `Cc`, которую `forges_rendered_text` отвергает — значит title не может подделать четвёртое поле `overdue-step` в списке.

**Грамматика `--deadline`**: новый regex принимает все прежние входы, `fullmatch` + проверка `group(0)` корректно отбрасывают пустую строку, а порядок `d,h,m,s` и однократность единиц следуют из структуры regex — `5m2h`, `1h1h`, `1h30`, `h30m`, `90x` отвергаются. `format_overdue` всегда печатает строку, которую `_parse_deadline` принимает обратно (включая `0s`).

**Покрытие сценариев**: все 14 + 8 сценариев дельты имеют тест, чей docstring их называет. Изменение заархивировано, активной директории `openspec/changes/status-steps-and-paths/` не осталось, два byte-exact пина stdout не сдвинулись.

## Замечания (не блокирующие)

Сценарий «stdout stays what the documentation promises» в `openspec/specs/process-log/spec.md:432` утверждает, что «stdout carries exactly what it carried before this change», но тот же ADDED-requirement выше (строка 310) требует, чтобы список помечал задачу `overdue-step` четвёртым полем, а деталь печатала строку `Overdue step …` — обе на stdout. Для задачи с просроченным шагом stdout не равен прежнему; сценарий верен только в случае «просрочки нет», и именно в этом случае его демонстрируют оба теста. Формулировку стоило ограничить путями (они-то на stderr).

Пункт 1.3 задач изменил принимаемую грамматику `--deadline` (`src/agentmarshal/steps.py:56`, теперь `1h30m`, `1d3h4m7s`), но дельта содержит только `## ADDED Requirements`, и требование «`step start` records a step's start and deadline» (`openspec/specs/process-log/spec.md:197`) по-прежнему описывает лишь «a duration such as `90m`» без сценария на составные единицы. Поведение закреплено тестом, но в спеке капабилити его нет.

`docs/quickstart.md` и `docs/sidecar.md` не упоминают ни три новые строки путей на stderr, ни новые добавления в stdout; `docs/` вне scope контракта, так что это отступление для отчёта, а не правка в этом диффе.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7cc214f47152d63a95ab3adbeb7f3b4aed1af3a9", "verdict": "approved", "findings": [], "advisory_findings": ["advisory-spec-stdout-unchanged-scenario-contradicts-overdue-mark", "advisory-deadline-compound-duration-grammar-absent-from-spec", "advisory-docs-not-updated-for-new-status-output"]}
AGENTMARSHAL_VERDICT_END
