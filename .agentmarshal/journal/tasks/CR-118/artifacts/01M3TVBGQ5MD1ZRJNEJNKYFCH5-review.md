Разобрал дифф по контракту CR-118: проверил три файла из scope, сверил заявления о механизме с кодом (`records.py:498-523`, `records.py:364,383,414,426,470,481`, `validate.py:182-212`, `gate.py:890`, `status.py:135`, `records.py:1079`) и с опубликованной историей (`CHANGELOG.md:11-29`, `UPGRADING.md:3-48`, журнальные контракты CR-114 и CR-115).

Что сходится:

- `read_records` действительно валидирует каждую запись при чтении, gate читает только задачу-кандидата, а whole-journal `validate` печатает одну `FAIL`-строку на задачу и `continue`-ит — поэтому «three records, across two tasks», «one failure line per affected task» и «the remaining 280 tasks were reported OK» (282 − 280 = 2) согласованы между собой и с `validate.py:182-212`; `validate: journal invalid` есть в `cli.py:766`.
- Числа 3 записи / 11 вхождений / две задачи совпадают с контрактом CR-114 (`eleven occurrences across three records written by 0.1.0`, `both tasks are closed`). Фраза «two review records» в том же контракте — про две `FAIL`-строки, и дайджест правильно не наследует эту двусмысленность.
- Отгруженный набор `Cc`, `Cs`, `Zl`, `Zp` + bidi и один предикат `forges_rendered_text` на records / contract headers / `validate`-рефы — подтверждается кодом; `isprintable()` в `src/` больше нигде нет.
- Профиль «Adopter A (Python web service on Linux)» совпадает с тем, что индекс уже использует для A в 001–010; hash-строка, формат заголовка, батч-таблица и строка в `docs/README.md` соответствуют соседям.

Измерения (1918 / 732 / 282) сверить verbatim не могу: исходник адоптера в снапшоте отсутствует, он застейджен приватно. CI тоже не прогнал — запуск `uv run` и python в этой сессии не разрешён; изменение чисто markdown, тестов, читающих `docs/`, в `tests/` нет.

Блокирующее замечание одно.

`docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md:82` утверждает «The shipped set adds `Cs` to the reporter's list», то есть что единственное расхождение отгруженного правила с предложением адоптера — это `Cs`. Это неверно: предложение адоптера в этом же файле (строки 60–61) перечисляет bidi-символы как `U+202A–U+202E, U+2066–U+2069`, а отгруженный `_BIDIRECTIONAL_CONTROLS` (`src/agentmarshal/journal/records.py:507-509`) содержит ещё U+061C, U+200E и U+200F — и поправка в контракте CR-114 («Amended 2026-09-24 (the refused set)») прямо фиксирует оба добавления как «two classes joined it during the work». Reporter, читающий disposition, решит, что его список bidi взяли дословно. Исправляется одной оговоркой.

Два совета, не блокируют.

`docs/proposals/025-...md:95-97` подаёт как факт, что `validate` релиз-кандидата прогнали read-only по журналу адоптера и он прошёл, со ссылкой «(CR-115)». В журнале CR-115 следов этого прогона нет: `completed`-запись (`01M38SSKHMQS9FQ2YYTM0TDHMZ-completed.json`) не несёт ни заметки, ни артефакта, хотя пятый критерий самого CR-115 требует «the run is reported in the task's completion», и последний review задачи (`01M38SQ1TJF47G2RRSP08ZF4P4-review.md`) отдельно просил это зафиксировать. По правилу README («A disposition without that column is a promise; with it, it is a place to look») ссылка ведёт в место, где искать нечего. CR-115 закрыт и append-only, так что в scope CR-118 это не правится — но формулировку стоит сделать такой, какую журнал подтверждает.

`docs/proposals/README.md:74-75` описывает A как «the reporter of the first batch — proposals 001, 002, 005, 006, 007 and 010 came from the same journal». В таблице батча 2026-08-30 в том же файле за A записаны ещё 003, 004 и 012, так что перечисление читается как исчерпывающее, не будучи им. Формулировка взята из Context контракта, поэтому это именно совет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "346d70a700311694b2f1537321ae8199a2e15fe8", "verdict": "changes_required", "findings": ["shipped-set-delta-names-only-cs"], "advisory_findings": ["release-check-claim-has-no-recorded-run", "index-omits-three-of-adopter-a-proposals"]}
AGENTMARSHAL_VERDICT_END
