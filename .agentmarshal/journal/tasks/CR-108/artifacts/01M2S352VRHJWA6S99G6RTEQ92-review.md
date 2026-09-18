Замечаний, которые блокируют мерж, нет. Каждый критерий приёмки я сверил с файлами снапшота:

- **SECURITY.md**:
  - Канал для сообщений ровно один — GitHub private vulnerability reporting.
  - Все четыре обязательных класса уязвимостей перечислены.
  - Срок ответа не обещается.
  - Оговорка про trust boundary (запись от чужого identity не считается уязвимостью) совпадает с README.md:12-25. Там тоже написано, что gate сравнивает строки email и ничего не аутентифицирует. Поэтому узкая трактовка «forging… undetected» — это честное следствие того, что проект вообще заявляет, а не лазейка.
- **Issue forms**:
  - `finding.yml` содержит пять обязательных полей ровно по формату из CONTRIBUTING.md:37-43, а в `description` указана языковая политика.
  - Для непонятного отказа gate есть отдельная форма `gate-refusal.yml`.
  - `config.yml` отключает blank issues и ссылается на SECURITY.md. Ветка `master` в ссылке совпадает с `.github/workflows/agentmarshal-governance.yml:10`.
- **PR template**:
  - Все пять обязательных пунктов на месте: CR-NNN, scope, локальные проверки (список совпадает с CONTRIBUTING.md:110-115 байт в байт), `AGENTMARSHAL_ACTOR`, английский.
  - Якорь `#this-repository-governs-itself` существует.
- **docs/README.md**: в карту попали все 45 файлов под `docs/`. Ни один файл не пропущен и ни одна ссылка не мёртвая. Пометки deferred/declined совпадают с полем `Disposition` в каждом proposal.
- **README.md** ссылается на карту. **CONTRIBUTING.md** честно говорит, что проект ведёт один человек, и срок ответа не обещает.
- Ссылок на Discussions или несуществующие каналы поддержки нет. Все пути в scope.

Одно некритичное замечание:

В `.github/pull_request_template.md:4` есть пункт «This change does not alter the contract…». Он ставит автору условие, которого в CONTRIBUTING.md нет. Там в строках 84-85 сказано только, что контракт и прежнее состояние задачи gate читает с base side, а evidence records — append-only. Запрета трогать контракт нет. К тому же контракт по ADR-0011 меняют отдельной записью-amendment, так что формулировку стоит свести к тексту CONTRIBUTING.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c56b9aa3d2f3cc524431845b5b6cdf18da86e380", "verdict": "approved", "findings": [], "advisory_findings": ["pr-template-contract-item-exceeds-contributing"]}
AGENTMARSHAL_VERDICT_END

Кстати: коннекторы claude.ai Gmail, Google Calendar и Google Drive не авторизованы. Если они понадобятся, их нужно подключить в настройках коннекторов на claude.ai.
