Проверил запись ADR против самого репозитория: журнал, `review.py`, `gate.py`, `records.py`, ADR-0004/0006/0008/0009 и proposal 022.

Что подтвердилось фактами:

- Счётчики точные. В журнале 22 amendment-записи в 19 задачах; CR-095 (сама эта задача) даёт одну, значит **21 amendment в 18 из 92 завершённых задач** — ровно то, что написано. Расхождение с контрактом (91) в пользу ADR: на ревьюируемом коммите завершено 92.
- Нарратив про «поправку между вторым и третьим раундом» реален и проверяем: CR-075 — два `changes_required`, затем amendment с reason про формулировку критерия, затем раунды 3 и 4 с `approved`.
- `review.py:347-378` — контракт в embedded читается из снапшота ревьюируемого коммита, в sidecar из рабочего дерева sidecar; `gate.py:735-758` — из merge-base tree, в sidecar из рабочего дерева, и транскрипт уже говорит «not pinned to a commit» (`gate.py:815-819`). Всё это ADR описывает верно.
- Валидация записей действительно закрытая (`records.py:224-228`), `reason` у amendment обязателен (`records.py:270-275`), `recorded_by` действительно опционален (`records.py:674-677`), schema 4 действительно штампуется только при наличии поля — и ADR-0004 в Consequences сам фиксирует этот паттерн, так что ссылка корректна.
- «Every path that hands a contract» — путей ровно два, `brief.py:256` и `review.py:361`; других потребителей `contract.md` в коде нет.
- `reviewed_contract` опционален только на человеческом пути — подтверждается: `cli.py:575-581` запрещает `review --reviewed-finding`, так что findings-lane ревью идут только через `submit-review`, у которого промпта нет.

Теперь то, что не сходится.

**gate-currency-claim-unsupported** — `docs/adr/ADR-0011-contract-amendment-visibility.md:82-83`: «the gate will require the candidate to take the newer text before it can be judged against it». Gate этого не требует и требовать не может: контракт читается из `merge-base(base, candidate)` (`gate.py:595-597`, `gate.py:744-747`), а merge-base по определению не содержит коммитов, добавленных в base после точки ветвления. Поправка, влитая в main, пока кандидат в полёте, для gate просто не существует — он оценит scope по старому тексту и пропустит кандидата. Проверки «кандидат актуален относительно base» в gate нет вообще (`is-ancestor`/`rev-list` используются только для пустого репозитория и в `prune.py`), и `docs/self-hosting-workflow.md:118-120` подтверждает ту же модель. Предложение это не безобидное: оно обосновывает ключевой выбор Decision 1 («that is the signal rather than a defect») защитой, которой нет, — ровно то преувеличение, от которого запись сама себя предостерегает на строке 38-39, и ровно то, что threat model контракта запрещает («not a new refusal»). Формулировка на строках 45-47 сказана корректно («applies to that candidate only once the candidate merges it») — вот её и надо оставить.

**absent-field-case-answered-and-deferred** — `ADR-0011:142-143` против `ADR-0011:169-171` и `ADR-0011:178-180`. Decision 4 закрывает вопрос отсутствующего `reviewed_contract` категорически: «An absence is therefore never a violation and never a line anywhere». Decision 5 затем говорит, что реализующая задача «has to answer the absent-field case first», и сама же его отвечает тем же аргументом, а Decision 6 строит на этом причину, по которой открытый вопрос нельзя решить сейчас: «It cannot be answered before the absent-field case is». По собственному тексту записи absent-field case уже отвечен — значит заявленная причина отложить единственный открытый вопрос несостоятельна.

**adr-0009-lane-admission-misstated** — `ADR-0011:191-193`: «ADR-0009 D3 admits a task to that lane *because* its contract declares no scope». ADR-0009 D3 (`docs/adr/ADR-0009-research-findings-lifecycle.md:89-96`) требует двух условий: контракт не объявляет scope **и** задача несёт хотя бы одну `finding`-запись; там же прямо сказано, что «a task with an empty scope and no finding is... a task that cannot land yet». Приведённая причина — половина условия, выданная за само условие.

**findings-lane-decided-against-non-goal** — `ADR-0011:190-195`. Non-Goals контракта CR-095 включают «Anything about the findings lane», а этот bullet принимает решение о ней: findings-lane задачи «its reviews are handed the same rendering». Это содержательное распространение Decision 1 на lane, вынесенную из объёма задачи; если намерение было лишь «исключений не вводим», это стоит сказать как отказ решать, а не как решение.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e6e01db0e2ebc098be7e74c9d79ee461b7639c71", "verdict": "changes_required", "findings": ["gate-currency-claim-unsupported"], "advisory_findings": ["absent-field-case-answered-and-deferred", "adr-0009-lane-admission-misstated", "findings-lane-decided-against-non-goal"]}
AGENTMARSHAL_VERDICT_END
