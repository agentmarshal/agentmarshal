+++
schema = 1
id = "CR-056"
title = "init scaffolds the upstream outbox and says what it is for"
scope = ["src/agentmarshal/project.py", "src/agentmarshal/cli.py", "tests/test_journal.py", "docs/quickstart.md"]
acceptance = [
  "`agentmarshal init` creates `.agentmarshal/upstream/` containing a README that states the convention",
  "`agentmarshal init` tells the operator the directory exists and what it is for",
  "an existing `.agentmarshal/upstream/README.md` is never overwritten",
  "failing to scaffold the outbox does not fail init: the project is still initialized",
  "the quickstart mentions the outbox where it describes what init writes",
]
+++

# CR-056: init scaffolds the upstream outbox and says what it is for

## Context

Adopter proposal 012, remaining half. Adopters on a pinned wheel never patch the
tool locally, so everything they notice about it has exactly one addressee:
upstream. With no convention for where that material lives, three adopters
invented three layouts, and four files copied between two of them diverged
within days.

Both halves of the receiving end now exist — `CONTRIBUTING.md` states the
channel, the language rule and the privacy expectation, and `docs/proposals/`
carries a disposition for every proposal. What is missing is the near end: a new
adopter learns the convention only by reading the upstream repository. `init`
knows it is setting up a host repo and is the one moment the operator is looking.

## Objective

Have `init` create the outbox and say what it is for, so the convention arrives
with the tool instead of having to be discovered.

## Acceptance Criteria

- `agentmarshal init` creates `.agentmarshal/upstream/` with a `README.md`
  stating the convention: findings for upstream go here, sanitized at source,
  and the original stays with the reporter.
- `init` names the directory and its purpose on stdout.
- An existing `.agentmarshal/upstream/README.md` is left untouched — an adopter
  who has written their own does not lose it.
- Scaffolding is best effort: if the directory or file cannot be written, the
  project is still initialized and `init` still succeeds.
- The quickstart mentions the outbox where it describes what `init` writes.

## Non-Goals

- A command that sends a proposal anywhere. The channel is a directory and a
  convention, not a transport; how a batch reaches upstream is the adopter's
  choice (see CONTRIBUTING.md).
- Scaffolding anything else — agent guides, harness permission templates. Those
  are vendor-specific and are a separate decision.
- Validating or linting the contents of the outbox.
