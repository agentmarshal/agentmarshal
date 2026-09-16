Проверил все десять дайджестов, индекс и правку CONTRIBUTING против контракта CR-094, а числовые утверждения — против самого репозитория.

Что сошлось:

- Все десять файлов (014–023) несут версию `0.3.0`, блок «Measurements, as reported», раздел `## Proposed` и `## Disposition` с обоснованием.
- Все десять source-хешей — полные 64 знака нижним регистром, без дублей между собой.
- В новых дайджестах нет путей, имён репозиториев, доменов, идентификаторов задач и цитат кода: единственные backtick-фрагменты — имена команд самого проекта (`init`, `doctor`, `leak-scan`, `record-session`, `validate`, `agentmarshal review`).
- Колонка «Where» есть у всех десяти строк; 016 в диспозиции прямо говорит, что фикс уже на default-ветке, и называет 0.4.0.
- Проверяемые утверждения точны: в журнале ровно 21 amendment-запись в 18 задачах из 91 завершённой (022); CR-069 действительно имеет последовательность opened → amendment → review → review → amendment → review → review → completed, причём второй review — `changes_required` с претензией к формулировке критерия, ровно как описано. Код тоже подтверждает: `doctor_checks` возвращает четыре проверки (014), `_run_reviewer` возвращает только stdout при нулевом коде возврата (021), ошибка плейсхолдера не называет токен (015), пиннинг reviewer prose на ветке есть (016).

Advisory-замечания (ничего из этого не блокирует):

ADV-001 — `CONTRIBUTING.md:58`: строка длиной ~110 символов ломает перенос по ~78 колонкам, принятый во всём файле; абзац читается рвано в diff и в терминале.

ADV-002 — `CONTRIBUTING.md:57` и раздел «Tracking what happened to yours» в `docs/proposals/README.md:41-49` утверждают безусловно, что каждый дайджест несёт sha256 присланного файла, но у 001–013 source-строки нет вовсе; репортёр из партии A, выполнив описанную процедуру (захешировать свой файл и поискать результат), не найдёт ничего, и текст об этом не предупреждает.

ADV-003 — `docs/proposals/018-session-activity-vocabulary-and-cost.md:3` и `docs/proposals/020-leak-scan-names-no-file-and-self-matches.md:3`: в шапке стоит плоское «Disposition: accepted», хотя заголовок раздела и строка индекса фиксируют частичное решение (отложены cost-поле и acknowledged-and-proceed). Прецедент есть — 005 несёт уточнение прямо в шапке.

ADV-004 — `docs/proposals/020-leak-scan-names-no-file-and-self-matches.md:34`: «merge request» на фоне двенадцати «pull request» в остальных девяти дайджестах — не только терминологический разнобой, но и слабый намёк на семейство провайдера репортёра, что расходится с собственной дисциплиной партии «Git hosting provider» без названия.

ADV-005 — `CONTRIBUTING.md:58-59`: в одном абзаце слово «digest» означает сначала опубликованный документ («Each digest carries the full sha256»), а через строку — сам хеш («the digest identifies the original to whoever holds it»); для читателя, который только знакомится с каналом, это двусмысленно.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d3c0e2a7c8843d083771164101248fc0f8f5d7ba", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-001", "ADV-002", "ADV-003", "ADV-004", "ADV-005"]}
AGENTMARSHAL_VERDICT_END
