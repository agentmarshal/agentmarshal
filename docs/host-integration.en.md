# Host Integration

Document-ID: agentmarshal-host-integration
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

A host repository uses AgentMarshal as a pinned submodule. The framework
provides contracts, validators and scripts; the host provides project config,
journal, provider secrets, CI wiring and human gates.

<!-- Section-ID: layout -->
## Layout

Target layout:

```text
host/
  agentmarshal/
  .agentmarshal/
    project.json
    config/runtime.conf
    plugins/
    journal/
```

Legacy `.agents/` is supported through adoption mode and remains host-owned.

If `.agents/` is a historical archive rather than the active runtime journal,
the host should use a fresh bootstrap next to that archive:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language en \
  --legacy-archive .agents
```

In this mode the active journal is created under `.agentmarshal/journal`, while
`.agents/` is recorded only as a legacy archive. New host/product tasks must not
be written to `.agents/`.

<!-- Section-ID: config -->
## Config

`.agentmarshal/project.json` defines:

- runtime config path;
- journal root;
- agents/prompts paths;
- default provider and secret bindings;
- bundled/host-local plugin roots.

Runtime config defines `review_language`, active roles, worktree root/pattern
and stats policy.

<!-- Section-ID: bootstrap -->
## Bootstrap

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language en
./agentmarshal/bin/agentmarshal doctor
```

`init --adopt-existing` adopts an existing `.agents/` layout. Fresh bootstrap
uses the mock provider. For projects where historical `.agents/` must remain an
archive, use `--legacy-archive .agents` instead of `--adopt-existing`.

<!-- Section-ID: ci -->
## CI

Host CI must:

1. checkout the pinned submodule;
2. avoid updating the submodule to remote HEAD;
3. run `validate.sh`;
4. run relevant AgentMarshal tests;
5. preserve the exact pipeline SHA.

<!-- Section-ID: providers -->
## Providers

Provider-specific operations stay behind the SPI boundary: refs, compare,
pipeline, jobs, merge requests and immutable blobs. GitFlic is the first
working provider; the mock provider is required for standalone tests.

<!-- Section-ID: versioning -->
## Versioning

AgentMarshal updates use a dedicated branch/task:

```text
read changelog → update submodule → host CI → review exact gitlink → merge
```

The host task becomes `done` only after successful host CI on the new pinned
commit.
