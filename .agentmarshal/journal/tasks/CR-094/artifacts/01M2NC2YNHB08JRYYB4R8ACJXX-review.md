Проверил снапшот на коммите 4d2adb0389d6efd5c7ae666f912f03cc2fe20413 против контракта CR-094.

Что сошлось:

- Десять дайджестов 014–023, у каждого есть `Observed on: 0.3.0`, блок «Measurements, as reported», раздел `## Proposed` и `## Disposition` с обоснованием — формат совпадает с более ранними 001–013.
- Source-строки: десять уникальных sha256, полный нижний регистр hex, ни одного дубликата. Ни один из них не цепляется за встроенные сигнатуры `leak-scan` (`_LEAK_PATTERNS` в `src/agentmarshal/journal/capture.py:253` не содержит entropy-правила), так что собственная транзакция журнала на них не споткнётся.
- Санитизация: grep по десяти файлам и по индексу не нашёл ни имён хостингов/доменов, ни путей, ни task-идентификаторов, ни блоков кода. Единственные backtick-токены — имена наших же команд и хэши. Профиль в таблице репортёров описывает setup, а не продукт/клиента.
- Индекс: новая секция «Batch of 2026-09-16» с колонкой **Where**, все десять ссылок резолвятся в существующие файлы; 016 в диспозиции прямо говорит, что поведение уже на default-ветке, и называет 0.4.0, строка индекса — «0.4.0 carries the fix».
- Проверяемые фактические утверждения совпадают с репозиторием: «21 amendment records across 18 of its 91 completed tasks» в 022 сходится (всего 22 амендмента в 19 задачах, минус незакрытая CR-095 → 21/18, completed-задач ровно 91); «doctor, whose four checks are git, repository, project file and schema» сходится с `doctor_checks` (`src/agentmarshal/doctor.py:112`); «declares no markers of its own» из 020 сходится с `.agentmarshal/project.json`; 017 верно описывает шаблон с `continue-on-error: true` в `templates/github/agentmarshal-governance.yml`.
- CONTRIBUTING описывает все три способа трекинга (хэш, диспозиция, куда ушло) и отсылает к README. Переименование заголовка «Current batch» → «Batch of 2026-08-30» ничего не ломает: ссылок на якорь `#current-batch` в репозитории нет.

Замечание (не блокирующее): в `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:3` шапка и строка индекса говорят просто «accepted», хотя тело диспозиции признаёт, что третья просьба репортёра («print the kept-at path for approved reviews») буквально не выполняется — «What it asked for literally is what 0.4.0 removes». Этот же диф вводит в README конвенцию помечать частичное принятие скобкой (как 018 и 020), так что репортёр, трекающий свою находку по шапке и по таблице, не увидит, что один из трёх пунктов ушёл в другой форме.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "4d2adb0389d6efd5c7ae666f912f03cc2fe20413", "verdict": "approved", "findings": [], "advisory_findings": ["prop-016-partial-acceptance-not-marked-in-header-and-index"]}
AGENTMARSHAL_VERDICT_END
