# Contributing to AgentMarshal

Thank you for taking the time. This project is small and deliberate: it governs
agent work with durable, SHA-bound evidence, and it holds itself to the same
rules it ships. Two things below are unusual enough to read before you start —
the **language rule** and the **governed contribution flow**.

## Language

The rule differs by artifact, because the two have different jobs.

**Public artifacts are English.** Documentation, ADRs, files under
`docs/proposals/`, commit messages, pull-request titles and descriptions, and
code comments. These are the project's record; a mixed-language record breaks
search and deduplication — someone will not find that their finding was already
reported.

**Reports you send us may be in any language.** English is easier for us and
gets a faster answer, but do not let language stop you from reporting: send it
as it comes, and we will write the English version. If we cannot process a
report, we will say so and ask for English — we would rather have your finding
in your own words than not have it at all.

The practical consequence: what you *send* and what we *publish* need not be
the same document. Your original stays with you; upstream publishes an English
digest that keeps your measurements verbatim and credits the reporter.

## Reporting a finding

The value of a report is in what was measured, not in the prose around it. A
few precise numbers beat a page of description, and they lower the English bar
to almost nothing.

```
Symptom:      what you observed, with the exact command and its output
Measurements: counts, timings, how often it happens (e.g. "3 of 7 runs")
Version:      output of `agentmarshal --version`
Environment:  OS, Python version, git provider (GitHub / GitFlic / self-hosted)
Expected:     what you expected instead, and why
```

Findings from real operation are the most valuable input this project gets:
they carry failure frequency, the true cost of workarounds, and which error
messages leave an operator with nothing to act on. Reading the code cannot
produce that.

## Proposals from adopters

If you run AgentMarshal on your own repository, collect operational findings
there — the convention is a directory in your own repo, for example
`.agentmarshal/upstream/` — and send them when a batch is ready. Upstream lands
them under `docs/proposals/` as English digests, each carrying its source
attribution, the tool version it was observed on, and a disposition (accepted,
declined, deferred) with the reasoning. A declined proposal keeps its file and
its reason: the record is the point.

Proposals sent from a private repository are welcome. Strip anything
confidential before sending — we cannot un-publish what lands in a public
repository, and we will ask about anything that looks like it identifies a
third party.

## This repository governs itself

AgentMarshal is used to govern its own development, so a change here passes the
same gate the tool ships. This surprises people, so it is worth stating plainly:

- Work happens as a task `CR-NNN` whose **contract declares a scope**. The gate
  refuses a diff that touches anything outside it.
- A change needs an **independent review**: the recorded reviewer's email must
  differ from the commit authors'. This is enforced, not assumed.
- The candidate must carry a **pipeline attestation** for its exact commit.
- Evidence records are **append-only**; the contract and prior task state are
  read from the base side, so a change cannot widen its own scope.

**If you contribute with an agent, have it declare itself.** Set
`AGENTMARSHAL_ACTOR` in the agent's session environment, so the records it
writes say an agent wrote them. An agent normally commits under your git
identity, so nothing else can separate the two of you — and a review record
marked `vendor: human` that an agent produced is exactly the confusion this
project has already had to correct in its own journal.

For a pull request from a fork this matters more, not less: a fork PR is an
untrusted boundary — see [docs/github-enforcement.md](docs/github-enforcement.md).

If your change is refused by the gate, the output names the failing check. Open
an issue if the reason is not clear; a confusing refusal is itself a finding we
want.

## Development

Requires Python >= 3.12 and [uv](https://docs.astral.sh/uv/) (development
tooling only — not needed to install or run AgentMarshal). Run the same
sequence CI runs, project-wide, before you push:

```sh
uv sync --locked
uv run agentmarshal validate
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

`agentmarshal validate` checks the whole journal for integrity and is the
governance check in CI.

## Licence

By contributing you agree that your contribution is licensed under
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), the licence of this
project.
