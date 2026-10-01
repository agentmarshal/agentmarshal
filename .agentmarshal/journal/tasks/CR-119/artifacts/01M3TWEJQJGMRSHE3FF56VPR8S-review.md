Разобрал задачу по пунктам.

**Что проверил и подтвердил:**

- `docs/sidecar.md:275` — заголовок теперь «Complete, and record what it consumed», в тон шагу 7 квикстарта («Record what the task consumed»); под ним не осталось ни одной фразы, подающей токены как стоимость (`grep cost` по файлу пуст), и commit message приведён к «record CR-001 economics».
- `docs/sidecar.md:402-403` — строка таблицы разбита, и новая формулировка сверена с CLI: `--reviewed-finding` действительно объявлен у `submit-review` (`src/agentmarshal/cli.py:121`), `--accepted-finding` у `accept` (`src/agentmarshal/cli.py:150`), оба — взаимоисключающие с `--commit`. Таблица осталась двухколоночной.
- Переносы в `docs/quickstart.md:459-466` и `docs/proposals/024-...md:67-68` легли в ту же ширину (~78), что и окружающий текст; таблицы и кодовые блоки не тронуты.
- `tests/test_gate.py:33-44` — docstring больше не утверждает, что версия не отличает релиз от сборки репозитория, объясняет `.dev0` после CR-112 и оставшуюся роль проверки `finding` (чекаут, собранный когда дерево ещё несло 0.3.0). Логика `released_030` не менялась — порядок кандидатов, проверка версии и проба `finding --help` те же.
- Сгенерированный README (`src/agentmarshal/project.py:265-272`) говорит именно то, что требует критерий, и сверен с источником: `docs/proposals/README.md:44` — секция «Tracking what happened to yours», `:56` — «source line begins with the batch of 2026-09-16», формулировка «as sent, in full and in lowercase hex» совпадает дословно; `Source:` реально присутствует в опубликованных дайджестах (проposals 014–024). Ни релиз, ни документ, ни секция из новых фраз не выдуманы.
- `tests/test_project.py:26-35` закрывает критерий про README; существующие тесты (`tests/test_journal.py`) не сверяют README побайтно, так что добавление текста их не ломает.

**Advisory (не блокирует):** новый абзац «## After sending» в `src/agentmarshal/project.py:267-272` свёрстан по ~70-73 символа, тогда как весь остальной текст этого же README переносится по ~79-80 (сравни `project.py:248`, `:254-257`). Задача в соседних файлах как раз выравнивала перенос «по ширине окружающего текста», а здесь новый текст выбивается — читателю сгенерированного файла видна ступенька.

CI целиком прогнать в этом снапшоте не вышло (не git-репозиторий, запуск `uv run` не разрешён), так что про «full CI sequence passes» сужу статически: новые строки укладываются в `line-length = 88`, новый тест типизирован под `mypy --strict`, изменения в строковых литералах ruff format не переформатирует.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b33dedbd1686a4b0a07ad195772161b9ce210257", "verdict": "approved", "findings": [], "advisory_findings": ["outbox-readme-paragraph-wrapped-narrower-than-surrounding-text"]}
AGENTMARSHAL_VERDICT_END
