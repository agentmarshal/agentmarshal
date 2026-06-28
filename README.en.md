# AgentMarshal

Document-ID: agentmarshal-readme
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

AgentMarshal is a small engineering system for a governance/process layer on
top of Git. It helps AI-agent teams work through verifiable task contracts,
role/profile policy, review gates, provenance and an evidence journal.

AgentMarshal is not a model runtime, dispatcher, dashboard or agent memory. The
runtime can be human-operated, CLI-based or provided externally; the core keeps
rules, artifacts and trusted checks.

<!-- Section-ID: quick-start -->
## Quick Start

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init --recursive
./agentmarshal/bin/agentmarshal init --preset minimal --language en
./agentmarshal/bin/agentmarshal doctor --project-root .
./agentmarshal/bin/agentmarshal validate --project-root .
```

For a host with a historical `.agents` archive:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language en \
  --legacy-archive .agents
```

AgMake is used for task-local protocol execution:

```bash
./agentmarshal/bin/agmake init --task CR-123 --branch docs/CR-123-example
./agentmarshal/bin/agmake lint .agentmarshal/journal/tmp/runner/CR-123-runbook.sh
bash .agentmarshal/journal/tmp/runner/CR-123-runbook.sh
```

<!-- Section-ID: contracts -->
## Contracts

AgentMarshal public contracts:

- host integration: submodule, `.agentmarshal/project.json`, configurable
  journal and CI hooks;
- roles/profiles: ownership, allowed paths, tools, network/write policy;
- provider SPI: Git provider and CI/MR operations behind an adapter boundary;
- evidence plane: tasks, reviews, events, handoffs and normalized statistics;
- AgMake: deterministic task-local runbook that executes the protocol outside
  an expensive live model session.

Code identifiers, schemas, CLI flags and machine-readable data remain
language-neutral.

<!-- Section-ID: docs-map -->
## Documentation Map

- [Startup Guide](docs/startup-guide.en.md)
- [Adoption](ADOPT.en.md)
- [Operations](docs/operations.en.md)
- [Host integration](docs/host-integration.en.md)
- [Host adapter boundary](docs/host-adapter-boundary.en.md)
- [Public release readiness](docs/public-release-readiness.en.md)
- [Public repository policy](docs/public-repository-policy.en.md)
- [Methodology](methodology/README.en.md)
- [Architecture](docs/architecture.md)
- [Plugin architecture](docs/plugin-architecture.md)
- [AgMake](docs/agmake.md)
- [ADR](docs/adr/README.md)

<!-- Section-ID: status -->
## Status

Current milestone: private `v0.1`.

Public release requires sanitized documentation, generic English-first bundled
prompts, standalone CI and at least two exercised host integrations.
