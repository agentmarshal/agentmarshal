# Host Integration

Document-ID: agentmarshal-host-integration
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

Host repository использует AgentMarshal как pinned submodule. Framework
предоставляет contracts, validators и scripts; host предоставляет project
config, journal, provider secrets, CI wiring и human gates.

<!-- Section-ID: layout -->
## Layout

Целевой layout:

```text
host/
  agentmarshal/
  .agentmarshal/
    project.json
    config/runtime.conf
    plugins/
    journal/
```

Legacy `.agents/` поддерживается через adoption mode и остаётся host-owned.

Если `.agents/` является historical archive, а не активным runtime journal,
host должен использовать fresh bootstrap рядом с archive:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language ru \
  --legacy-archive .agents
```

В этом режиме активный journal создаётся в `.agentmarshal/journal`, а `.agents/`
только фиксируется как legacy archive. Новые host/product tasks не должны
записываться в `.agents/`.

<!-- Section-ID: config -->
## Config

`.agentmarshal/project.json` задаёт:

- runtime config path;
- journal root;
- agents/prompts paths;
- provider default и secret bindings;
- bundled/host-local plugin roots.

Runtime config задаёт `review_language`, active roles, worktree root/pattern и
stats policy.

<!-- Section-ID: bootstrap -->
## Bootstrap

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language ru
./agentmarshal/bin/agentmarshal doctor
```

`init --adopt-existing` принимает существующий `.agents/` layout. Fresh
bootstrap uses mock provider. Для проектов с историческим `.agents/`, который
нужно оставить архивом, используйте `--legacy-archive .agents`, а не
`--adopt-existing`.

<!-- Section-ID: ci -->
## CI

Host CI обязан:

1. checkout pinned submodule;
2. не обновлять submodule до remote HEAD;
3. запускать `validate.sh`;
4. запускать relevant AgentMarshal tests;
5. сохранять exact pipeline SHA.

<!-- Section-ID: providers -->
## Providers

Provider-specific операции находятся за SPI boundary: refs, compare, pipeline,
jobs, merge requests и immutable blobs. GitFlic — первый рабочий provider;
mock provider обязателен для standalone tests.

<!-- Section-ID: versioning -->
## Versioning

Обновление AgentMarshal выполняется отдельной branch/task:

```text
read changelog → update submodule → host CI → review exact gitlink → merge
```

Host task получает `done` только после successful host CI на новом pinned
commit.
