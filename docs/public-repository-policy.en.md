# Public Repository Policy

Document-ID: agentmarshal-public-repository-policy
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

The public AgentMarshal repository contains the framework code, public
contracts, generic prompts, schemas, tests and sanitized documentation needed
to adopt the framework in a new host project.

Internal operational journals, raw research notes, host-specific incidents and
private ADRs are not part of the public release unless they are explicitly
sanitized and still describe AgentMarshal itself.

<!-- Section-ID: public-scope -->
## Public Scope

Public content may include:

- framework CLI, scripts, schemas and tests;
- generic role prompts and execution profiles;
- adoption, startup, operations and adapter-boundary documentation;
- provider interfaces and mock implementations;
- public contribution and release process documentation.

<!-- Section-ID: private-scope -->
## Private Scope

Private content must remain outside the public repository:

- host runtime journals and raw model outputs;
- customer, production, domain, IP, credential or infrastructure details;
- host-specific ADRs that do not generalize to AgentMarshal;
- internal research monitoring data;
- secrets, tokens and machine-local configuration.

<!-- Section-ID: sanitization -->
## Sanitization

Before publishing or copying a document into the public repository, check it
for private host names, domains, IP addresses, credentials, raw transcripts,
absolute local paths and assumptions about a single Git provider.

If a document mixes public framework knowledge with private operational
history, extract the public rule into a new sanitized document and keep the raw
artifact private.

<!-- Section-ID: github-ci -->
## GitHub CI

GitHub CI is the public release gate. It must run without private credentials
and without a host repository. Provider-specific live integration tests belong
to host projects or private adapter test environments.

<!-- Section-ID: release-branches -->
## Release Branches

`master` is the stable public branch. Framework development may use `dev` or
`next` to avoid breaking host projects that pin public releases.

Public releases should be tagged. Hosts should pin a tag or exact commit and
update through a reviewed gitlink change.
