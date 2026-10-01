Проверил диф против контракта и `gate.py`.

Что сделано верно:
- Текст правила в `src/agentmarshal/journal/brief.py:331-335` слово в слово совпадает по смыслу с AGENTS.md:29-32 (`.agentmarshal/journal/` — не для имплементера, прочий файл под `.agentmarshal/` — только если его называет scope). AC1 выполнен.
- Старая формулировка «Do not edit anything under .agentmarshal/» в репозитории больше не встречается ни в одном источнике брифинга (только в контракте CR-121 и в артефакте ревью CR-117), и на её отсутствие есть тест `tests/test_brief.py:110`. Новый текст закреплён в `tests/test_brief.py:87-93`. AC3 выполнен.
- Остальной состав и порядок брифинга не тронуты; других генераторов брифинга с этим правилом нет.

Блокирующая находка: под заголовком «Rules enforced by AgentMarshal» остался пункт «Satisfy every acceptance criterion; they are the definition of done.» (`src/agentmarshal/journal/brief.py:330`), а gate этого не проверяет — в `src/agentmarshal/journal/gate.py` нет ни одной проверки acceptance criteria (слов `criteri*` в файле нет вовсе; есть только требование approving review и независимости ревьюера, строки 960-986). Это подтверждает и `docs/overview.md:171-174`: «required machine-readable acceptance criteria that the gate enforces» — это roadmap, «Today acceptance criteria are required by convention only (ADR-0004)». То есть ровно тот случай, который описывает AC2: правило, которого gate не проверяет, должно быть либо убрано из списка, либо перенесено под заголовок, не заявляющий enforcement. Хуже того, новый тест `tests/test_brief.py:149,155` прямо фиксирует это правило под заголовком enforcement, то есть закрепляет неверное утверждение. AC2 не выполнен.

Advisory: три теста (`tests/test_brief.py:87-93`, `:112-114`, `:159-164`) утверждают одну и ту же строку правила; при следующей правке формулировки ломаться будут все три. Достаточно было бы оставить проверку текста в одном месте, а в тесте про заголовки сверять только префикс пункта.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "95d723a966083ed2072638c991ceb2357eae93bf", "verdict": "changes_required", "findings": ["acceptance-rule-still-claims-gate-enforcement"], "advisory_findings": ["rule-text-asserted-in-three-tests"]}
AGENTMARSHAL_VERDICT_END
