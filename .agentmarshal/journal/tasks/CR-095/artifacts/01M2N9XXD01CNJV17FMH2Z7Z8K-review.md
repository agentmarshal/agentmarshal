Проверил ADR-0011 против пяти критериев контракта, сверил цифры с журналом (21 amendment-запись в 18 из 91 завершённой задачи — совпадает), сверил утверждения о механике с `gate.py` и `review.py` (чтение контракта из merge-base и из снапшота ревьюируемого коммита — подтверждается), и прогрепал абсолютные утверждения.

**Блокирующие**

`adr0011-dangling-proposal-link` — строка 22 ADR-0011 ссылается на `../proposals/022-amendments-invisible-to-the-reviewer.md`; такого файла в репозитории нет. `docs/proposals/` содержит 001–013 плюс README, а README текущего батча прямо говорит: «Twenty-two source files digested into thirteen proposals». То есть 022 — это номер исходного файла адоптера, который по политике `CONTRIBUTING.md` остаётся у репортёра и никогда не публикуется здесь. Критерий 5 требует, чтобы запись называла предложение, на которое отвечает; сейчас она называет несуществующий документ и даёт ссылку в никуда. Это ровно тот же класс дефекта, который поправила собственная амендмент-заметка контракта от 2026-09-16 («written from habit rather than from the repository»).

`adr0011-sidecar-refusal-unanswered` — решение 3 (строки 76–95) предписывает: «`validate` and the gate compare … and refuse when they disagree». Список «Sides and absence» под ним специально разбирает sidecar для *стороны чтения* («from the sidecar's working tree in a sidecar»), но не для *исхода*. При этом решение 5 той же записи говорит «a sidecar gate advises; it does not refuse», а ADR-0008 §5 — «The **gate runs advisory** … What the gate does not do in this placement is **decide a merge**». Так запись сама себе противоречит и противоречит ADR-0008: новый refusal объявлен безусловно, а sidecar-ответ, который здесь отличается, не дан отдельно. Критерий 2 требует именно этого.

`adr0011-no-change-at-all-overbroad` — строки 150–151: «A journal that never amends anything sees no change at all, and its transcripts stay byte-identical.» Это опровергается решением 4 той же записи: `reviewed_contract` добавляется в review-записи независимо от того, были ли амендменты. Журнал, который никогда ничего не амендит, всё равно получает новое поле в каждой новой review-записи, а значит и в её проекции (ср. строку транскрипта в `docs/sidecar.md:311`). Абсолютное утверждение шире механизма, который оно описывает — критерий 4.

**Совещательные**

`adr0011-every-sidecar-check-advisory` — строка 122 говорит «the notice that already says every sidecar check is advisory». Само уведомление формулирует уже: `Sidecar checks are advisory and decide no merge.` А ADR-0008 дважды отсылает к исключению ADR-0009 §4, и `docs/sidecar.md:391` подтверждает: `gate --findings` в sidecar решает и «never the advisory notice». §6 записи выводит findings-lane из области действия, так что фактического вреда нет, но «every» шире, чем механизм.

`adr0011-record-read-side-unstated` — та же строка 87 называет сторону чтения записей как «the amendment records from the journal it is gating». Это не сторона. В embedded-случае `gate.py:735-746` читает контракт из merge-base, а `load_task_status` (`gate.py:583`) читает записи из post-candidate-проекции — это разные деревья, и критерий 2 требует назвать сторону явно. Плюс «когда читается» остаётся без ответа для самой амендмент-транзакции: `gate.py:730` в journal-only-полосе вообще не заходит в ветку чтения контракта, так что gate не сверит секцию в том коммите, который её и пишет.

`adr0011-alternative-reason-garbled` — строки 155–158: «Rejected because it informs exactly one consumer: the implementer's brief, and every future reader of the contract, would still see a document with no history.» Двоеточие делает «the implementer's brief» тем самым единственным осведомлённым потребителем, тогда как по смыслу это ровно те, кто остаётся неосведомлённым. Причина отказа есть, но предложение читается наоборот — критерий 3 требует причину, которую читатель сможет разобрать.

Критерии 1 и 5 в остальном выполнены: дефект изложен точно (записи целы, SHA-привязка есть, не хватает именно видимости истории), собственные цифры проекта я проверил по журналу и они верны.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "0e598ba7292277c9100f81031794e9809c3fc5fe", "verdict": "changes_required", "findings": ["adr0011-dangling-proposal-link", "adr0011-sidecar-refusal-unanswered", "adr0011-no-change-at-all-overbroad"], "advisory_findings": ["adr0011-every-sidecar-check-advisory", "adr0011-record-read-side-unstated", "adr0011-alternative-reason-garbled"]}
AGENTMARSHAL_VERDICT_END
