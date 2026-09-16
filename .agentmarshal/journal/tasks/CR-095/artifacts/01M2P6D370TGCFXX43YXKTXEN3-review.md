Проверил ADR-0011 против пяти критериев контракта, сверил все числа с журналом и все утверждения о механике с кодом.

**Что подтвердилось по репозиторию**

- Собственные цифры проекта: `ls */records/*amend*.json` даёт 22 записи в 19 задачах, из них одна — амендмент самой CR-095, то есть **21 запись в 18 задачах** ✓; завершённых задач (с `completed`-записью) в этом снапшоте ровно **92** ✓ (в proposal 022 стоит 91 — CR-094 закрылась между ними, и оговорка «when this was written» это держит).
- Случай «контракт поправлен между вторым и третьим раундом после блокирующего finding о формулировке критерия» — это CR-075: `01M1D484…-review.json` (`changes_required`, `CR-075-001`), затем `01M1D49E…-amendment.json` с причиной именно про переписанный критерий, затем ещё два раунда ✓.
- Механика: `gate.py:735-746` читает контракт из merge-base, `review.py:360-369` — из снапшота ревьюируемого коммита, sidecar в обоих местах читает своё рабочее дерево ✓. Закрытая валидация записей — `records.py:224-227` ✓. Схемная политика «штампуем новую схему только на записи с новым полем, текущая остаётся полом» дословно совпадает с ADR-0004 (строки 148-151) ✓. `gates never parse prose` — точная цитата ADR-0004 D3 ✓. `submit-review` действительно пишет verdict без промпта (`submit_review.py:36-69`) ✓. Все дайджесты в журнале — нижний регистр hex (`_ARTIFACT_HASH_PATTERN`, `_REVIEWED_COMMIT_PATTERN`) ✓.
- Ссылка на `../proposals/022-amendments-invisible-to-the-reviewer.md` резолвится, предложение опубликовано и числится в `docs/proposals/README.md:101` — блокирующий finding прошлого раунда закрыт ✓. Sidecar-refusal тоже закрыт: решение 3 больше не вводит отказа ни в одной расстановке и честно оставляет sidecar открытым ✓. Заголовок и дисклеймер «not implemented by this document» совпадают с ADR-0009/ADR-0010 ✓.

Ни одного противоречия с ADR-0004, ADR-0006 или ADR-0008 не нашёл. Три замечания — совещательные.

`adr0011-no-amendment-task-unchanged` — строки 129-130 («A task with no amendments has nothing to render and nothing about it changes») опровергаются строками 136-138 той же секции: review-запись получает `reviewed_contract` под новым номером схемы независимо от амендментов, и запись сама это признаёт как «the only part of this decision that reaches a journal which has never amended anything». Абсолютное «nothing about it changes» шире механизма, который оно описывает (критерий 4, первая половина); прошлый раунд блокировал предка этой фразы, и сужение до «a task» с явной поправкой ниже вред снимает, но неточность осталась.

`adr0011-context-sidecar-unqualified` — строка 38 («Nor can a candidate be judged against a contract it has not incorporated») верна только для embedded: в sidecar и gate (`gate.py:738-742`), и ревьюер (`review.py:360-369`) читают контракт из рабочего дерева sidecar, которое кандидат не инкорпорирует вообще. Решение 3 эту разницу называет отдельно, так что читателя не вводят в заблуждение, но само утверждение в Context дано без оговорки о расстановке.

`adr0011-reviewed-contract-no-reader` — решение 4 (строки 98-114) вводит `reviewed_contract`, но нигде не называет party и момент чтения: единственный кандидат в читатели (сверка в sidecar-gate) вынесен в «Left open», а для embedded-расстановки читателя нет вовсе — только «the evidence to see it afterwards». Сторона, с которой берётся хешируемый текст, выводится из решений 1 и 3, поэтому критерий 2 я считаю выполненным, но прямой ответ «кто и когда это читает» в записи отсутствует.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5bc42efffdb26d0bee72f4edd8e4b81aabb95bb7", "verdict": "approved", "findings": [], "advisory_findings": ["adr0011-no-amendment-task-unchanged", "adr0011-context-sidecar-unqualified", "adr0011-reviewed-contract-no-reader"]}
AGENTMARSHAL_VERDICT_END
