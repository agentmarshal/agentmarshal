Проверил документ против контракта, критериев приёмки, названных ADR (0004, 0006, 0008) и фактов в коде и журнале.

Что подтвердилось как верное:

- Счёт амендментов точный: в журнале 22 amendment-записи в 19 задачах, из них одна — собственная CR-095; без неё ровно **21 запись в 18 задачах**, и **92** задачи с completion-записью (CR-095 не завершена). Формулировка «21 amendment records across 18 of the 92 tasks completed when this was written» проверяется поштучно.
- Механика описана точно: `gate.py:746` читает контракт из merge-base tree, `review.py:360-369` — из snapshot проверяемого коммита в embedded и из рабочего дерева sidecar-журнала в sidecar. Утверждение «nothing binds it to a SHA at all» для sidecar верное.
- Цитата ADR-0004 D3 («gates never parse prose») точна; `recorded_by` действительно optional по ADR-0006 и `records.py:139-146`; валидация записей действительно closed (`records.py:219-227`); все digest'ы — lowercase hex (`hexdigest()`, `[0-9a-f]{64}`); новые поля действительно приходили через bump схемы.
- Контракт текста отдаётся ровно двумя путями — review prompt и `brief`; `status`/`report` печатают только заголовок и scope. Так что «Every path … : the review prompt and the implementer's brief» — не шире механизма.
- Proposal 022 существует по указанной ссылке, ADR-0009 D3 процитирован верно.

Теперь то, что не проходит.

**F1 (блокирующее)** — Decision 6, третий буллет (строки 176-181) противоречит Decision 4 (строки 128-131) в пределах одного документа. D6 утверждает, что задача findings-lane «is amended like any other, so its reviews are handed the same rendering», а D4 утверждает, что «a review of a finding is handed no contract, so there is nothing to hash». По D1 рендеринг привязан именно к пути доставки контракта — значит, если контракт не выдаётся, то и рендерить не к чему. В коде это подтверждается: `cli.py:575-580` отказывает `review --reviewed-finding` («not supported in this release; use the human path»), а `submit-review` вообще ничего не выдаёт рецензенту. По ADR-0009 D3 последняя рецензия в этой полосе обязана быть finding-bound — то есть противоречие покрывает ровно все рецензии findings-lane, а не краевой случай. Реализующая задача не сможет понять, рендерить ли историю амендментов на этом пути. Это же ломает критерий «no absolute claim … broader than the mechanism it describes», и сверх того трогает объявленный контрактом non-goal «Anything about the findings lane».

**A2 (совет)** — Decision 1 (строки 70-77) сознательно вводит асимметрию: записи читаются из рабочего дерева, а контракт — из snapshot'а проверяемого коммита, «including an amendment recorded after the candidate was built». Документ не называет прямое следствие: рецензенту будет показана запись об изменении критерия, которого в выданном ему тексте контракта нет, а рендеринг по собственному признанию «does not answer *what* changed» (строки 86-88). Свести одно с другим рецензент не может, и запись не говорит, как это читать. Критерий «what happens when it changes» отвечен для записей, но не для этого видимого рассогласования.

**A1 (совет)** — ADR-0008 назван материалом контракта и определяет всё, на чём держится sidecar-половина рассуждения (placement, advisory-гейт, «the same commands, the same record schema, the same validation»), но ни разу не назван и не слинкован в записи, тогда как ADR-0004, ADR-0006 и ADR-0009 процитированы ссылками. Особенно это заметно в строке 157, где фраза «a change to what a sidecar gate is» опирается на ADR-0008 D1/D5, не называя их.

**A3 (совет)** — Decision 4, строка 125: «Adding it raises the review record's schema number» сказано без оговорки, которую ADR-0004 уже установил для schema 4 («writers stamp 4 only when those fields are used and keep 3 as the floor for all other new records»). Отсюда остаётся неотвеченным, какую схему штампует рецензия без `reviewed_contract`. При этом Decision 6 заявляет «One question is genuinely open» — а это вторая, и она не названа.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "3fc6328e5e272ffd26f7e6c9d096f48c48056c4f", "verdict": "changes_required", "findings": ["F1-findings-lane-rendering-contradicts-d4"], "advisory_findings": ["A1-adr-0008-named-but-uncited", "A2-post-snapshot-amendment-unreconcilable", "A3-schema-floor-question-unnamed"]}
AGENTMARSHAL_VERDICT_END
