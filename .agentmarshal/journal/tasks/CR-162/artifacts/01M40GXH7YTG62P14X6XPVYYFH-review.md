Проверил диф против контракта, спеки `process-log`, ADR‑0014 (решения 8, 9 с поправкой от 2026‑10‑03 и 13) и реального кода в снапшоте.

Что сошлось:

- `steps.open_steps` — одна функция на оба вида `status`, читает записи и события как данные, `now` инжектится; правило закрытия шага ровно такое, как в контракте: `step-ended`, implementation‑сессия для implementation, `review`‑запись для review (сессия с activity=review намеренно не закрывает), сессия той же activity для coordination/other/незнакомой, плюс `completed`/`abandoned` для любого шага. Сравнение `created_at > started_at` строгое, нечитаемый `created_at` не закрывает, нечитаемый `at` трактуется как `datetime.min` — как и описано; `_moment` глушит `OverflowError` на краевых смещениях.
- Строки просрочки идут на stdout после `print_task_detail`, целиком через `escape_for_display`, и сами называют источник («this machine's process log»). Список получает четвёртое поле `overdue-step` только при просрочке, первые три поля не тронуты.
- Пути печатаются один раз на stderr, по строке на путь, каждая через `escape_for_display`; `local_state` берётся от `placement.project_root`, то есть в sidecar — репозитория журнала (хост в вызов не входит). Нерешаемый local state деградирует до `unavailable (<reason>)` и команда всё равно отвечает; отсутствующий `log/` — не ошибка (`read_events` сам возвращает `[]`), а файл вместо каталога и отказ по правам ловятся в `_read_process_events` и печатаются на stderr без провала.
- Лог читается один раз за прогон, события группируются один раз (`step_events_by_task`), `now` берётся один раз — тесты это пиняют спаями. Байт‑точные пины stdout в `test_status_view.py` и `test_display.py` не сдвинулись, к ним добавлены ассерты stderr.
- Новая регулярка `_DURATION` — надмножество прежней (`90m`, `3h`, `2d` по‑прежнему проходят), пустое совпадение отсекается через `match.group(0)`, порядок и однократность единиц проверены негативными кейсами (`1h1h`, `5m2h`, `h30m`, `1h30`, `90x`); `format_overdue` печатает ровно то написание, что `--deadline` принимает.
- Все 22 сценария обеих новых требований имеют тест, чей докстринг их называет; изменение заархивировано в `openspec/changes/archive/2026-10-03-status-steps-and-paths/`, `openspec/changes/` пуст кроме `archive`, требования перенесены в `openspec/specs/process-log/spec.md` как ADDED (оба требования действительно новые, MODIFIED здесь неуместен).

Одно замечание, не блокирующее:

`docs-sidecar-status-transcript-stale` — транскрипт `agentmarshal status CR-001` в `docs/sidecar.md:306-320` показывает на stderr единственную строку `Placement: sidecar`, а команда теперь печатает ещё три (`journal:`, `process log:`, `local state:`); там же строка таблицы `docs/sidecar.md:401` («Print `Placement: sidecar` on stderr; stdout unchanged») и пояснение в `docs/quickstart.md:477-479` описывают stderr `status` как только строку placement. Файлы `docs/` не входят в scope CR‑162, поэтому правка здесь была бы выходом за рамки — но дрейф реальный и просит отдельного follow‑up (логично — вместе с задачей по `doctor`, который по решению 13 получит те же строки).

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7cc214f47152d63a95ab3adbeb7f3b4aed1af3a9", "verdict": "approved", "findings": [], "advisory_findings": ["docs-sidecar-status-transcript-stale"]}
AGENTMARSHAL_VERDICT_END
