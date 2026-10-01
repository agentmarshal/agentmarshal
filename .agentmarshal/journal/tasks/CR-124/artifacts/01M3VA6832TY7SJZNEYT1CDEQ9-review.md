Прошёлся по диффу и сверил каждое утверждение о поведении инструмента с кодом.

**Что проверено и сходится.** Правка 031 теперь точна: `reviewed_contract` пишет только лаунчер (`src/agentmarshal/journal/review.py:906`), а `submit-review` его не передаёт — ни парсер (`src/agentmarshal/cli.py:116-142`), ни `_run_submit_review` (`src/agentmarshal/cli.py:629-641`), хотя сама функция параметр принимает (`src/agentmarshal/journal/submit_review.py:49`); это ровно то, чего не хватало прошлому раунду. Описание ворот в 035 верно: схема, совпадение `task` с директорией, коллизии путей, второй `opened` по всем задачам диффа (`gate.py:1020-1091`), и привязки записи к задаче транзакции действительно нет — ограничение `task_dir_prefix` живёт только в measurements-only-полосе для закрытой на базе задачи (`gate.py:704-710`). 036 верно: сессия не несёт коммита (`records.py:108-121`, `records.py:940-958`), ворота смотрят только `verdict` и e-mail ревьюера против авторов диапазона (`gate.py:898`, `gate.py:966-985`), `outcome` — свободный текст (`records.py:548`), `implemented` и `provider-limit` документированы (`docs/quickstart.md:433`, `449`; `CHANGELOG.md:41` в 0.4.1). 032 верно: `report` печатает только `reviews=`/`tokens=` (`report.py:144-145`), у сессии нет ни start time, ни длительности. 035 верно цитирует рецепт из README аутбокса, который пишет `init` (`src/agentmarshal/project.py:237-240`), и формулировку 019 «stages only the journal» (`019-...md:33`). Все пять новых хешей — 64 знака нижним регистром, дублей по каталогу нет. Арифметика измерений сходится: 033 — $27.02 и ~95 мин по строкам таблицы, 13 blocking; 035 — 70/252 = 28%; 036 — 4+3=7. Введение батча теперь перечисляет ровно четырнадцать тем, из них четыре неопубликованные без номеров; строки индекса 032-036 и карта документации на месте; все пять замечаний прошлого раунда (027 называет отказавшего, 030 «Both» получило антецедент, 031 — хеш и ссылку на 033, форма диспозиции 028/030, секции Where у 027-030) закрыты.

**Чего проверить не смог.** Оригиналы репортёра 017-021 и документ координатора с dispositions в снапшот не входят, поэтому дословность измерений и совпадение sha256 (критерии 1-2) непроверяемы. Последовательность CI запустить не удалось: `uv` и `python3` в этой песочнице требуют approval. Дифф — только markdown, тест, трогающий `docs/`, проверяет лишь наличие ссылок на `docs/proposals/` (`tests/test_project.py:38-42`), фильтров по путям в workflow нет, так что причин для падения не вижу — но утверждать, что критерий 5 выполнен, не могу.

Ниже — непреграждающие замечания.

В `docs/proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md:87-97` и в её же Where (строки 102-107) и строке индекса диспозиция противоречит себе: «**The header fields** … are accepted» и в том же абзаце «так же на столе формы, которые оставляют контракт неизменным и объявляют назначение в другом месте, читаемом воротами», плюс «where the assignment will live is undecided». Для репортёра, отслеживающего заявку по словарю диспозиций, «поля шапки приняты» и «где будет жить назначение — не решено» несовместимы; принято объявленное назначение, а не его размещение в шапке.

В `docs/proposals/028-check-outcomes-are-not-evidence.md:3`, `docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md:3`, `docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md:85` и `docs/proposals/032-the-journal-has-no-time-axis.md:75-81` одно и то же состояние — «реально, но ждёт архитектурного решения» — теперь помечено словом `accepted`, тогда как предметы, рядом с которыми эти файлы себя же и ставят, в индексе остаются `deferred`: поле `evidence` из 026 (`README.md:177`), cost-поле 018 (`README.md:162`), reset-time 024 (`README.md:188`). 032 это прямо проговаривает — «into the rework of accounting — where the cost field of proposal 018 and the reset-time field of proposal 024 already sit», — и получается, что одна полка в индексе подписана двумя разными значениями словаря. Форму в скобках прошлый раунд забраковал справедливо, но раздел Disposition в `docs/proposals/README.md:30-40` под выбранное решение не расширен.

В `docs/proposals/README.md` строка 035 перечисляет только per-task staging и предупреждение ворот, а принятый там же `status`-листинг записей, которые есть в рабочем дереве и отсутствуют на базовой ветке (`035-...md:92-93`, `99-102`), в столбце Where пропущен; строки 032, 034 и 036 перечисляют все принятые части, так что требование критерия 3 «consistent with its index row» выполнено лишь по букве.

В `docs/proposals/032-the-journal-has-no-time-axis.md:84-87` диспозиция принимает «`gate` mode», который позволил бы проверке распознать journal-only изменение, не упоминая, что ворота уже это различие вычисляют и печатают: `journal_only = all(path.startswith(_JOURNAL_PREFIX) ...)` (`src/agentmarshal/journal/gate.py:650`) и «PASS: journal-only transaction (deterministic lane; review not required)» (`gate.py:738-741`). Примитив есть, просьба репортёра — вынести его в обязательную проверку; названный факт сделал бы обоснование сильнее и не занижал бы дешевизну работы — тот же класс неточности, что прошлый раунд отметил на утверждении 031 о хеше контракта.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "ae6a33e462173e18c25216bc4ef63dab43bf6c3d",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "034-header-fields-accepted-while-location-undecided",
    "disposition-vocabulary-split-accepted-vs-deferred",
    "035-index-row-omits-status-listing",
    "032-gate-journal-only-lane-already-exists"
  ]
}
AGENTMARSHAL_VERDICT_END
