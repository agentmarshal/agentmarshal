# 011 — Windows: a new task directory can be created unreadable

- **Reporter:** Adopter B · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

On a Windows host, a task directory created from inside a sandboxed executor
session inherited that sandbox's ownership: ACL inheritance disabled, explicit
rights only for the owner, `SYSTEM` and `Administrators`. The operator's normal
account could not read the journal directory of the task that had just been
created — `open` reported success.

The tool's own postcondition — that a task's contract and records exist and are
usable — was not met, and nothing detected it.

## Proposed

Treat access to the created directory as part of `open`'s postcondition, with a
check the operator can run, and an explicit hook after `open`.

## Disposition — accepted

This is the first Windows-specific defect reported from operation, and it is a
genuine gap rather than a platform quirk: `open` claims success while leaving a
journal the operator cannot read. Verifying that what we just wrote is readable
belongs in the command, on every platform — the same class of check as refusing
to follow a symlink when creating a project file.

Worth stating honestly: AgentMarshal is designed to be portable but has no
Windows test coverage, so this report is also evidence about our coverage, not
only about ACLs. The narrower hook request is folded into proposal 009.
