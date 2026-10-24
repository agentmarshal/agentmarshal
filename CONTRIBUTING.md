# Contributing to AgentMarshal

Thank you for taking the time. This project is small and deliberate: it governs
agent work with durable, SHA-bound evidence, and it holds itself to the same
rules it ships. Two things below are unusual enough to read before you start —
the **language rule** and the **governed contribution flow**.

One person maintains this project, so replies may take days. No response-time
promise is made.

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

A proposal landed from the batch of 2026-09-16 onwards carries the full sha256
of the file you sent, so you can find your own by hashing your copy and
searching for the result. The hash is one-way: it identifies the original to
whoever already holds it and discloses nothing to anyone else. Earlier batches
predate the convention and are matched by title. Alongside the disposition, an
accepted proposal names where it went — a release, a decision record, or the
work that carries it. That is how you follow a proposal after sending it;
`docs/proposals/README.md` states it in full.

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
Who records the independent review for a pull request from a fork is not yet
settled; if you need one, say so in the pull request's description.

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

If an agent does the implementation work, [AGENTS.md](AGENTS.md) states the
rules it follows — how to read the task's contract, what it may not touch,
this same check sequence and what to report.

### Versions

Between releases the default branch carries a version with a `.dev0` suffix, so
a build from it never reports a published release's version and sorts before
the version it names. The number it names is the release expected next, which
is a guess the branch is free to be wrong about: this branch carried
`0.5.0.dev0` while a patch release was being prepared instead. The task that
prepares a release sets the version it publishes, replacing whatever the branch
carried; the first task after the tag is pushed sets a `.dev0` version again.
The release workflow refuses to publish a development or local version, so a
branch version cannot reach PyPI by accident.

### Releases

Every release is accepted through a full audit of the project by a strong
model, enforced by the release workflow — a version cannot reach PyPI without
it. The order is fixed:

1. A release task sets the version the release publishes and finishes the
   release documentation (the changelog and upgrading notes for it).
2. Change freeze: until the tag is pushed, nothing lands on the default
   branch but the fixes below and the release's own notes.
3. The full project is audited by the allowlisted model — currently
   `gpt-6-astra`, named in `.github/scripts/check_release_audit.py`. The
   audit's full text may carry undisclosed security detail and stays
   private; what the gate reads is the dispositions file below.
4. Each blocking finding is either fixed — as an ordinary task with ordinary
   review — or dispositioned in the audit file as `deferred` or `rejected`
   with the reason. A finding is blocking when it is a broken published
   decision or threat-model promise, a security defect, or a false statement
   in the release documentation.
5. The audit file `release/audit-<version>.toml` is committed.
6. The tag `v<version>` is pushed.

There is no re-audit loop: the fixes are ordinary work and the next audit is
the next release's. Because work lands after the audit, the gate cannot ask
that nothing changed; it asks that what changed is the fixes of
dispositioned findings and the release notes.

The audit file is TOML:

```toml
version = "0.6.0"                    # the released version; the tag is v0.6.0
audited_commit = "059ba350bcf40d8d912d30850535816f2a87d076"  # the commit audited, as a full 40-character id
model = "gpt-6-astra"                # must be in the script's allowlist
audited_at = 2026-10-24T00:00:00Z    # when the audit ran

[[finding]]                          # one per blocking finding
id = "F-1"                           # its identifier in the audit
disposition = "fixed"                # fixed | deferred | rejected
task = "CR-231"                      # the fixing task; required when fixed

[[finding]]
id = "F-2"
disposition = "deferred"
reason = "accepted for the next release"  # required for deferred and rejected
```

A finding's description may be withheld — the file carries dispositions, not
audit text. Before building, the release workflow runs
`.github/scripts/check_release_audit.py <tag>` and the job fails — nothing is
built or published — when the file is missing or malformed, its `version`
differs from the tag, `audited_commit` is not an ancestor of the tagged
commit, `model` is not allowlisted, a `fixed` finding's task's last
lifecycle record in the journal is not `completed` — a task completed and
then reopened does not count — or a path changed between `audited_commit` and
the tag lies outside `.agentmarshal/journal/`, `release/`, `CHANGELOG.md`,
`UPGRADING.md`, `pyproject.toml`, `uv.lock`, `src/agentmarshal/__init__.py`
and the contract scopes of the tasks the file lists as `fixed`.

## Licence

By contributing you agree that your contribution is licensed under
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), the licence of this
project.
