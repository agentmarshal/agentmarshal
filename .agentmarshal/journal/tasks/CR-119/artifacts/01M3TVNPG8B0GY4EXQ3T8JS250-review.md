Проверил все пять пунктов acceptance против файлов в снапшоте.

Что сошлось:

- `docs/sidecar.md:275` — заголовок теперь «Complete, and record what it consumed», та же формулировка, что в `docs/quickstart.md:418` («Record what the task consumed»); commit-сообщение в блоке (`docs/sidecar.md:297`) тоже приведено к «record CR-001 economics». Утверждений про cost в файле больше нет.
- Строка таблицы `submit-review`, `accept` (`docs/sidecar.md:402`) сверена с CLI: `src/agentmarshal/cli.py:119-121` и `147-150` — у обеих команд обязательная mutually-exclusive группа `--commit` / `--reviewed-finding` и `--commit` / `--accepted-finding`; findings-lane опубликована в 0.4.0 (`CHANGELOG.md:60-69`). Описание точное. Старый anchor `#complete-and-record-what-it-cost` нигде не используется — проверил ссылки в `docs/`, `README.md`, `src/`, `tests/`.
- Переносы: новые строки в `docs/quickstart.md:462-466` — 72/34/71/71 символов, соседние строки абзаца 76/77/72; в `docs/proposals/024-...md:67-68` — 68/38 при соседних 75–77. Таблицы и code blocks не тронуты, строк >88 нет нигде в изменённых файлах.
- Docstring `released_030` (`tests/test_gate.py:34-42`) больше не утверждает неразличимость версий — и это верно: дерево отдаёт `0.5.0.dev0` (`pyproject.toml:3`). Объяснение, зачем остаётся проба `finding --help` (сборка из чекаута времён, когда дерево ещё несло `0.3.0`, команду уже знала), соответствует истории. Логика функции в диффе не менялась.
- Outbox README (`src/agentmarshal/project.py:264-271`) говорит, как сопоставить отправленный finding: хеш файла в строке `Source:`. Формат сверен с реальным digest — `docs/proposals/024-...md:3` несёт `**Source:** sha256:...`, раздел «Tracking what happened to yours» существует (`docs/proposals/README.md:44`). Тест `tests/test_project.py:26-35` это закрепляет и использует уже существующий хелпер `_scaffold_outbox`; других ассертов на текст README (кроме `tests/test_journal.py:1961` на «Sanitize at source») нет, так что они не ломаются. Непубликованных релизов/задач/документов новые формулировки не называют.

Одно замечание, не блокирующее: в `src/agentmarshal/project.py:266` сказано, что строка `Source:` есть у «each published digest», тогда как сам индекс, на который этот же абзац ссылается, оговаривает, что хеш появился с партии 2026-09-16, и digests 001–013 строки `Source:` не несут (проверил — она есть только в 014–024). Для нового адоптера это практически безразлично, но утверждение шире, чем published факт.

Полную последовательность CI (`uv run pytest`, `ruff check`, `ruff format --check`, `mypy`, `agentmarshal validate`) в этом окружении запустить не удалось — выполнение команд здесь ограничено; проверил статически: длины строк новых Python-фрагментов 78/80/82 при `line-length = 88`, em dash в том же строковом литерале уже встречается выше, импортов и типов тест не добавляет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c058320f0ac0250e0592db45d5313f808c65321d", "verdict": "approved", "findings": [], "advisory_findings": ["outbox-readme-overstates-source-line-coverage"]}
AGENTMARSHAL_VERDICT_END
