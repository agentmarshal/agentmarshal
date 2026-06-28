# Plugins, presets и host extensions

## Назначение

AgentMarshal отделяет reusable framework behavior от специфики host repository.
Plugin API нужен для provider adapters, generic workflow capabilities и
project-specific gates.

Архитектурное решение: [ADR-0011](adr/ADR-0011-core-plugins-presets-and-host-extensions.md).

## Layout

Bundled plugins находятся в framework:

```text
agentmarshal/plugins/<plugin-id>/
  plugin.json
  scripts/
  schemas/
  tests/
```

Host-local plugins находятся в host binding:

```text
.agentmarshal/plugins/<plugin-id>/
  plugin.json
  scripts/
  schemas/
  tests/
```

External official/community plugin хранится отдельно и подключается pinned
version/commit. Его resolved location и checksum фиксируются в project config.

## Manifest

Минимальный пример:

```json
{
  "schema": 1,
  "id": "example-host-ci",
  "version": "0.1.0",
  "api_version": "1",
  "type": "host",
  "distribution": "host-local",
  "description": "Project-specific pre-merge gates.",
  "capabilities": ["ci.gate"],
  "entrypoints": {
    "doctor": "scripts/doctor.sh",
    "validate": "scripts/validate.sh"
  },
  "permissions": {
    "network": false,
    "git_write": false,
    "secrets": []
  },
  "requires": {
    "agentmarshal": ">=0.1.0 <0.2.0",
    "commands": ["bash"]
  }
}
```

Schema: [`../schemas/plugin-manifest.schema.json`](../schemas/plugin-manifest.schema.json).

Paths entrypoints являются относительными plugin root, не содержат `..` и
проверяются на существование/исполняемость. Manifest является data file и не
исполняется как shell.

## Capabilities

Vocabulary v1:

```text
provider.refs
provider.merge_request
provider.compare
provider.pipeline
ci.gate
policy.scope
policy.merge
review.triage
worktree.manage
stats.record
contribution.export
```

Неизвестная capability блокирует plugin activation. Новая capability требует
изменения plugin API/versioned compatibility contract.

## Presets

Preset перечисляет plugin IDs и defaults. Он не содержит shell entrypoints.
`init --preset <id>`:

1. разрешает preset в exact список plugins;
2. показывает plan;
3. получает consent;
4. записывает resolved список в project config;
5. запускает `doctor`.

Обновление preset в новой версии AgentMarshal не меняет уже resolved host config
автоматически.

## Trust

- bundled plugin доверяется как часть pinned AgentMarshal commit, но включается
  явно;
- official/community plugin pinится version/commit/checksum;
- host-local plugin проходит обычный host review;
- secrets передаются только по declared names и optional
  `provider.secret_bindings` из host `project.json`;
- network/git-write permissions запрещены по умолчанию;
- plugin не изменяет CI/config без integration plan и operator consent.

Default provider выбирается host config:

```json
{
  "provider": {
    "default": "mock",
    "secret_bindings": {}
  }
}
```

`agentmarshal/providers/dispatch.sh` может принимать `--provider` явно или
читать `provider.default` из project config. Fresh bootstrap использует mock
provider; production host выбирает GitFlic/GitHub/GitLab adapter и передаёт
credentials только через объявленные environment variables.

## Разработка и upstream

Host-specific behavior сначала реализуется в `.agentmarshal/plugins/`.
Кандидат в framework/official plugin должен:

- иметь generic config без host names/secrets;
- воспроизводиться в fixture-host;
- пройти standalone tests;
- описать compatibility/migration;
- иметь sanitized issue или qualification report.

Порядок contribution описан в [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
