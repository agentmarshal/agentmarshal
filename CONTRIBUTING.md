# Contributing to AgentMarshal

AgentMarshal развивается на основании реального опыта host-проектов. Не нужно
публиковать весь host journal: contribution должен содержать минимальный,
санитизированный и воспроизводимый контекст.

## Что отправлять upstream

Подходит для framework или official plugin:

- нарушение публичного AgentMarshal contract;
- generic CLI/schema/lifecycle/provider defect;
- capability, воспроизводимая на fixture-host или нескольких hosts;
- host-local extension, из которой удалена project-specific binding.

Остаётся в host:

- application paths и prompts;
- deployment/tenant policy одного проекта;
- внутренние сервисы и credentials;
- gate, не имеющий generic configuration contract.

## Host journal

Рекомендуемые поля задачи:

```text
Target-Repository: host|framework|cross-repository
Framework-Version: <tag>
Framework-Commit: <sha>
Upstream-Status: candidate|submitted|accepted|released|rejected
Framework-Issue: <reference>
Framework-PR: <reference>
Framework-Release: <version>
```

Host task остаётся источником локального evidence. Она получает `done` только
после upstream release, обновления pinned submodule и успешного host CI.

## Bug report

Указать:

- AgentMarshal version/commit;
- provider и runtime versions;
- минимальный redacted project/plugin config;
- reproduction;
- expected/actual behavior;
- redacted logs;
- workaround, если есть.

Не публиковать tokens, private URLs, prompts, raw runs, персональные данные,
полный host journal или стоимость внутренних запусков.

## Plugin contribution

Путь:

```text
host-local extension
→ fixture/second-host reproduction
→ generic manifest/config contract
→ standalone tests
→ compatibility and migration notes
→ issue/PR
```

Contribution обязан содержать `plugin.json`, schema-valid config, tests и
описание permissions/secrets. Community plugin не становится trusted
автоматически.

## Qualification report

Код не обязателен. Полезный отчёт:

```text
Host-Provider: GitLab
AgentMarshal-Version: v0.3.1
Outcome: partial
Failed-Capability: provider.pipeline
Evidence: <redacted>
Workaround: <description>
```

## Cross-repository lifecycle

```text
host finding → host task → upstream issue/PR → AgentMarshal release
→ host gitlink update → host CI/MR → host task done
```

Upstream `submitted`, `accepted` и `released` не равны host `done`.
