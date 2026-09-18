Я проверил все шесть критериев приёмки и ставлю **approved**. Блокирующих замечаний нет, есть одно advisory.

Что проверил в snapshot:
- **Scope.** Все изменённые пути входят в scope контракта. Behaviour не меняется.
- **SECURITY.md.** Канал для отчёта один: GitHub private vulnerability reporting. Все четыре класса уязвимостей на месте:
  - обход gate;
  - изменение записи или запись, которую lifecycle не допускает. Это покрывает «forging or altering… undetected», и формулировка сознательно согласована с trust boundary из `README.md:12-25`;
  - вывод leak-scan, раскрывающий то, что он должен скрывать;
  - журнал, оставленный в невалидном состоянии.

  Response time не обещан. Утверждение «as the README states» подтверждается текстом README.
- **Issue forms.** В `finding.yml` все пять полей из формата CONTRIBUTING обязательны, language policy есть и в description, и в markdown-шапке. `gate-refusal.yml` покрывает непонятный отказ gate. `config.yml` отключает blank issues и ссылается на SECURITY.md.
- **PR template.** Каждый пункт (`CR-NNN`, scope, append-only, `AGENTMARSHAL_ACTOR`, English, шесть команд проверки, Apache-2.0, review и attestation) совпадает с разделами CONTRIBUTING. Пункт «does not alter the contract» не противоречит ADR-0011: там сказано, что `amend` не редактирует `contract.md`.
- **docs/README.md.** Карта покрывает все 43 документа под `docs/` (11 ADR, 23 proposals плюс их README, incident, migration, 7 guides, JSON-шаблон), README на неё ссылается. Dispositions у proposals 003, 004, 009 и 013 описаны верно.
- **CONTRIBUTING.md.** Прямо сказано, что maintainer один и response time не обещается. Фраза о том, что вопрос с fork-review не решён, признаёт этот пробел и ничего не решает, так что в non-goals она не лезет.
- **Ссылки.** Ссылок на Discussions или несуществующие support-каналы нет. Владелец и имя репозитория в URL совпадают с `pyproject.toml`, `master` — с текущей default branch.

Advisory: ссылки на SECURITY.md в `.github/ISSUE_TEMPLATE/config.yml:4` и на CONTRIBUTING.md в `.github/pull_request_template.md:29` жёстко прописывают `blob/master`. При этом `.github/workflows/agentmarshal-governance.yml:10` прямо допускает переименование ветки в `main`, и тогда обе ссылки сломаются. Надёжнее не привязываться к ветке: `…/security/policy` и `…/blob/HEAD/CONTRIBUTING.md`.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c56b9aa3d2f3cc524431845b5b6cdf18da86e380", "verdict": "approved", "findings": [], "advisory_findings": ["CR108-ADV-1-hardcoded-master-branch-urls"]}
AGENTMARSHAL_VERDICT_END
