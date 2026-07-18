# AgentMarshal

Agent work attestation and merge governance: durable, vendor-neutral,
SHA-bound evidence rails for agent-driven development.

Agents produce more changes than a human can read. AgentMarshal aims to
make "this work was independently reviewed" a property of the repository
rather than of someone's memory: task contracts, review verdicts bound to
exact commits, and merge gates — with the evidence living in git, not in
an ephemeral session log.

## Status

**Pre-alpha.** This repository is a project skeleton: there is no usable
functionality yet, and everything — APIs, schemas, CLI — is subject to
change without notice.

The [agentmarshal/](agentmarshal/) submodule pins the archived v1
implementation (bash), kept read-only for reference during the rewrite.

## Development

Requires Python >= 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run pytest
uv run ruff check
uv run mypy
```

## License

[Apache-2.0](LICENSE)
