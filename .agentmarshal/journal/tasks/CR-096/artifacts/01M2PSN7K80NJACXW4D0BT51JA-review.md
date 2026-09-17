Разобрал контракт, дельта-спеку, реализацию и тесты; прогнать pytest в этой песочнице нельзя (запуск Python не разрешён), поэтому проверка статическая — по коду, а не по зелёному прогону.

Что проверил и что сходится:

- **Покрытие сценариев.** Все 9 сценариев из `openspec/changes/archive/2026-09-17-render-amendment-history/specs/` имеют тест, docstring которого их называет: 5 в `contract-history` (launcher, brief, без recorder, «без amendment ничего не изменилось» — на обоих концах, чтение из активного журнала) и 4 в `review-evidence` (launcher пишет digest, human path не пишет, отказ по схеме, старые записи читаются как раньше).
- **Байт-в-байт для журналов без amendment.** `append_amendment_history(text, "")` возвращает `text` без изменений, пиннутый 0.3.0-тест вызывает `_review_prompt("CONTRACT", "DIFF", commit)` без нового аргумента — ожидания не тронуты, изменён только docstring, что AC2 («expectations unmodified») разрешает.
- **Источник записей.** `launch_review` берёт `task.records` из `load_task_status(journal_root, …)` — рабочее дерево при embedded, журнал сайдкара при sidecar — тогда как `contract` читается из снапшота ревьюируемого коммита (`review.py:360-380`). Это ровно ADR-0011 D1, и AC3 выполнен.
- **Схема 5.** `_SUPPORTED_SCHEMAS` получает 5 для всех типов (что поправка к контракту от 2026-09-17 прямо благословляет), поле разрешено только на `review` при `schema >= 5`, отдельная проверка даёт сообщение с именем поля, `create_review_record` штампует 5 только при наличии поля и держит 3/4 как пол — дословно ADR-0011 D4 и политика ADR-0004. `submit-review` проводит поле только когда его дал вызывающий; CLI-аргумента не появилось, так что human path не может его выдумать.
- **Дайджест.** Хэш берётся от `contract`, не от `contract_material` — блок истории в него не входит, и `test_the_contract_digest_covers_the_contract_and_not_its_history` это пинит. Сценарий говорит «exact contract bytes the prompt carried», противоречия нет.
- **Форджинг.** Каждая строка reason префиксуется `> `, имя recorder схлопывается по whitespace и живёт на строке с таймстампом — ни reason, ни actor не могут подделать заголовок или новую запись.
- **Ничего не сдвинулось.** `gate.py` не тронут, `attestation.py` не перечисляет поля, других мест, где контракт выдаётся стороне, в `src/` нет (только `brief.py:333` и `review.py:67`). Все изменённые пути лежат в объявленном scope; `tasks.md` протикан целиком. Структура архива и новый baseline с написанным Purpose повторяют CR-091/092/093.
- Догфудинг виден на самом CR-096: `contract.md` блока истории не содержит, а в промпт этого ревью он пришёл из записи `01M2PRKZC497JGMRYE7ARFQNA1-amendment.json`.

Блокирующих находок нет. Три замечания ниже — advisory.

A-001: `render_amendment_history` в `src/agentmarshal/journal/brief.py:49-50` при `reason`, который не строка, делает `continue` — молча выбрасывает amendment из блока; это единственный путь, на котором поправка исчезает от того самого читателя, для которого блок и делался, и он расходится с fail-closed дисциплиной остального record-слоя (лучше поднять `JournalRecordError`, раз ветка всё равно недостижима).

A-002: `openspec/changes/archive/2026-09-17-render-amendment-history/design.md:27` утверждает «The refusal message names the field, as the schema 4 message does», но отказ schema 4 в `src/agentmarshal/journal/records.py:288-290` звучит как «finding records and finding bindings require schema 4» и никакого поля не называет — архивный design-документ теперь несёт ложное утверждение о коде, с которым себя сравнивает.

A-003: `src/agentmarshal/journal/review.py:16-19` тянет `append_amendment_history`/`render_amendment_history` из `brief.py`, из-за чего review-лаунчер зависит от модуля брифинга имплементора; общий рендерер логичнее держать в отдельном модуле — связность не циклическая и ничего не ломает, но владение кодом получилось неочевидное.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9d2cea0a68727f05d67c88e921c7d09852e59ee2", "verdict": "approved", "findings": [], "advisory_findings": ["A-001", "A-002", "A-003"]}
AGENTMARSHAL_VERDICT_END
