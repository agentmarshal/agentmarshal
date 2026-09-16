Проверил ADR-0011 против контракта, репозитория (`.agentmarshal/journal`), кода (`journal/gate.py`, `journal/review.py`, `journal/records.py`, `journal/brief.py`), ADR-0004/0006/0008/0009, proposal 022 и CHANGELOG.

Что подтвердилось фактически:
- `gate.py:735-746` читает контракт из merge-base tree; `review.py:358-366` — из snapshot reviewed commit (embedded) и из working tree сайдкара (sidecar). Оба утверждения записи верны.
- `records.py:_validate_record` действительно закрыт по полям (`record has unsupported fields`), digest-паттерн — ровно 64 lowercase hex, `reason` у amendment обязателен. Схема 4 стампится только на записях с новыми полями — параллель в Decision 4 корректна.
- Счёт «21 amendment records across 18 of the 92 tasks completed»: в журнале 22 amendment-записи в 19 задачах, из них одна — собственная CR-095 (не завершена); остальные 18 задач все завершены, завершённых задач ровно 92. Число точное (контракт и proposal 022 несут более старое «91» — это не расхождение записи с репозиторием).
- CR-069 — та самая задача: opened → amendment → review → review → **amendment** (reason про формулировку критерия) → review → review → completed. Раунд 2 дал `changes_required` с blocking finding. Нарратив Context воспроизводится по журналу.
- Contract-индекса ADR в репозитории нет — поправка контракта от 2026-09-16 соответствует дереву, scope диффа не выходит за один файл.

Найденное:

**adr0011-transcript-claim-contradicts-open-question** (blocking) — `docs/adr/ADR-0011-contract-amendment-visibility.md:117` и `:130` объявляют, что транскрипт гейта не меняется и что «no question about transcripts arises», а `:175-181` и `:185-188` оставляют открытым ровно вопрос о транскрипте: «whether a sidecar gate should say anything when the field is present and differs». Обоснование в Decision 3 («changes what the party is *shown*, not what the gate refuses») этот вопрос не закрывает — sidecar-гейт по ADR-0008 D5 ничего не отказывает, его единственный выход и есть транскрипт, так что дихотомия «shown vs refuses» к нему неприменима. Consequences `:215` повторяет тот же абсолют («it puts no line in any transcript»). Запись одновременно утверждает, что вопроса нет, и называет его единственным genuinely open вопросом.

**adr0011-sidecar-sha-absolute** (advisory) — `:57`, `:124`, `:172`: «nothing binds it to a SHA at all» / «no SHA binds the contract». Контракт сайдкара лежит в истории самого сайдкара; ADR-0008 D7 называет её append-only «within the sidecar's own history», а CHANGELOG 0.3.0 прямо кладёт на неё scope discipline сайдкара. Защитима более узкая формулировка, которую Context уже даёт рядом — «no commit anywhere in the host». В нынешнем виде читается так, будто у контракта в сайдкаре истории нет вовсе, что подрывает и соседнее обещание из Decision 5 («a reader can compare that with the contract as it now stands»).

**adr0011-line-173-unwrapped** (advisory) — `:173` длиной 105 символов в документе, обёрнутом по ~79; след поздней правки без переноса.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a6b76dd83bd8a0dc46addfb902745f554506c1d1", "verdict": "changes_required", "findings": ["adr0011-transcript-claim-contradicts-open-question"], "advisory_findings": ["adr0011-sidecar-sha-absolute", "adr0011-line-173-unwrapped"]}
AGENTMARSHAL_VERDICT_END
