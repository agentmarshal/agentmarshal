# 019 — Journal-only transactions assume direct commits to the base branch

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:fb551e203f2f4fca47f1b4a94621eb34291ad872edf6167acf0134a10108009a` · **Disposition:** accepted

## Finding

The quickstart commits opening, amendment and completion straight to the base
branch. A repository that forbids direct commits — by provider protection or by
hooks — needs every journal transaction to travel through its own branch and
pull request, and neither the documentation nor the CLI helps: the branch has to
be named so the CI gate can find the task, the working tree has to be clean
outside the journal, and after completion the review and completion records sit
untracked on the base checkout until someone wraps them into a pull request.

The reporter wrote a wrapper. Every adopter with a protected base branch will
write the same one.

Measurements, as reported:

- Journal-only pull requests per task in that flow: **2 to 3**, each waiting
  about **1 minute** of CI.
- Wrapper size: about **40 lines** of shell, plus **20** shared with the
  completion wrapper for the wait-for-check logic.
- A failure mode hit once and then guarded against: the wrapper's own failure
  leaves the checkout on the journal branch, and a rerun reports nothing to
  commit although the commit exists and only needs merging.

## Proposed

Document the protected-base pattern next to the self-hosting workflow — this
repository already merges its own completion pull requests, so the pattern is in
use — and ship either a small command or an example script that creates the
branch, stages only the journal, runs the leak scan and prints the pull-request
command.

## Disposition — accepted

The pattern is not merely in use here; it is how this repository has worked for
every task of the last two releases, through a driver that has never left the
operator's machine. Publishing the documented pattern and a worked example is
overdue, and the reporter's measurement of what it costs to rediscover — sixty
lines and one failure mode — is the argument for shipping the example rather
than only the prose.

We will ship it as a documented pattern with a script under the templates
directory rather than as a CLI command. A command would have to know about
providers, protection schemes and merge policies, which is the harness layer
this project deliberately does not enter. A script an adopter reads and adapts
carries the knowledge without the tool acquiring an opinion about their
provider.

Accepted for the next release, together with the branch-naming requirement
named in proposal 017.
