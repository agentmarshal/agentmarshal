# ADR-0020: The outbox command group

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0009](ADR-0009-research-findings-lifecycle.md) (the `finding`
record and command — a research finding inside a task's journal, the concept
whose name the outbox must not take) and
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md) (what the
core does not do itself can arrive as a supplied extension under a declared
isolation). It answers
[proposal 012](../proposals/012-upstream-feedback-channel.md),
[proposal 023](../proposals/023-upstream-outbox-has-no-transaction.md) and
[proposal 029](../proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md).

This ADR records a decision. The command group, its checks and the
documentation lines it describes are **not implemented by this document**;
they follow in their own tasks. The present tense below is how a decision is
written, not a claim about shipped behaviour.

## Context

`init` creates `.agentmarshal/upstream/` — the outbox — and writes a README
into it (`_scaffold_outbox`, `project.py`): one file per finding, sent
upstream as a batch; the statement that the outbox is **not journal
evidence**, with the pathspec that keeps it out of journal staging —
`git add .agentmarshal ':(exclude).agentmarshal/upstream/**'`; the
sanitize-at-source rule; and the way to follow a sent finding by its hash.
The scaffold is best-effort — a project whose outbox could not be written is
still initialized — and an existing README is never overwritten. The shape of
a finding — the five fields Symptom, Measurements, Version, Environment,
Expected — lives in
[CONTRIBUTING.md](../../CONTRIBUTING.md)'s "Reporting a finding", not in the
outbox README.

`agentmarshal finding` is a different concept: it records a hash-pinned
research finding inside a task's journal
([ADR-0009](ADR-0009-research-findings-lifecycle.md)), and its arguments —
`--task`, `--summary`, `--artifact` (`cli.py`) — are a journal record's, not
an outbox file's. `docs/proposals/README.md` documents the return half of
the channel: since the batch of 2026-09-16 each published digest carries a
`Source:` line — the sha256 of the file sent — so a reporter hashes their
outbox copy and searches the proposals directory for the result.

Between those documents sits everything an adopter does with a finding, and
the tool touches none of it. Two proposals measured what that costs:

- [proposal 023](../proposals/023-upstream-outbox-has-no-transaction.md):
  the outbox has a convention but no transaction — of the reporter's first
  nine findings, eight were swept into three commits about something else,
  and zero of the eight landed in a commit that mentions findings;
- [proposal 029](../proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md):
  the convention has no scaffold and its name is taken — of thirteen
  findings written after reading and agreeing with the convention, the full
  Environment line survived in one, while the Version field survived in all
  thirteen, and it is the only one of the five a command fills in;
- [proposal 012](../proposals/012-upstream-feedback-channel.md) opened the
  channel itself: a documented convention instead of a local invention —
  shipped — with the transaction behind it still missing.

## Decision

### 1. One command group, named `outbox`

The group covers the life of a finding for upstream — scaffold, check,
send, status — under the name `outbox`. It is not named `finding`: that
name is taken by the journal command of
[ADR-0009](ADR-0009-research-findings-lifecycle.md), and
[proposal 029](../proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md)
measured the collision — an adopter who types `agentmarshal finding --help`
after reading CONTRIBUTING finds `--task` required and learns the wrong
concept.

### 2. `outbox new` scaffolds a draft

`outbox new "<gist>"` writes a new draft into the outbox — named with the
next free number and a slug from the gist — carrying the five fields of
CONTRIBUTING's finding form as headings, with the Version and Environment
lines filled in from the machine the command runs on.

### 3. `outbox check` validates the drafts before a batch

`outbox check` reads the outbox and names, for each draft that does not
conform, the file and the missing field. It also runs the leak scan — the
scan the merge boundary runs (`scan_diff_for_leaks`, `capture.py`) — over
what would be sent. Its exit status refuses on a failure, so a batch
wrapper can refuse to send before publication rather than after it.

### 4. `outbox send` makes one batch commit

After the check passes, `outbox send` stages only the outbox — the
pathspec of the outbox README applied in the other direction, including
`.agentmarshal/upstream/` and nothing else — and makes one commit of the
batch. Delivery stays with the operator: the commit is what leaves the
repository, by whatever channel the operator chooses, and the tool
transmits nothing.

### 5. `outbox status` reports back from an index file

`outbox status --index <file>` hashes each file in the outbox — the same
sha256 over the file as sent — and compares the hashes with the `Source:`
lines of an index file the operator names, reporting which outbox files an
entry claims and which none does. The index is a file: the operator
obtains it and passes its path. The command opens no network.

### 6. The layout documentation says what the outbox is not

The map of places
([ADR-0014](ADR-0014-where-things-live.md)) states it plainly: the outbox
is **neither evidence nor journal** — the one directory under
`.agentmarshal/` that does not record the adopter's own work. Findings for
upstream are not append-only, not task-scoped and not gated; the exclude
pathspec stays the mechanism that keeps them out of journal commits.

## Consequences

- The five fields stop depending on memory: `new` writes them as headings
  and `check` refuses a draft that dropped one — the drift
  [proposal 029](../proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md)
  measured surfaces at send time, on the sender's side.
- The outbox gains the transaction
  [proposal 023](../proposals/023-upstream-outbox-has-no-transaction.md)
  found missing: one commit of the outbox only, so findings stop riding
  along in journal commits — and task commits stop dragging half-written
  findings.
- The channel
  [proposal 012](../proposals/012-upstream-feedback-channel.md) opened
  closes its loop: an adopter learns what became of a finding by matching
  its hash against an index they hold, without asking anyone and without
  the tool touching a network.
- `finding` keeps its journal meaning; the outbox's name cannot be
  mistaken for it.
- A batch wrapper gains a refusal point before publication — the check's
  exit status — rather than upstream asking about a suspect file after it
  lands.

## Alternatives considered

**Name the group `finding`.** Refused — the name is taken by the
research-finding command of
[ADR-0009](ADR-0009-research-findings-lifecycle.md);
[proposal 029](../proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md)
names the collision a defect of its own.

**Keep the convention prose-only.** Refused — the measurements stand:
thirteen files written by an operator who had read and agreed with the
rule, and the only field that survived is the one a command fills in. A
schema belongs in the tool.

**The tool delivers the batch itself.** Declined — delivery stays with
the operator; the channel upstream is reached by is theirs to choose. If
an adopter later wants a networked sender, it arrives as a supplied
extension with its isolation declared under
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md), not as a
core command. `status` reads a file for the same reason: the group keeps
no network.

**Fold the outbox into the journal.** Refused — the outbox is the one
directory under the project directory that is not evidence about the
adopter's own work
([proposal 023](../proposals/023-upstream-outbox-has-no-transaction.md));
journal records are append-only, task-scoped and gated, and a finding
draft is none of those.

**Enforce the fields at the gate.** Refused — the gate decides on
evidence and the contract; the outbox is neither, and its check is a
command a batch wrapper calls, not a gate lane.
