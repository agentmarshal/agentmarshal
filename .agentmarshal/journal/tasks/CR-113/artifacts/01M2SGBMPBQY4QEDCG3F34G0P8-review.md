**Вердикт: changes_required.** Сам digest 024 сделан хорошо, но заявленная правка «tokens are not cost» доведена до конца только в одном месте.

**Что в порядке:**
- 024 написан по-английски, под существующим псевдонимом Adopter D с тем же профилем, `Source` указан как sha256, у каждого из трёх предложений есть disposition с обоснованием.
- 0.4.0 уже есть в CHANGELOG (2026-09-18), так что ссылка на неё корректна.
- `--outcome` действительно принимается как свободная строка: словаря значений нет, `report` его не агрегирует.
- Строка в `docs/README.md` на месте.

**Blocking:**
- **QS-COST-FRAMING** — `docs/quickstart.md:418`, `420`, `459`, `463`: новый абзац «Token counts are what the record measures, not what a provider charges» стоит внутри шага «### 7. Record what the task cost». Этот шаг по-прежнему начинается с «a task's cost is known when it ends» и дальше говорит о записи токенов как о «Recording the cost» и «the cost would live in a working tree». То есть quickstart сам себе противоречит, и остаётся та подача, которую digest признаёт ошибкой («calling the token record what a task cost»).
- **README-TOKEN-COSTS** — `README.md:53` всё ещё говорит «To see how the project actually evolved, token costs and all, read the journal». Это снова называет измерения токенов в журнале стоимостью, хотя правка в строке 32 и digest утверждают, что README так больше не говорит.

**Advisory:**
- **INDEX-EACH-DIGEST-HASH** — в `docs/proposals/README.md` новый абзац про `sha256sum` утверждает, что «each digest names the file it came from that way». Это противоречит разделу «Tracking what happened to yours» чуть выше: там сказано, что proposals до батча 2026-09-16 хэша не имеют. К тому же абзац почти дословно повторяет инструкцию из этого же раздела.
- **DIGEST-SIX-TIMES** — в `024-provider-quota-stop-cannot-be-recorded.md` проза утверждает «counted in tokens, the rejected model is six times cheaper». Этого соотношения нет среди процитированных измерений: ~0.67M против >27.5M дают порядка 40 раз, и эти две величины вообще не сопоставимы. Цифра должна либо попасть в дословные measurements, либо уйти из текста.
- **QS-OUTCOME-UNCHECKED** — `docs/quickstart.md:446`: «free text that the tool neither checks nor counts» сказано слишком сильно. Флаг `--outcome` обязательный, а `_validate_session_record` в `src/agentmarshal/journal/records.py:512` отклоняет пустую строку. Формулировка из digest, «neither checks the value», точнее.
- **SIDECAR-COST-HEADING** — `docs/sidecar.md:275` («Complete, and record what it cost») говорит так же, но файл вне scope. Стоит взять в следующую задачу.

CI я не запускал: команду `uv run agentmarshal validate` не одобрили, поэтому последний пункт acceptance (полный CI проходит) я не проверил.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "70fe23c5c74d5257970c3b561ab7d07483e3c605", "verdict": "changes_required", "findings": ["QS-COST-FRAMING", "README-TOKEN-COSTS"], "advisory_findings": ["INDEX-EACH-DIGEST-HASH", "DIGEST-SIX-TIMES", "QS-OUTCOME-UNCHECKED", "SIDECAR-COST-HEADING"]}
AGENTMARSHAL_VERDICT_END
