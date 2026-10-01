Проверил diff против контракта CR-121, прочитав `src/agentmarshal/journal/brief.py:318-343`, `tests/test_brief.py:65-118`, `src/agentmarshal/journal/gate.py` и `AGENTS.md:29-32`.

Что сходится:

- Новое правило в брифинге дословно повторяет то, что говорит `AGENTS.md:29-32`: журнал не принадлежит имплементеру, а другой файл под `.agentmarshal/` меняется, только когда его называет scope. Критерий 1 выполнен.
- Под заголовком «Rules enforced by AgentMarshal» осталось одно правило — scope, — и gate его действительно проверяет (`gate.py:804-832`, `outside = [path for path in changed if not scope_covers(...)]`). Критерий 2 выполнен.
- Тесты покрывают и новый текст (`tests/test_brief.py:87-92`), и отсутствие старой формулировки (`tests/test_brief.py:110`). Критерий 3 выполнен.
- Остальной текст и порядок брифинга не изменились; других мест, где ассертится текст брифинга, в репозитории нет (grep по `tests/`, `src/`, `docs/`, `templates/`, `README.md` даёт только `tests/test_brief.py` и сам `brief.py`).

Запустить полную CI-последовательность в этой read-only среде не удалось — `uv run pytest` и прочие команды требуют подтверждения, так что четвёртый критерий в части «CI проходит» проверен только статически (длины строк в пределах 88, формат строковых конкатенаций соответствует black/ruff-стилю, ассерты не ссылаются на удалённый текст).

Два замечания, не блокирующие:

Пункт «Satisfy every acceptance criterion; they are the definition of done» молча переехал из списка enforced в «Rules the project follows» (`src/agentmarshal/journal/brief.py:330-335`), хотя gate фактически отказывает кандидату без одобряющего review или покрывающего acceptance-записи (`gate.py:890-960`), а именно там критерии приёмки и судятся. Критерий 2 такое перемещение разрешает, но для имплементера брифинг теперь занижает статус этого правила до соглашения.

Ассерт `".agentmarshal/" not in enforced` (`tests/test_brief.py:114`) закрепляет больше, чем требует контракт: gate реально держит `.agentmarshal/journal/` append-only (`gate.py:225-233`, `_is_append_only_evidence_path`), поэтому правдивое утверждение об этой проверке под заголовком enforced теперь сломает тест.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7856f82872af4a36cdd76dc64af570503c660de8", "verdict": "approved", "findings": [], "advisory_findings": ["acceptance-rule-demoted-from-enforced-list", "test-forbids-any-agentmarshal-path-under-enforced-heading"]}
AGENTMARSHAL_VERDICT_END
