# Adopt AgentMarshal

Document-ID: agentmarshal-adopt
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

AgentMarshal is added to a host repository as a submodule. Framework code lives
in `agentmarshal/`; configuration, journal and runtime state belong to the
host.

The adoption goal is to get verifiable role/profile contracts, provider
binding, evidence journal, validation and AgMake runbooks without baking
project-specific policy into the framework.

<!-- Section-ID: install -->
## Install

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init --recursive
```

The host must pin an exact AgentMarshal commit or release tag. Automatic
submodule tracking of a branch is forbidden.

<!-- Section-ID: init -->
## Init

Fresh project:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language en
```

Existing project with `.agents/`:

```bash
./agentmarshal/bin/agentmarshal init --adopt-existing --language en
```

`init` creates `.agentmarshal/project.json`, runtime config, journal layout and
plugin roots. Fresh bootstrap uses the mock provider so `doctor` does not
require an external Git provider.

<!-- Section-ID: configure -->
## Configure

The operator edits:

- `.agentmarshal/project.json` — bootstrap anchor, paths, provider binding,
  plugin roots;
- `.agentmarshal/config/runtime.conf` or legacy `.agents/config/...` —
  `review_language`, active roles, worktree root, stats policy;
- host role specs, prompts and host-local plugins.

Secrets are passed through environment variables. AgentMarshal does not read
user credential files and does not print secret values.

<!-- Section-ID: validate -->
## Validate

```bash
./agentmarshal/bin/agentmarshal doctor
./agentmarshal/scripts/validate.sh
./agentmarshal/tests/bootstrap.sh
./agentmarshal/tests/provider-spi.sh
./agentmarshal/tests/resource-routing.sh
./agentmarshal/tests/negative.sh
```

Host CI should run `validate.sh` and relevant AgentMarshal tests when framework,
binding or journal files change.

<!-- Section-ID: next -->
## Next

After adoption:

1. Freeze role ownership and execution profiles.
2. Configure provider secrets and CI gates.
3. Run the first task through an AgMake runbook.
4. Update the AgentMarshal submodule in a dedicated branch with review of the
   exact gitlink.

For a fresh host, AgMake writes runtime artifacts below the configured journal
root, usually `.agentmarshal/journal/tmp/runner/`. For an adopted legacy host,
the path remains below `.agents/tmp/runner/`.

More details: [host integration](docs/host-integration.en.md) and
[operations](docs/operations.en.md).
