+++
schema = 1
id = "CR-061"
title = "Deliver the contract to the implementer as a briefing"
scope = ["src/agentmarshal/journal/brief.py", "src/agentmarshal/cli.py", "tests/test_brief.py", "docs/quickstart.md"]
acceptance = [
  "`agentmarshal brief --task <id>` writes a briefing to stdout and nothing else, so it can be piped into any agent",
  "the briefing contains the contract's markdown body verbatim, including its Non-Goals and any threat-model section",
  "the briefing states the task id, the declared scope entries, and the acceptance criteria from the header",
  "the briefing states the rules this tool itself enforces: only scoped paths may change, the journal is not the implementer's to edit, and the acceptance criteria are the definition of done",
  "briefing a task that is not open is refused, naming the task's state",
  "briefing an unknown task is refused with a message naming the task",
  "a contract whose header does not parse is refused through the contract error, not a traceback",
  "the quickstart shows the briefing as the way an implementer receives the task",
]
+++

# CR-061: Deliver the contract to the implementer as a briefing

## Context

The contract reaches the reviewer by construction: `review` reads it out of the
reviewed snapshot and puts it in the prompt it builds. Nothing does this for the
implementer. `open` writes `contract.md` to disk, and whether it ever reaches
the party doing the work is a question about somebody's harness.

Measured on ourselves, 2026-08-31: across four tasks implemented by an agent
from the contract, there were **no scope violations and no violations of a
declared non-goal** — two of those contracts explicitly forbade path hardening
that did not appear. But the contract was pasted into the prompt **by hand**
every time. The discipline that produced that result is not in the tool, and a
manual step is one somebody forgets.

The reviewer's prompt is not the model to copy. It is assembled inside a command
that runs the reviewer itself, and this project bundles no implementer and takes
no position on which one an operator uses. So the deliverable is text on stdout,
which any harness can consume, rather than an integration with one.

## Objective

A command that prints everything an implementer needs to work inside the
contract, in a form that can be piped into whatever agent does the work.

## Acceptance Criteria

- `agentmarshal brief --task <id>` writes the briefing to **stdout** and nothing
  else to stdout, so `agentmarshal brief --task CR-001 | some-agent` works.
- The briefing carries the contract's markdown body **verbatim** — its Non-Goals
  and any threat-model section reach the implementer unabridged, since those are
  the parts that bound the work.
- It states the task id, each declared scope entry, and each acceptance
  criterion from the header.
- It states the rules this tool enforces, so an implementer that reads only the
  briefing still knows them: only scoped paths may change, the journal under
  `.agentmarshal/` is not theirs to edit, and the acceptance criteria are the
  definition of done.
- Briefing a task that is not open is refused, and the message names the state.
- Briefing an unknown task is refused, and the message names the task.
- A contract whose header does not parse is refused through the contract error
  type rather than escaping as a traceback.
- The quickstart shows the briefing as how an implementer receives the task.

## Threat model and boundaries

This command **reads** one file from the operator's own journal and prints it.
It writes nothing, deletes nothing, runs nothing, and contacts no network. The
contract it prints is a file the operator wrote themselves.

The project's path protections exist for a different boundary: the gate reads
candidate content supplied by a contributor, where an adversary is real. Nothing
of that applies here, so the following are **not** defects in this task and must
not be guarded against:

- symlinks, path traversal, or TOCTOU on the journal or contract path;
- untrusted content inside the contract, including markdown or prompt-like text.
  The contract is the operator's own specification; sanitizing it would corrupt
  the very instructions the implementer needs, and a contract that could attack
  its own reader is a contract the operator wrote to do that.

What matters here is narrower: the briefing must be **complete and unaltered**,
because a truncated or paraphrased boundary is worse than none — an implementer
would then believe it had been told everything.

## Non-Goals

- **Running an implementer.** This project bundles none and takes no position on
  which one is used. The command emits text; the operator pipes it.
- **Project-specific instructions** such as the repository's test or lint
  commands. The tool does not know them, and inventing a config field for them
  is a separate decision.
- **Reading the contract from a commit** rather than the working tree. An open
  task's contract is on disk; a `--commit` selector can come later if wanted.
- **Any machine-readable output format.** The consumer is a language model.
- **Enforcing that an implementer was briefed.** Nothing detects that, and this
  makes the honest case convenient rather than mandatory.
