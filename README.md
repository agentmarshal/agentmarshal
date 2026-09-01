# AgentMarshal

Agent work attestation and merge governance: durable, vendor-neutral,
SHA-bound evidence rails for agent-driven development.

Agents produce more changes than a human can read. AgentMarshal aims to
make "this work was independently reviewed" a property of the repository
rather than of someone's memory: task contracts, review verdicts bound to
exact commits, and merge gates — with the evidence living in git, not in
an ephemeral session log.

**Trust boundary (0.2.0):** the merge gate enforces that a review's recorded
reviewer email differs from the commit authors', and binds the verdict to the
exact commit SHA. It does **not** cryptographically authenticate who recorded
a review or which checkout was gated — the recorder and the reviewed tree are
operator-trusted. Signing/provenance is roadmap, not a 0.2.0 guarantee.

One consequence is worth stating outright, because the gate's output can read
like more than it is: **a `human` reviewer is a self-declaration.** The gate
compares an email string against the commit authors'; it establishes nothing
about a person having read anything. A record an agent produced with
`--vendor human` is indistinguishable from one a person created, and it passes
the same check — we have seen exactly that happen in operation. Until review
records are signed, `vendor` and `model` are labels the recorder chose, and the
independence check is a string comparison, not evidence of human involvement.

## Built in the open

AgentMarshal governs its own development. Everything under
`.agentmarshal/journal/` is real: the task contracts we worked to, the review
verdicts bound to exact commit SHAs, the lifecycle records, and the
token-economics measurements of what each task actually cost. The tool's
guarantees are demonstrated on the tool's own history — not just described.

We opened this repository with its **full history** on purpose — the mistakes,
the abandoned tasks (CR-036, CR-037), the multi-round reviews, the token spend.
We do **not** rewrite history: the SHA-bound audit trail *is* the product, and
rewriting it would destroy the very property AgentMarshal exists to provide.

That honesty cuts both ways — the shipped design docs are explicit about the
historical 0.1.0 boundary and note what has changed since:

- [ADR-0004](docs/adr/ADR-0004-journal-data-model.md) and
  [ADR-0005](docs/adr/ADR-0005-evidence-capture-and-format.md) mark planned
  supplementary-artifact capture policy, the private store, and the
  in-toto/attestation projection as roadmap. They remain inactive in 0.2.0;
  ADR-0005 separately records the advisory leak-scan that has shipped.
- [docs/migration-v1-to-v2.md](docs/migration-v1-to-v2.md) records what the
  v1→v2 migration lost (contract prose) and that the machine-readable
  acceptance array was empty in every contract through CR-038 — without
  backfilling any historical record.

To see how the project actually evolved, token costs and all, read the journal.

## Status

**Pre-alpha.** Version 0.2.0 ships the governed loop end to end: task contracts,
review and operator-acceptance evidence, lifecycle repair, the fail-closed gate,
completion, reporting, validation, advisory leak scanning, and local pruning.
APIs, schemas, and CLI are subject to change without notice.

## Install

Install the published 0.2.0 release:

```sh
pip install agentmarshal==0.2.0
agentmarshal --version
```

Plain `pip install agentmarshal` installs the latest published release, which
may not be the version described here — pin it if you share a journal, and see
[UPGRADING.md](UPGRADING.md) for why.

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

## Quickstart

New to the idea? [docs/overview.md](docs/overview.md) explains the purpose,
the design, and the vocabulary (host repo, task, gate, …) in a page. The whole
loop, inside a git repository — see [docs/quickstart.md](docs/quickstart.md)
for the annotated walkthrough with a full configuration reference:

```sh
agentmarshal init                                     # write .agentmarshal/
agentmarshal open --title "Add greeting" --scope src/ # -> task CR-001 + contract
git add .agentmarshal && git commit -m "open CR-001"
BASE=$(git rev-parse HEAD)

git switch -c feat/CR-001                              # do the work in scope
# ...edit files under src/...
git add src && git commit -m "implement CR-001"
IMPL=$(git rev-parse HEAD)

# record an INDEPENDENT review (reviewer email != commit author)
agentmarshal submit-review --task CR-001 --commit "$IMPL" \
  --verdict approved --role reviewer --vendor human --model none \
  --email reviewer@example.com

# the gate is the merge authority; it passes only when every check holds
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal gate --task CR-001 --commit "$IMPL" --base "$BASE"

AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal complete --task CR-001 --commit "$IMPL" --base "$BASE"

agentmarshal status CR-001   # -> done, with the SHA-bound review evidence
agentmarshal validate        # -> whole-journal integrity check (run this in CI)
```

The gate only decides; performing the merge is your provider's job. Wiring it
to block merges is covered in
[docs/self-hosting-workflow.md](docs/self-hosting-workflow.md) and
[docs/github-enforcement.md](docs/github-enforcement.md).

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
