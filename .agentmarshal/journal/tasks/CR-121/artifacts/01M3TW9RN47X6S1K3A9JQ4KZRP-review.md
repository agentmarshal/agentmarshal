Разобрал diff против контракта CR-121, AGENTS.md и `gate.py`.

Что сделано правильно:
- Новый текст правила (`src/agentmarshal/journal/brief.py:331-334`) совпадает по существу с правилом AGENTS.md:29-32 — ничего под `.agentmarshal/journal/` не трогаем, другой файл под `.agentmarshal/` только когда его называет scope. Критерий 1 выполнен.
- Под «Rules enforced by AgentMarshal» остался только scope-бюллетень, и это ровно то, что проверяет gate (`gate.py:804-820`). Старая формулировка про `.agentmarshal/` как целое ушла — gate такого правила не имеет. Критерий 2 по этому пункту выполнен.
- Тесты пинят и новый текст (`tests/test_brief.py:87-92`), и отсутствие старого (`tests/test_brief.py:110`), плюс раздельность секций. Критерий 3 выполнен. Других мест с этим текстом в репозитории нет (`grep` по `*.py/*.md/*.toml`), так что сломанных ассертов не остаётся.

Одна проблема, блокирующая.

**CR-121-acceptance-bullet-demoted** — в `src/agentmarshal/journal/brief.py:328-336` вставка новой секции «Rules the project follows:» перед journal-правилом утащила вместе с ним и бюллетень «Satisfy every acceptance criterion; they are the definition of done»: он теперь стоит после нового заголовка, то есть больше не входит в список правил, которые инструмент заявляет как enforced. Это не то, что просил контракт: критерий 4 требует, чтобы остальное содержимое брифинга осталось неизменным, а acceptance-правило как раз enforced — gate в diff-полосе валит кандидата без одобряющего review (`gate.py:898`, `gate.py:959-960`), именно через который и держатся acceptance criteria; CR-061 прямо перечислял его среди правил, которые «this tool itself enforces» (`.agentmarshal/journal/tasks/CR-061/contract.md:10`). Так что критерий 2 здесь не оправдывает перенос: правило проверяется, а брифинг теперь объявляет его просто практикой проекта. Починка — одна строка: вернуть бюллетень под «Rules enforced by AgentMarshal», сразу за scope-правилом, и начать новую секцию только с journal-правила. Заодно стоит дотестировать принадлежность этого бюллетеня секции, иначе ассерт `tests/test_brief.py:93` остаётся безразличным к заголовку.

Отдельно: критерий 4 про «full CI sequence passes» я проверить не смог — запуск `uv run pytest` / `ruff` / `mypy` в этой песочнице не разрешён, так что утверждать прохождение CI не берусь. По чтению кода изменение чисто строковое и ассерты нового теста логически выполняются на новом выводе.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7856f82872af4a36cdd76dc64af570503c660de8", "verdict": "changes_required", "findings": ["CR-121-acceptance-bullet-demoted"]}
AGENTMARSHAL_VERDICT_END
