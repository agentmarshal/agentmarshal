Проверил всё по критериям контракта — читал только файлы, ничего не менял. Запустить CI не смог: в этой песочнице выполнение `uv run`/`pytest`/`ruff` заблокировано (permission denied), поэтому последний критерий («the full CI sequence passes») проверен статически, а не прогоном. Говорю это прямо, чтобы не выдавать непроверенное за проверенное.

Что проверено и сходится:

- `docs/sidecar.md:275` — заголовок теперь «Complete, and record what it consumed», что совпадает со словарём шага 7 quickstart (`docs/quickstart.md:419` «Record what the task consumed»); `grep` по «cost» в sidecar.md не даёт ни одного вхождения, commit-message в примере приведён к «record CR-001 economics». Устаревших anchor-ссылок на прежний заголовок в репозитории нет.
- Строка таблицы про `submit-review`, `accept` (`docs/sidecar.md:402`) сверена с CLI: `--reviewed-finding` объявлен у `submit-review` (`src/agentmarshal/cli.py:121`), `--accepted-finding` — у `accept` (`src/agentmarshal/cli.py:150`), оба в mutually exclusive группе с `--commit`, и `_placement` для обеих команд вызывается без `require_host`, так что формулировка «record over the sidecar's own evidence» корректна.
- Переносы в шаге 7 quickstart и в проposal 024 приведены к ширине окружающего текста (~78), таблицы и code blocks не тронуты.
- Docstring `released_030` (`tests/test_gate.py:34`) теперь верен: `pyproject.toml:3` — `0.5.0.dev0`, а `--version` печатает чистую версию (`cli.py:88`), так что сравнение `!= "0.3.0"` действительно исключает локальный build; объяснение, что именно ещё отсекает проба `finding --help`, согласуется с историей (до 0.4.1 дерево несло версию `0.3.0` без суффикса).
- Новая секция «After sending» в `_OUTBOX_README` согласована с `docs/proposals/README.md:44` («Tracking what happened to yours», «The source line begins with the batch of 2026-09-16»), и `grep` подтверждает, что `Source:` несут именно proposals 014–024. Тест `tests/test_project.py:27` проверяет наличие всех трёх опорных подстрок в сгенерированном README — они в шаблоне есть, так что тест пройдёт.

Два замечания, не блокирующих:

OUTBOX-README-WRAP-WIDTH — в `src/agentmarshal/project.py:265-272` новая секция «After sending» завёрнута по ~70-73 символа, тогда как весь остальной текст `_OUTBOX_README` завёрнут по ~79-80; в задаче, одним из критериев которой как раз является «wrapped to the width of the text around them», сгенерированный текст сам получился уже окружения.

OUTBOX-README-INDEX-NOT-LOCATED — там же, `src/agentmarshal/project.py:272`: README отправляет читателя к «The proposals index», не называя, где он лежит (`docs/proposals/README.md` в upstream-репозитории), хотя соседний абзац хотя бы говорит «the upstream project's CONTRIBUTING». Адоптер, который «did not find it and asked», по этой фразе снова должен догадываться, где искать digests.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b33dedbd1686a4b0a07ad195772161b9ce210257", "verdict": "approved", "findings": [], "advisory_findings": ["OUTBOX-README-WRAP-WIDTH", "OUTBOX-README-INDEX-NOT-LOCATED"]}
AGENTMARSHAL_VERDICT_END
