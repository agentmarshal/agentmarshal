# Политика публичного репозитория

Document-ID: agentmarshal-public-repository-policy
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

Публичный репозиторий AgentMarshal содержит framework code, public contracts,
generic prompts, schemas, tests и sanitized documentation, необходимые для
подключения framework к новому host project.

Internal operational journals, raw research notes, host-specific incidents и
private ADRs не входят в public release, если они явно не очищены и не
описывают сам AgentMarshal.

<!-- Section-ID: public-scope -->
## Public Scope

В public content могут входить:

- framework CLI, scripts, schemas и tests;
- generic role prompts и execution profiles;
- adoption, startup, operations и adapter-boundary documentation;
- provider interfaces и mock implementations;
- public contribution и release process documentation.

<!-- Section-ID: private-scope -->
## Private Scope

Private content должен оставаться вне public repository:

- host runtime journals и raw model outputs;
- customer, production, domain, IP, credential или infrastructure details;
- host-specific ADRs, которые не обобщаются до AgentMarshal;
- internal research monitoring data;
- secrets, tokens и machine-local configuration.

<!-- Section-ID: sanitization -->
## Sanitization

Перед публикацией или переносом документа в public repository проверьте его на
private host names, domains, IP addresses, credentials, raw transcripts,
absolute local paths и assumptions о единственном Git provider.

Если документ смешивает public framework knowledge с private operational
history, вынесите public rule в новый sanitized document, а raw artifact
оставьте private.

<!-- Section-ID: github-ci -->
## GitHub CI

GitHub CI является public release gate. Он должен запускаться без private
credentials и без host repository. Provider-specific live integration tests
принадлежат host projects или private adapter test environments.

<!-- Section-ID: release-branches -->
## Release Branches

`master` является stable public branch. Framework development может
использовать `dev` или `next`, чтобы не ломать host projects, которые pin public
releases.

Public releases должны тегироваться. Hosts должны pin tag или exact commit и
обновляться через reviewed gitlink change.
