# AgentMarshal

Agent work attestation and merge governance: durable, vendor-neutral,
SHA-bound evidence rails for agent-driven development.

Agents produce more changes than a human can read. AgentMarshal aims to
make "this work was independently reviewed" a property of the repository
rather than of someone's memory: task contracts, review verdicts bound to
exact commits, and merge gates — with the evidence living in git, not in
an ephemeral session log.

**Trust boundary (0.1.0):** the merge gate enforces that a review's recorded
reviewer email differs from the commit authors', and binds the verdict to the
exact commit SHA. It does **not** cryptographically authenticate who recorded
a review or which checkout was gated — the recorder and the reviewed tree are
operator-trusted. Signing/provenance is roadmap, not a 0.1.0 guarantee.

## Status

**Pre-alpha.** The first Python CLI slice: `agentmarshal init` writes project
metadata into a git repository; the journal, gate, and review/completion
commands follow. APIs, schemas, and CLI are subject to change without notice.

## Install

```sh
pip install agentmarshal
```

Requirements: **Python >= 3.12** and **git** on `PATH` — the gate, review,
and completion commands shell out to git. No Python dependencies.

AgentMarshal is **model-agnostic** and bundles no reviewer. To review a task,
either set `AGENTMARSHAL_REVIEWER_CMD` to any reviewer command (for example a
Codex or Claude CLI — it receives the prompt on stdin and prints the machine
verdict, with `{model}` and `{prompt_file}` substituted), or record a verdict
directly with `agentmarshal submit-review`. The latter runs no model; its
`--vendor`/`--model` arguments are recorded provenance labels, not an invoked
model (use e.g. `--vendor human --model none` for a human review).

(`git archive`-based review snapshotting currently assumes a POSIX host;
Windows is untested.)

## Development

Requires Python >= 3.12 and [uv](https://docs.astral.sh/uv/) (development
tooling only — not needed to install or run AgentMarshal).

```sh
uv sync
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

Initialize a git repository for AgentMarshal:

```sh
uv run agentmarshal init
```

## License

[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0). The full text
ships in the `LICENSE` file of the source distribution.
