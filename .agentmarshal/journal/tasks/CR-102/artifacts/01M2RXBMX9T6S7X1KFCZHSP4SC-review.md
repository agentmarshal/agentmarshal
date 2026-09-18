Прочитал весь diff и сверил его с контрактом, delta-спекой, design.md, ADR-0004 и ADR-0005, плюс прошёлся по дереву за пределами diff'а (gate.py, migrate.py, open_task.py, prune.py, brief.py и все тесты, которые трогают terminal records).

**Что проверил по существу:**

- Guard `load_task_for_record` (`src/agentmarshal/journal/status.py:105`) эквивалентен правилу проекции: `state != "open"` ⟺ `has_terminal_record` в `project_status`, потому что состояние меняют только `opened`/`completed`/`abandoned`/`reopened`, и `reopened` сбрасывает и то, и другое. Второго списка admitted-типов нет — `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` читается и проекцией, и writer'ом (критерий 3 выполнен, grep по `"session"`/`"reopened"` в `src/` это подтверждает).
- Все writer'ы закрыты. `write_record` вызывается из семи мест в `src/`; `open_task.py:169` пишет в новую директорию задачи (и падает, если она есть), `migrate.py` — путь миграции, остальные пять теперь идут через guard. Дыра, которую описывает proposal, была ровно в `submit_review.py` и в commit-ветке `launch_review` — обе закрыты.
- Guard стоит **до** любой оплачиваемой или пишущей работы: в `launch_review` — до `_resolve_commit`/`_run_reviewer` (`review.py:1002`), в `_launch_finding_review` — первой строкой (`review.py:822`), в `submit_review` — до `write_artifact`, так что prose-артефакт не остаётся сиротой (`submit_review.py:55` против `:75`).
- `reopen` не сломался именно потому, что `"reopened"` входит в admitted-набор: `tests/test_reopen.py:94` продолжает получать «cannot be reopened (state: abandoned)» от собственной проверки CLI, а не от guard'а.
- Существующие assert'ы на текст не поехали: новое сообщение начинается ровно со старого префикса `task CR-001 is not open (state: ...)`, поэтому `tests/test_journal.py:1001` проходит, а подстрока «terminal record» сохранилась для `tests/test_acceptance.py:182`.
- Опубликованная спека `openspec/specs/record-lifecycle/spec.md` отличается от delta-спеки только заголовком и `ADDED Requirements` → `Requirements`. Ссылка на ADR-0005 Decision 3 и на его status-note проверена — note про reopening действительно есть (`docs/adr/ADR-0005-evidence-capture-and-format.md:29-31`).
- Каждый сценарий спеки назван в docstring соответствующего теста; `complete`, `abandon`, `accept`, `amend`, `finding`, `submit-review` параметризованы по обоим terminal-состояниям, launcher — по обоим состояниям и обоим bindings.

Блокирующих дефектов не нашёл. Два замечания без блокировки:

**GATE-KEEPS-A-SECOND-ENCODING-OF-THE-ADMITTED-SET** — критерий «no second list of it exists in the tree» выполнен для writer'ов, но то же правило «что допустимо после terminal record» второй раз закодировано строковыми литералами в `src/agentmarshal/journal/gate.py:715` (`-completed.json`, `-abandoned.json`, `-reopened.json`) и `:748` (`-session.json`), независимо от `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`. Сейчас они согласованы, и `gate.py` вне scope этой задачи, так что править было нечем — но дрейф, от которого критерий защищается, там по-прежнему возможен.

**LAUNCHER-TEST-NO-LONGER-EXERCISES-A-REAL-ABANDON** — в `tests/test_review_launcher.py:141` новый хелпер `_close_task` заменил живой вызов `main(["abandon", ...])` прямой записью record'а, и так теперь закрывается и abandoned-ветка ранее существовавшего теста. Объяснение в docstring («the lane commands that close a task have preconditions of their own») верно для `completed`, но не для `abandon`, у которого таких preconditions нет и который этот тест успешно вызывал раньше. Сквозная цепочка «abandon → review» перестала покрываться.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1128b48855589e0b52aa5b5261d0a358743221cb", "verdict": "approved", "findings": [], "advisory_findings": ["GATE-KEEPS-A-SECOND-ENCODING-OF-THE-ADMITTED-SET", "LAUNCHER-TEST-NO-LONGER-EXERCISES-A-REAL-ABANDON"]}
AGENTMARSHAL_VERDICT_END
