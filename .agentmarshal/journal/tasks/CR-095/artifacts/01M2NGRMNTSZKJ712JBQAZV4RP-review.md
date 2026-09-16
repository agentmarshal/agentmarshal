Проверил запись против контракта, кода (`review.py`, `gate.py`, `records.py`, `brief.py`), журнала и названных решений ADR-0004/0006/0008.

Что подтвердилось фактически: gate действительно читает контракт из merge-base (`src/agentmarshal/journal/gate.py:735-746`), reviewer — из снапшота ревьюируемого коммита (`src/agentmarshal/journal/review.py:357-366`), валидация записей закрыта по полям (`src/agentmarshal/journal/records.py:219-227`), launcher всегда имеет контракт, а `review --reviewed-finding` сегодня отказывает и уводит на человеческий путь (`src/agentmarshal/cli.py:575-581`). Счёт «21 amendment across 18 of the 92 completed» сходится с журналом (22 файла amendment, минус собственный CR-095; 92 записи `-completed.json`), и CR-069 — ровно тот случай «поправка между вторым и третьим раундом, дальше судили третий и четвёртый».

CR095-F1 — в Decision 1 (`docs/adr/ADR-0011-contract-amendment-visibility.md:70-85`) рассуждение о «разных сторонах» верно только для embedded: утверждение «That is not the side the contract comes from — the review prompt takes the contract from the reviewed commit's snapshot» неверно в sidecar, где `launch_review` читает контракт из рабочего дерева sidecar-журнала (`src/agentmarshal/journal/review.py:357-360`), то есть с той же стороны, что и записи; следом и «rendering can name an amendment the contract text beside it does not yet reflect», и успокоение «the gate reads the contract from the merge-base tree» в sidecar не выполняются (gate там берёт контракт из дерева sidecar — `src/agentmarshal/journal/gate.py:740-742`). Сам документ знает про это в Decision 5 (строки 164-166), но в Decision 1 различие не оговорено, а критерий требует отвечать про sidecar отдельно везде, где ответ другой.

CR095-F2 — Decision 4 (строки 141-145) закрывает вопрос абсолютом «An absence is therefore never a violation and never a line anywhere», а Decision 5 и Decision 6 (строки 169-172, 179-182) объявляют absent-field case ещё не отвеченным и предпосылкой открытого вопроса про sidecar-gate; один из двух текстов неверен, и это ровно тот «never», который контракт просит быть защитимым.

CR095-A1 — строки 67-68 приписывают ADR-0006 опциональность атрибуции («who recorded it when the record names an actor, which ADR-0006 leaves optional»), но ADR-0006 как раз требует всегда выводить значение из окружения (git-identity как фолбэк), а опциональность — обратная совместимость схемы для записей, написанных до поля (`src/agentmarshal/journal/records.py:135-141`); все amendment-записи в журнале несут `recorded_by`.

CR095-A2 — «Every path that hands a contract to a party who must act on it» (строка 64) захватывает и бриф findings-задачи (`src/agentmarshal/journal/brief.py:264-276`, ветка пустого scope на строке 270), тогда как Decision 6 (строки 192-195) говорит, что про findings-полосу здесь ничего не решается; либо правило надо сузить, либо оговорку.

CR095-A3 — строки 148, 167 и 173 выбиваются из переноса по 79 символам, которого держатся остальные ADR (167 и 173 — около 105 и 120 символов): следы правки без переразбивки абзаца.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "2fe84cdfdaa34705ba61477ce69d11ad40a06ec1", "verdict": "changes_required", "findings": ["CR095-F1", "CR095-F2"], "advisory_findings": ["CR095-A1", "CR095-A2", "CR095-A3"]}
AGENTMARSHAL_VERDICT_END
