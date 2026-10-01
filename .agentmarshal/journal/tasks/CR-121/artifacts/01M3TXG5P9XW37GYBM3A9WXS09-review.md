Я проверил diff против контракта и против `gate.py`.

**Что сверено:**

- **Критерий 1** — `src/agentmarshal/journal/brief.py:334-337` печатает правило ровно так, как его формулирует `AGENTS.md:28-31`: ничто под `.agentmarshal/journal/` не принадлежит имплементатору, а другой файл под `.agentmarshal/` меняется только когда его называет scope задачи. Старая, более строгая строка ушла.
- **Критерий 2** — каждое правило под заголовком «Rules enforced by AgentMarshal» действительно проверяется гейтом: scope — `gate.py:804-829` (`outside = [path for path in changed if not scope_covers(effective, path)]`, контракт читается из merge-base, то есть кандидат не расширяет свой scope); append-only записей **и артефактов** — `gate.py:1002-1017` вместе с `_is_append_only_evidence_path` (`gate.py:320-325`), которая покрывает и `tasks/*/artifacts/*`; approving review именно этого коммита — `gate.py:890-897` (фильтр по `reviewed_commit == resolved_commit` плюс `verdict == "approved"`). «Satisfy every acceptance criterion» переехал под «Rules the project follows» — верно, гейт критерии не читает, их судит ревьюер; туда же попало journal-правило.
- **Критерий 3** — `tests/test_brief.py:89-112` утверждает текст нового правила и отсутствие старой формулировки `Do not edit anything under .agentmarshal/` в брифинге.
- **Критерий 4** — diff трогает только блок правил, остальной текст брифинга не изменён; `tests/test_brief.py:115-154` проверяет распределение правил по заголовкам, а полный текст каждого правила утверждается в одном месте (в heading-тесте journal-правило используется только как короткий префикс-локатор). Строки обоих файлов укладываются в `line-length = 88`. Посторонних копий этого текста в репозитории нет — grep по `tests/`, `docs/`, `templates/`, `README.md`, `AGENTS.md` на «Rules enforced», «definition of done», «implementer's to edit» даёт только `brief.py` и `test_brief.py`, так что других падающих ассертов эта правка не создаёт. Подстановки в тестах я сверил посимвольно со склейкой литерала в `brief.py` — все подстроки совпадают, включая пробелы на стыках переносов, и разбиение по `"\n\n"` даёт ровно те два абзаца правил.

Оговорка: прогнать сам CI-набор (`pytest`, `ruff`, `mypy`, `agentmarshal validate`) в этой песочнице не удалось — запуск команд был отклонён, так что проверка критерия 4 в части «full CI sequence passes» у меня статическая, а не исполненная. Блокирующих и advisory-замечаний нет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5a6a6f89816cb3c0ba1fcb2917135a5f41006687", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
