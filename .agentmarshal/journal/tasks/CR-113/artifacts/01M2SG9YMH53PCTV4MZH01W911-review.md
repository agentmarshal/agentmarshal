Ревью CR-113 на коммите `70fe23c5`: блокирующих замечаний нет, вердикт **approved**, пять advisory-замечаний.

**Критерии приёмки, проверенные по snapshot:**
- **Заголовок 024.** Строка Reporter дословно совпадает с профилем Adopter D из 014–023. Source дан как sha256, и по каждому из трёх предложений есть disposition с обоснованием.
- **Индекс proposals.** В `docs/proposals/README.md` появилась таблица батча 2026-09-18 с колонкой Where. Там же сказано, как найти свой digest через `sha256sum`. `docs/README.md` дополнен по amendment.
- **Quickstart не приписывает tool'у лишнего.** Я проверил код: `--outcome` принимает свободный текст, и `_validate_session_record` требует только непустую строку (`src/agentmarshal/journal/records.py:512`). `report.py` значение `outcome` вообще не читает. Значит, фраза «tool neither checks nor counts» верна по смыслу: словарь значений не проверяется.
- **Ссылки на релизы.** Упомянут только 0.4.0, и он есть в `CHANGELOG.md` (запись от 2026-09-18). Итоговый рework прямо назван «not scheduled in any published release».
- **CI я не запускал.** В окружении нет `uv`, а snapshot не является git-репозиторием. Diff меняет только документацию, а тестов, которые читают docs, в `tests/` нет.

**Advisory-замечания:**

1. **README-TOKEN-COSTS-REMAINS.** `README.md:53` всё ещё говорит «token costs and all, read the journal». Это та же подача токенов как стоимости, которую убрали в строке 32. Поэтому утверждение 024 «the README no longer calls them what each task cost» выполнено только наполовину.
2. **QUICKSTART-STEP7-STILL-FRAMES-COST.** В `docs/quickstart.md` шаг 7 по-прежнему называется «Record what the task cost». Рядом остались фразы «a task's cost is known when it ends», «the cost would live in a working tree» и «Recording the cost is a step». Всё это противоречит новому абзацу «Token counts are … not what a provider charges» внутри того же шага.
3. **DIGEST-UNSOURCED-RATIO.** В `docs/proposals/024-…md` есть фраза «counted in tokens, the rejected model is six times cheaper». Это числовое утверждение, но его нет среди дословно цитируемых measurements. Из приведённых цифр (~0.67M против >27.5M) коэффициент 6 не получается, так что читатель не может его проверить.
4. **INDEX-HASH-MATCH-DUPLICATED.** Новое предложение про `sha256sum` в `docs/proposals/README.md` повторяет уже существующий раздел «Tracking what happened to yours» («Hash your outbox file, search this directory…»). Лучше было сослаться на него, а не объяснять заново рядом.
5. **DEFERRAL-REASON-MISATTRIBUTED.** 024 откладывает поле «for the reason proposal 018's cost field is». Но 018 откладывает поле cost по другим причинам: деньги невозможно заверить, и непонятно, как делить стоимость между задачами. 024 же приводит в качестве причины изменение схемы и нагрузку от апгрейда на 0.4.0.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "70fe23c5c74d5257970c3b561ab7d07483e3c605", "verdict": "approved", "findings": [], "advisory_findings": ["README-TOKEN-COSTS-REMAINS", "QUICKSTART-STEP7-STILL-FRAMES-COST", "DIGEST-UNSOURCED-RATIO", "INDEX-HASH-MATCH-DUPLICATED", "DEFERRAL-REASON-MISATTRIBUTED"]}
AGENTMARSHAL_VERDICT_END
