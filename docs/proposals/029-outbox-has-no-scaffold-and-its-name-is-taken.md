# 029 — The outbox convention has no scaffold, and the command name an adopter reaches for is taken

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:929e6c4f03ce07452a3c9c434c1ebb183716ef719aeccf628a21f73e3f1d6f68` · **Disposition:** accepted

## Finding

The outbox is described in three documents and implemented in none of them.
`CONTRIBUTING.md` gives the shape of a report — Symptom, Measurements,
Version, Environment, Expected — and names `.agentmarshal/upstream/` as the
convention for collecting findings until a batch is ready;
`docs/proposals/README.md` explains how to follow a sent proposal afterwards
by hashing the file. Between those documents sits everything an adopter
does, and the tool touches none of it: nothing creates the directory,
nothing writes a skeleton carrying the five fields, nothing looks at a draft
before a batch leaves. The shape survives exactly as long as someone
remembers it.

The name an adopter reaches for is already taken by something else.
`agentmarshal finding` records a hash-pinned research finding **inside a
task's journal**; it has nothing to do with the outbox. An adopter who has
just read CONTRIBUTING, types `agentmarshal finding --help` and finds
`--task` required does not learn they are in the wrong place — they learn
that the outbox is not the thing they thought it was.

Measurements, as reported — thirteen findings written over seven days, all
by the same operator's loop, all after reading and agreeing with the
convention, counted on 2026-09-22 immediately before the two most recent
were brought back to form; the drift is the measurement:

- `## Expected`, the field CONTRIBUTING asks for by name: present in 11 of
  13. The two most recent dropped it, substituting a section that proposes a
  fix instead of stating what was expected and why.
- Environment as CONTRIBUTING defines it — operating system, Python version,
  git provider — is complete in **1 of 13**: the first one written. Five
  more carry one element of it, never all three. The remaining seven name
  the loop's topology and no environment at all.
- The version field survived in 13 of 13. It is also the only one of the
  five that is a command: CONTRIBUTING prints `agentmarshal --version` next
  to it.

The field backed by something executable held for thirteen files; the fields
backed by prose decayed within seven days — not disagreement, but what a
convention does when nothing carries it. And the cost lands upstream: a
digest published from a finding with no environment line either omits it or
reconstructs it from what the maintainer happens to know about that
reporter.

## Proposed

- A subcommand that scaffolds a finding into `.agentmarshal/upstream/`: the
  five fields as headings, version and environment lines pre-filled from the
  machine it runs on, the next free number, and a slug from a one-line
  summary — what `init` already does for trust preconditions, done for
  intake.
- A validation of the outbox over the same code path, naming the file and
  the missing field, so a batch wrapper can refuse to send — before
  publication rather than after it.
- A name that does not collide with `finding`, or a reconciliation of the
  two: today the command whose name matches the documented concept
  implements a different concept.

## Disposition — accepted

Thirteen files, written by an operator who had read the rule and agreed with
it, and the only field that survived intact is the one a command fills in —
the finding proves itself. A project that insists on structure everywhere
else should not leave its own intake to memory; the five fields are the
schema of the thing being collected, and schemas belong in the tool.

Accepted, together with the command proposal 023 already asked for: one
command group covering the whole life of a finding — scaffold, validation,
batching and sending, and reporting back the disposition of what was sent —
the intake half here, the delivery half there, sharing the file and the
hash. Its name will not be `finding`. Accepted; not shipped yet.
