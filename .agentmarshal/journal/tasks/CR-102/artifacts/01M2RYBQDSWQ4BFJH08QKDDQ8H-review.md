Разобрал контракт, дифф и окружающий код (запустить тесты не дали — sandbox отклонил `pytest`, так что проверка статическая: прочитал все вызовы `write_record`, все прежние приватные guard'ы и все тесты, которые ассертят старые тексты отказов).

**Что сходится.** Гард `load_task_for_record` (`src/agentmarshal/journal/status.py:105`) читает допустимый набор из `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` — той же константы, что использует `project_status`, второго списка в дереве нет (единственное похожее место, `gate.py:744` с `-session.json`, — это отдельное правило формы диффа из ADR-0005 D3, не writer'ский набор). Все команды, пишущие запись в существующую задачу, проходят через гард: `submit-review`, `accept`, `amend`, `finding`, `complete` (три пути + sidecar-путь в `cli.py:881`), `abandon`, `reopen`, `record-session`, оба биндинга `review`. `open_task.py` и `migrate.py` пишут не в существующую задачу — справедливо оставлены в стороне.

**Совместимость со старыми тестами** держится не случайно, но впритык: `tests/test_acceptance.py:182` ассертит подстроку `"terminal record"`, и она выживает только благодаря хвосту нового сообщения «its terminal record admits only…»; `tests/test_journal.py:1001` и `tests/test_reopen.py:94` совпадают как префиксы. Ломающихся ассертов не нашёл.

**Гарды стоят до дорогой работы**: в `launch_review` (`review.py:1002`) — до `_resolve_commit`/`git diff`/tempdir, в `_launch_finding_review` (`review.py:822`) — до распаковки снапшота и записи prompt-файла. Оба новых теста лаунчера это пинят через stub, который не отработал.

Ниже — две неблокирующие претензии.

Правило «переоткрыть можно только из `done`» теперь живёт в трёх местах: проекция `status.py:68`, гард `status.py:123`, и `cli.py:989` — причём копия в CLI после изменения достижима только для `state == "open"`, потому что для терминальных состояний до неё доходит уже гард; design.md устраняет дрейф для *множества* допустимых типов, но этот предикат получил свежую вторую копию.

Инвентарь писателей в `openspec/changes/archive/2026-09-18-writer-refuses-a-closed-task/design.md` неполон: он называет «two paths straight out of `cli.py` (`amend`, `finding`)», тогда как дифф правит четыре (`amend`, `finding`, `reopen` и sidecar-ветку `_run_complete`), и не упоминает собственный guard в `review.py::_launch_finding_review` — при том что документ прямо утверждает, что состояние «checked against the diff rather than assumed».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ac73088906cdd86e56732f65e2cc9534692afd36", "verdict": "approved", "findings": [], "advisory_findings": ["reopen-rule-has-three-copies", "design-writer-inventory-incomplete"]}
AGENTMARSHAL_VERDICT_END
