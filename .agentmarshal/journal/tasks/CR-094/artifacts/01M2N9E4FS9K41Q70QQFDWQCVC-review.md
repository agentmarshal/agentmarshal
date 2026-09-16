Проверил снапшот: десять новых дайджестов, индекс и абзац в CONTRIBUTING.

Что сверил с кодом и журналом (не только с диффом):

- **Хэши:** все десять `Source:` — валидный 64-символьный lowercase hex, дубликатов нет; у старой партии (001–013) `Source:` отсутствует, что совпадает с заявлением README о том, что конвенция начинается с партии 2026-09-16.
- **Санитизация:** grep по именам репозиториев, хостам, URL, путям и идентификаторам задач вида `CR-NNN` в новых файлах и в строках индекса — пусто; единственные code spans это имена команд самого AgentMarshal и сами хэши. Профиль Adopter D описывает setup, а не продукт/клиента/домен.
- **Фактура диспозиций:** `doctor` действительно имеет ровно четыре проверки (`src/agentmarshal/doctor.py:119`), словарь activity — implementation/review/other (`src/agentmarshal/journal/records.py:508`), stderr ревьюера действительно отбрасывается на успешном выходе (`src/agentmarshal/journal/review.py:195`), шаблон CI действительно гоняет gate с `continue-on-error` и тянет задачу из имени ветки (`templates/github/agentmarshal-governance.yml`), leak-scan возвращает только категории (`src/agentmarshal/journal/capture.py:277`), README аутбокса ничего не говорит про исключение из staging (`src/agentmarshal/project.py:229`). Всё это подтверждает «девять из десяти всё ещё верны на default branch».
- **Числа про наш собственный журнал в 022** — 21 amendment-запись, 18 задач, 91 завершённая задача — сходятся точно; и CR-059 действительно amended между вторым и третьим раундом ревью, как описано.
- **016:** поведение с пинингом прозы действительно есть и покрыто тестами (`tests/test_review_launcher.py:772`), версия в `pyproject.toml` — 0.3.0, то есть утверждение «сборка с ветки рапортует ту же версию» верно.

Одна неточность, не блокирующая.

В `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:41` диспозиция помечена просто «accepted», а строка индекса (`docs/proposals/README.md:88`) обещает «0.4.0 carries the fix», хотя вторая просьба репортёра из блока `## Proposed` — печатать kept-at путь и для approved-ревью без findings — на default branch сознательно не выполняется: тест `test_a_clean_approval_keeps_nothing_and_says_nothing` (`tests/test_review_launcher.py:803`) фиксирует, что чистое одобрение не сохраняет прозу и ничего не печатает. В 018 и 020 частичное принятие помечено явно («in part», с причиной отложенной половины), здесь же репортёр по своему хэшу прочитает безусловное «accepted» и будет ждать в 0.4.0 того, чего проект делать не собирается.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "144e70a6e317ff91c0a5da52b214ea60f1440d13", "verdict": "approved", "findings": [], "advisory_findings": ["016-blanket-accepted-omits-approved-review-prose-ask"]}
AGENTMARSHAL_VERDICT_END
