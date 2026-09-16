Проверил запись против контракта и против репозитория.

**Что сверил с кодом и журналом (всё сходится):**
- «the gate reads the contract from the merge-base tree» — `src/agentmarshal/journal/gate.py:735`, `:746`.
- «the prompt's contract comes from the reviewed commit's snapshot», а в sidecar — из рабочего дерева sidecar-журнала — `src/agentmarshal/journal/review.py:359-368`.
- «Record validation is closed» — `src/agentmarshal/journal/records.py:134`, таблица `_ALLOWED`-полей.
- Прецедент версии («writers stamp 4 only when those fields are used and keep 3 as the floor») — ADR-0004, строки 148-151. `_SUPPORTED_SCHEMAS = {1,2,3,4}`.
- «lowercase hex every other digest in this journal uses» — `records.py:148`, `:321`.
- «who recorded it, when the record names an actor» — `recorded_by` опционально для всех типов записей (`records.py:136-142`); у `amendment` собственного actor-поля нет, формулировка корректна.
- Счётчики: в журнале 22 amendment-записи в 19 задачах и 92 `*-completed.json`. За вычетом собственной поправки CR-095 получается ровно **21 запись в 18 задачах из 92 завершённых** — цифра в ADR верна (контракт и proposal говорят «91», но они писались раньше; ADR точнее, не расхождение).
- ADR-0008 подтверждает sidecar-утверждение: evidence привязан к SHA хоста только «within the sidecar's own history» (строки 141-152).

Критерии 1, 3, 5 закрыты полностью. Ниже — три необязательных замечания.

**ADV-1 — `findings-lane-claim-vs-left-open`.** Decision 3 (строка 83) утверждает «This decision adds no check and no line to the gate, in any placement and **on any lane**», а Decision 1 (строка 52) говорит про «The review prompt» без оговорок — оба высказывания решают что-то за findings lane. Раздел «Left open» (строки 132-134) и Non-Goals контракта («Anything about the findings lane») говорят ровно обратное: этот lane запись не решает. Либо снять «on any lane» и квалифицировать Decision 1, либо признать в «Left open», что gate-строка для findings lane всё-таки решена (её нет).

**ADV-2 — `reviewed-contract-optionality-unreachable`.** Decision 4, строки 110-117: абзац выше постановляет, что «a writer stamps the new schema only on a record that carries the field and keeps the current one as the floor». Значит запись `submit-review` без `reviewed_contract` получит текущую схему (4), а не новую — и названный случай оптиональности («the case it is optional for is the human path») внутри новой схемы не достижим ни одним писателем. Практический ответ на «что при отсутствии» («never a violation and never a line anywhere») при этом остаётся верным; поправить нужно обоснование, а не поведение.

**ADV-3 — `unwrapped-lines`.** Строки 45 и 168 не перенесены и уходят далеко за ширину, на которой свёрстан весь остальной файл (78 символов) — след вставленных позже предложений («That matters most in the case that occurs most:», «The defect is invisibility, not insufficient ceremony.»). Чисто косметика.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "2f72cb0b32e94a475b500ebf71b80c400deed815", "verdict": "approved", "findings": [], "advisory_findings": ["findings-lane-claim-vs-left-open", "reviewed-contract-optionality-unreachable", "unwrapped-lines"]}
AGENTMARSHAL_VERDICT_END
