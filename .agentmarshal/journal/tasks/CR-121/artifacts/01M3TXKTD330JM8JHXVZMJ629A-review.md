Я прошёл контракт по критериям и сверил классификацию правил с `src/agentmarshal/journal/gate.py`.

**Критерий 1** — правило журнала. `src/agentmarshal/journal/brief.py:334-337` печатает ровно то, что говорит `AGENTS.md:29-32`: под `.agentmarshal/journal/` имплементер ничего не правит (журнал append-only и пишется командами `agentmarshal`), а другой файл под `.agentmarshal/` меняется только когда его называет scope задачи. Формулировки эквивалентны.

**Критерий 2** — классификация по заголовкам. Под «Rules enforced by AgentMarshal» остались ровно три правила, и каждое действительно проверяется гейтом: scope — `gate.py:804-833` (`outside = [path for path in changed if not scope_covers(...)]`); append-only записей и артефактов — `gate.py:1006-1017` вместе с `_is_append_only_evidence_path` (`gate.py:320-326`), который покрывает и `/records/`, и `/artifacts/`; одобряющий ревью именно этого коммита — `gate.py:891-963`, где ревью фильтруются по `reviewed_commit == resolved_commit`. Под «Rules the project follows» — acceptance criteria (гейт их не проверяет, он требует ревью, а критерии судит ревьюер) и правило журнала. Совпадает с тем, что требует контракт после поправки от 2026-10-01.

**Критерий 3** — `tests/test_brief.py:89-112` утверждает точный текст нового правила и отсутствие старой формулировки `Do not edit anything under .agentmarshal/` в брифинге; `tests/test_brief.py:115-154` проверяет, что каждое правило лежит под своим заголовком и не лежит под чужим.

**Критерий 4** — диф трогает только блок правил, остальное содержимое брифинга не изменилось. Текст каждого правила утверждается одним тестом (в `test_brief_lists_each_rule_under_its_heading` правило журнала фигурирует только префиксом `- Nothing under .agentmarshal/journal/` как метка принадлежности, а не повторением текста). Строки укладываются в `line-length = 88` из `pyproject.toml:48`, форматирование соответствует ruff format, типизация тестов не затронута. Запустить CI в этом read-only снапшоте я не мог — это сверка статическая.

Одно необязательное замечание ниже.

Имя и docstring теста `test_brief_prints_complete_contract_and_governance` (`tests/test_brief.py:65-70`) теперь шире того, что он проверяет: из него убраны оба утверждения про правила, и слово «governance» в имени больше ничем не покрыто — осталась проверка контракта и scope-секции.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5a6a6f89816cb3c0ba1fcb2917135a5f41006687", "verdict": "approved", "findings": [], "advisory_findings": ["stale-test-name-governance"]}
AGENTMARSHAL_VERDICT_END
