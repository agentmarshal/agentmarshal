# 012 — No convention for sending findings upstream

- **Reporters:** Adopter A, Adopter B · **Observed on:** 0.1.0 · **Disposition:** accepted, shipped

## Finding

Adopters using a pinned wheel never patch the tool locally, so everything they
notice about it has exactly one addressee: upstream. There was no convention for
where such material lives or how to send it, so findings settled in chat logs
and commit messages and never arrived.

Both reporters invented a directory of their own and asked upstream to
standardise one. The cost of not having it is visible in this batch: three
adopters produced three different layouts, and four files copied between two of
them diverged within days — an un-owned duplicate drifts almost immediately.

## Proposed

Make the outbox a documented convention rather than a local invention.

## Disposition — accepted, shipped

Both halves now exist. Upstream documents the channel, the language rule and the
privacy expectation in [CONTRIBUTING.md](../../CONTRIBUTING.md), and this
directory is the receiving end with a stated disposition for every proposal.
Downstream the convention is `.agentmarshal/upstream/` in the adopter's own
repository.

One point from the reports is worth repeating here because it shaped the policy:
proposals arrive from private repositories, and a public repository cannot
un-publish. So the rule is sanitize at source, upstream publishes digests, and
the original stays with the reporter.

Not yet done: `agentmarshal init` does not scaffold the outbox directory or say
anything about it, so a new adopter still has to read this to learn the
convention. That is the remaining part of the fix.
