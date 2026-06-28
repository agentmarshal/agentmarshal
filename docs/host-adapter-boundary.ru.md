# Host Adapter Boundary

Document-ID: agentmarshal-host-adapter-boundary
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

AgentMarshal core должен оставаться независимым от host repository, Git
provider и CI vendor. Host-specific поведение живёт в `.agentmarshal/`
configuration, host-local plugins и adapter scripts.

<!-- Section-ID: principles -->
## Принципы

- Core владеет contracts, schemas, validators и default runbook rails.
- Host владеет provider credentials, CI wiring, project gates и local policy.
- Provider adapters скрывают детали GitFlic, GitHub, GitLab или local mock.
- Host gates расширяют процесс без изменения AgentMarshal core.

<!-- Section-ID: layout -->
## Layout

```text
host/
  agentmarshal/               # pinned framework submodule
  .agentmarshal/
    project.json              # bootstrap anchor
    config/runtime.conf       # operator-editable runtime config
    integrations/
      git/
      ci/
      provider/
    plugins/
    journal/
```

<!-- Section-ID: provider -->
## Provider

Provider adapters предоставляют refs, compare, immutable blob reads, pipeline
status, job diagnostics и merge request operations. Host может начать с `mock`
и подключить реальный provider позже.

Secrets задаются явными environment bindings. AgentMarshal не должен напрямую
читать пользовательские SSH или provider credential files.

<!-- Section-ID: ci -->
## CI

Host CI должен инициализировать pinned submodule, запускать host bootstrap
checks, выполнять relevant AgentMarshal validators и сохранять exact SHA
evidence. CI не должен обновлять submodule до remote HEAD во время host
pipeline.

<!-- Section-ID: custom-gates -->
## Custom Gates

Host-specific gates живут в host-local plugins или integration scripts. Они
могут блокировать task, добавлять evidence или требовать human approval, но не
должны переписывать AgentMarshal core contracts.
