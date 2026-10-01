Прошёлся по диффу и сверил каждое утверждение о поведении инструмента с кодом: девять типов записей и поля `session` — role/actor/activity/outcome/tokens, без commit и без длительности (`src/agentmarshal/journal/records.py:34-120`); `report`, печатающий `reviews=`/`tokens=` и ничего про время (`src/agentmarshal/journal/report.py:144-164`); ворота, читающие `verdict == "approved"` и сравнивающие email ревьюера с авторами коммитов диапазона (`src/agentmarshal/journal/gate.py:898-983`); детерминированная journal-only полоса (`gate.py:650-740`); рецепт стейджинга, который `init` пишет в README аутбокса — `git add .agentmarshal/journal` либо `.agentmarshal` минус аутбокс (`src/agentmarshal/project.py:238-239`), ровно тот, который 035 называет подметающим; формулировка 019 «stages only the journal» (`019-...md:33`); `provider-limit` в квикстарте (`docs/quickstart.md:449`) и `--outcome implemented` (`docs/quickstart.md:433`). Всё сходится.

По критериям: 032-036 на месте с шапкой формы 027-031, профилем Adopter D, релизом наблюдения и sha256; у всех тринадцати дайджестов 024-036 есть раздел `## Where`, согласованный со своей строкой индекса; 027 называет отказавшего («declined — by us, upstream»), 031 называет 033 и в теле, и в Where; строки индекса для 032-036 заполнены disposition и where; введение батча теперь даёт тринадцать тем плюс отзыв = четырнадцать файлов, без номеров неопубликованных; карта `docs/README.md:62-66` получила пять строк. Все относительные ссылки в `docs/proposals/` разрешаются в существующие файлы; ни один номер proposal'а (018, 019, 023, 024, 026, 028, 030, 031, 033, 034) и ни один релиз (0.3.0, 0.4.0, 0.4.1) не является неопубликованным; посторонних идентификаторов репортёра нет. Арифметика измерений сходится: в 033 суммы по таблице дают $27.02, ~95 мин и 13 blocking; в 035 70/252 = 28%; в 036 4+3 = 7.

Чего проверить не смог: оригиналы репортёра (017-021) и документ координатора с dispositions в снапшот не входят, поэтому дословность измерений, совпадение sha256 и соответствие диспозиций тому документу я не верифицировал — проверял внутреннюю согласованность. Полную последовательность CI запустить не удалось: `pytest`/`uv` в этой песочнице требуют approval; дифф состоит только из документации, а единственный тест, трогающий `docs/`, проверяет наличие ссылок на `docs/proposals/` в README (`tests/test_project.py:38-42`), так что причин для падения не видно — но утверждать, что критерий 5 выполнен, я не могу.

Ниже — непреграждающие замечания.

В `docs/proposals/028-check-outcomes-are-not-evidence.md:3` и `docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md:3` шапка переведена в `deferred`, но тело файлов осталось прежним: заголовок раздела по-прежнему «## Disposition — accepted as a piece of work, deferred», а последняя строка раздела — «Accepted; not shipped yet.», и уже следующий абзац (новый Where) начинается словом «Deferred». Снятая CR-123 претензия к формулировке «accepted *(as a piece of work; deferred)*» таким образом живёт в теле дословно, а шапка теперь читается против него: репортёр видит в одном файле «deferred» (реально, но не сейчас) и «Accepted» (согласны и намерены действовать).

В `docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md:36-38` утверждение «`gate` … does not look at records of other tasks in the same diff» шире факта: ворота валидируют каждую добавленную запись в диффе — схему, совпадение `task` с каталогом, коллизии путей с базой и дублирующийся `opened` — по всем затронутым задачам (`src/agentmarshal/journal/gate.py:1019-1088`). Чего они действительно не делают — не требуют, чтобы запись принадлежала задаче, которой названа транзакция; сам finding от этого не слабеет, но формулировка занижает то, что ворота уже проверяют.

В `docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md:9-13` третьему предложению приписано, что «that file called it the cheapest of the three to try and the only one that would have caught its motivating case before a round was spent» — со ссылкой на 031. В опубликованном 031 такой характеристики нет нигде: ни в разделе Proposed, ни в Disposition. Читатель, прошедший по ссылке, цитату не найдёт; если она из оригинала репортёра, это стоит сказать явно.

В `docs/proposals/032-the-journal-has-no-time-axis.md:3` скобка шапки называет отложенными только session duration и lead-time report, тогда как раздел Disposition и Where откладывают туда же режим `gate` для journal-only изменения. Строка индекса спасается оборотом «the rest», шапка — нет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "058bd71730f4b21e3b6b9b83a652d7634d196cf3",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "028-030-header-disposition-contradicts-body",
    "035-gate-ignores-other-tasks-overstated",
    "033-attributes-characterization-031-does-not-make",
    "032-header-parenthetical-omits-gate-mode"
  ]
}
AGENTMARSHAL_VERDICT_END
