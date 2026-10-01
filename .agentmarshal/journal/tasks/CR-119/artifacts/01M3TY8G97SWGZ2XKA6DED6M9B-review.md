Проверил дифф против контракта и реального состояния репозитория.

**Что сошлось:**
- `docs/sidecar.md:276` — заголовок теперь «Complete, and record what it consumed», что совпадает с формулировкой шага 7 quickstart'а (`docs/quickstart.md:418` «Record what the task consumed»); слово «cost» в sidecar.md больше не встречается нигде, сообщение коммита в блоке приведено к quickstart'овскому «record CR-001 economics».
- Строка таблицы `docs/sidecar.md:402` проверена по самому парсеру: `submit-review` имеет взаимоисключающую обязательную группу `--commit` / `--reviewed-finding` (`src/agentmarshal/cli.py:120-121`), `accept` — `--commit` / `--accepted-finding` (`src/agentmarshal/cli.py:149-150`). Ни `submit_review.py`, ни `acceptance.py` не трогают git, так что «Unchanged under `--commit`» и перенос clause про host git facts в соседнюю строку корректны.
- Переносы: в шаге 7 quickstart'а и во всём `024-...md` ни одна строка прозы не выходит за ~79 символов; таблицы и код-блоки не тронуты.
- Докстринг `released_030` (`tests/test_gate.py:33-43`): версия в `pyproject.toml` действительно `0.5.0.dev0` (CR-112, запись в CHANGELOG под 0.4.1), а лане findings с командой `finding` — фича 0.4.0, т.е. сборка из дерева, ещё носившего `0.3.0`, уже знала команду. Объяснение зонда точное, логика теста не изменена.
- Outbox README (`src/agentmarshal/project.py:263-274`): формат `Source:` совпадает с реальными дайджестами (`**Source:** sha256:<hex>` в 014–024), оговорка «Since the batch of 2026-09-16» верна — у 001–013 source-строки нет (ровно та ловушка, на которую ранее указывал ADV-002 из CR-094). URL и ветка совпадают с `pyproject.toml:31` и `.github/pull_request_template.md`. Раздел «Tracking what happened to yours» существует (`docs/proposals/README.md:44`), 0.4.1 опубликован (CHANGELOG, 2026-09-24). Все семь ассертов нового теста выполняются.

Блокирующего не нашёл. Три замечания к качеству, не к корректности:

Новый тест `tests/test_project.py:43` утверждает, что сгенерированный README называет раздел «Tracking what happened to yours», но нигде не проверяется, что этот раздел всё ещё есть в `docs/proposals/README.md` — переименование заголовка апстримом оставит тест зелёным, а у адоптеров в репозиториях — ссылку в пустоту.

Ассерт `tests/test_project.py:39` (`"search through the files under"`) привязан к случайной формулировке, а не к факту: безобидная переписка фразы уронит тест, ничего не потеряв по сути, тогда как критерий приёмки говорит про факт, а не про слова.

Протокол сопоставления по sha256 теперь изложен в трёх местах — `CONTRIBUTING.md:60-67`, `docs/proposals/README.md:44-69` и шаблон `_OUTBOX_README` в `src/agentmarshal/project.py:266-274` — и ничто не держит их в согласии; именно на такое расхождение (безусловное утверждение про хэш против партий 001–013) уже ловили CR-094 и CR-113.

Полную CI-последовательность (`validate` / `pytest` / `ruff check` / `ruff format --check` / `mypy`) в этом снапшоте прогнать нечем — ни `uv`, ни `ruff`, ни `pytest` не установлены; проверял чтением. Форматирование нового `assert (...) in readme` соответствует тому, что black/ruff выдаёт при явных скобках вокруг операнда, длина строки 81 < 88.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ef69a4f83ce9b84430c3dcc8becf1a7f226b8e68", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-SECTION-TITLE-NOT-VERIFIED", "ADV-ASSERTION-PINS-INCIDENTAL-PROSE", "ADV-PROTOCOL-RESTATED-IN-THREE-PLACES"]}
AGENTMARSHAL_VERDICT_END
