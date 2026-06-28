# Public Release Readiness

Document-ID: agentmarshal-public-release-readiness
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

Public release means that the repository can be read, cloned and adopted by a
new host without private project context. Private operational history may stay
in internal repositories.

<!-- Section-ID: private-to-public -->
## Private To Public

Before publishing, confirm that AgentMarshal works in at least two host
repositories. One host should be a software-development project; another may be
a research or operations project to prove that the framework is not tied to one
workflow.

<!-- Section-ID: sanitization -->
## Sanitization

Remove or quarantine:

- private host names, domains, IPs and credentials;
- raw model transcripts;
- customer or production information;
- host-specific ADRs that do not describe AgentMarshal itself;
- accidental assumptions about a single Git provider.

<!-- Section-ID: prompts -->
## Prompts

Bundled prompts must be generic and English-first. Host-specific prompts belong
to host-local plugins or host configuration.

<!-- Section-ID: github -->
## GitHub

GitHub may be the public release home even if private development starts on
another provider. The public repository should have its own CI, release tags and
contribution guide.

<!-- Section-ID: release-branch -->
## Release Branch

Use a protected public branch for stable releases and a development branch for
framework changes that may temporarily break host integrations.
