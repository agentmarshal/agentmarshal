# Host Adapter Boundary

Document-ID: agentmarshal-host-adapter-boundary
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

AgentMarshal core must stay independent from the host repository, Git provider
and CI vendor. Host-specific behavior belongs to `.agentmarshal/` configuration,
host-local plugins and adapter scripts.

<!-- Section-ID: principles -->
## Principles

- Core owns contracts, schemas, validators and default runbook rails.
- Host owns provider credentials, CI wiring, project gates and local policy.
- Provider adapters hide GitFlic, GitHub, GitLab or local mock details.
- Host gates extend the process without modifying AgentMarshal core.

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

Provider adapters expose refs, compare, immutable blob reads, pipeline status,
job diagnostics and merge request operations. A host may start with `mock` and
bind a real provider later.

Secrets are explicit environment bindings. AgentMarshal must not read user SSH
or provider credential files directly.

<!-- Section-ID: ci -->
## CI

Host CI should initialize the pinned submodule, run host bootstrap checks,
execute relevant AgentMarshal validators and preserve exact SHA evidence. CI
must not update the submodule to remote HEAD during a host pipeline.

<!-- Section-ID: custom-gates -->
## Custom Gates

Host-specific gates live in host-local plugins or integration scripts. They may
block a task, add evidence or require human approval, but they must not rewrite
AgentMarshal core contracts.
