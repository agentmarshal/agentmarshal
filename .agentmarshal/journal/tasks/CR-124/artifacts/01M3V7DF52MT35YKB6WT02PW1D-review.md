Прошёлся по диффу и сверил каждое утверждение о поведении инструмента с кодом: `report` печатает только `reviews=`/`tokens=` и ничего о времени (`src/agentmarshal/journal/report.py:144-145`), `created_at` обязателен у каждой записи, а session-запись несёт `role`, `actor`, `activity`, `outcome`, `tokens` и никакого коммита (`src/agentmarshal/journal/records.py:36,113-119`), `gate` сверяет email ревьюера с авторами коммитов диапазона (`src/agentmarshal/journal/gate.py:967-983`), journal-only полоса смотрит только на поддерево своей задачи и записи других задач в диффе не проверяет (`src/agentmarshal/journal/gate.py:650-717`), рецепт стейджинга действительно тот, что `init` пишет в README аутбокса (`tests/test_project.py:19-22`), ни одна команда сама не коммитит. Внутренняя арифметика измерений сходится: у 033 2+4+2+0+1+3+1=13 blocking, суммы $27.02 и ~94.4 ≈ 95 мин, $27.02 > $18.24; у 035 70/252 = 28%; у 036 4+3=7. Секция `## Where` есть последней у всех 027-036 и согласуется со своей строкой индекса; 027 называет отклонившего («by us, upstream»), 031 называет 033 в обоих местах; введение батча даёт 13 тем плюс файл-отзыв = 14 без неопубликованных номеров; карта документации содержит все пять новых строк; все названные релизы (0.3.0, 0.4.0) опубликованы, а принятые-но-не-сделанные части релиза не называют. Оригиналы репортёра (017-021) и документ координатора с dispositions в снапшот не входят — дословность измерений и совпадение sha256 проверить нельзя. Полную последовательность CI запустить не удалось: `uv` в этой песочнице требует approval; дифф состоит только из документации, и ни один тест не читает `docs/`, так что причин для падения не видно, но критерий 5 в этой части я не подтверждаю.

Блокирующее замечание одно.

В `docs/proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md:62-65` утверждение «today the tool has no outcome value for them at all» неверно на момент публикации и противоречит собственной диспозиции этого же файла: значение `provider-limit` опубликовано как документированный outcome в 0.4.1 (`CHANGELOG.md:40-41`, `docs/proposals/024-provider-quota-stop-cannot-be-recorded.md:54-56`), на что сам файл и ссылается тремя абзацами ниже («extend the vocabulary proposal 024 established, where `provider-limit` names a session the provider refused to continue», строки 78-83) и на что корректно ссылается 036 (`docs/proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md:49`). По той же причине «The outcome values — for a session that ended on a provider limit and for one that ended on an output-limit truncation — are accepted… Accepted; not shipped yet» занижает уже сделанное: не отгружено только значение для обрыва по output-лимиту. Адоптер, читающий этот дайджест, не поймёт, можно ли писать `provider-limit` сегодня.

Ниже — непреграждающие замечания.

В `docs/proposals/032-the-journal-has-no-time-axis.md:3` скобка перечисляет как deferred только session duration и lead-time report, хотя `gate` mode отложен тем же решением, а абзац о нём (строки 83-85) вообще не называет диспозицию ни одним словом из словаря `docs/proposals/README.md:30-34` — «waits with the same rework» читается, но не является значением.

В `docs/proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md:73-74` и `docs/proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md:59-60` предложенная часть про `status` (показ назначения рядом с тем, что реально запускалось; показ сессии, породившей кандидата) не получает диспозиции ни в секции Disposition, ни в Where — тогда как 035 свою `status`-часть разбирает явно (`docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md:91-93`). Критерий 2 требует диспозиции для каждой части файла.

В `docs/proposals/028-check-outcomes-are-not-evidence.md:3,66,79` и `docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md:3,63,75` шапка теперь говорит просто «deferred», а заголовок секции («Disposition — accepted as a piece of work, deferred») и её последняя фраза («Accepted; not shipped yet.») продолжают утверждать принятие как работы. Исправление формы в шапке сделано, тело под неё не приведено, и шапка со строкой индекса теперь теряют половину, которую тело по-прежнему заявляет.

В `docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md:68` сказано «the six specification defects that motivated the earlier file», тогда как 031 говорит «About six were specification defects» среди 21 поправки (`docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md:29-31`), а мотивирующий случай там один; определённый артикль приписывает приблизительной оценке точность, которой у неё нет.

Два непреграждающих замечания прошлого ревью по файлам, которые эта задача и так правит, остались в силе: «a review record pins the contract it judged with a sha256» в `docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md:15-16` по-прежнему шире кода (`reviewed_contract` ставит только лаунчер, `src/agentmarshal/journal/review.py:906`; `submit-review` его не передаёт, `src/agentmarshal/cli.py:629-641`), и «Both are legitimate work» в `docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md:67` по-прежнему без внятного антецедента.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "058bd71730f4b21e3b6b9b83a652d7634d196cf3",
  "verdict": "changes_required",
  "findings": [
    "034-provider-limit-outcome-already-published-in-0.4.1"
  ],
  "advisory_findings": [
    "032-gate-mode-has-no-vocabulary-disposition",
    "034-036-status-part-has-no-disposition",
    "028-030-header-and-body-disagree-after-form-fix",
    "033-six-specification-defects-overstated",
    "cr-123-advisories-031-and-030-still-open",
    "ci-sequence-not-executed-uv-blocked"
  ]
}
AGENTMARSHAL_VERDICT_END
