+++
schema = 1
id = "CR-053"
title = "fail cleanly on a non-UTF-8 repo path, and verify what init and open wrote is readable"
scope = ["src/agentmarshal/project.py", "src/agentmarshal/journal/open_task.py", "src/agentmarshal/cli.py", "tests/test_journal.py"]
acceptance = [
  "find_git_root no longer raises UnicodeDecodeError on a repository path git reports as non-UTF-8: it refuses through the project's own error type, the way the gate already refuses non-UTF-8 git output",
  "init verifies the project file it just wrote can be read back, and reports a failure instead of returning success",
  "open verifies the task contract and opened record it just wrote can be read back, and fails the task creation instead of reporting a path nobody can read",
  "the readback failure names the path and the underlying error, so an operator can act on it",
  "no behaviour changes when the write succeeds, which is every ordinary run",
  "validate/pytest/ruff/format/mypy stay green, with tests for the non-UTF-8 refusal and for a readback failure surfacing as an error",
]
+++

# CR-053: fail cleanly on a non-UTF-8 repo path, and verify what init and open wrote is readable

## Context

Two defects that share a shape: a command reports success while leaving the
operator with something unusable.

**Adopter proposal 011.** On a Windows host a task directory created from inside
a sandboxed executor session inherited that sandbox's ownership — inheritance
disabled, rights only for the owner, `SYSTEM` and `Administrators`. The
operator's own account could not read the journal directory of the task that had
just been created, and `open` reported success. The tool's own postcondition —
that a task's contract and records exist and are usable — was not met, and
nothing noticed. Verifying that what we just wrote can be read back belongs in
the command, on every platform; it is the same class of check as refusing to
follow a symlink when creating the project file.

**Found in our own work.** `find_git_root` runs git with `encoding="utf-8"`, so a
repository path git reports as non-UTF-8 raises `UnicodeDecodeError` out of a
function whose contract is to return a path or `None`. The leak-scan command had
to guard its call site rather than rely on it. The gate already treats non-UTF-8
git output as a controlled refusal; this is the same rule applied where it was
missed.

## Objective

Make both commands tell the truth: refuse cleanly when git output cannot be
decoded, and confirm that what was written can be read before reporting success.

## Acceptance Criteria

- [ ] `find_git_root` refuses non-UTF-8 git output through the project error
      type rather than raising `UnicodeDecodeError`.
- [ ] `init` reads back the project file it wrote and fails if it cannot.
- [ ] `open` reads back the contract and the opened record and fails the task
      creation if it cannot.
- [ ] The failure names the path and the underlying error.
- [ ] No behaviour change on a successful write.
- [ ] Suite green, with tests for both failures.

## Non-Goals

- Not auditing platform permissions or ACL policy: the check is that *our own
  write* is readable back, not that the filesystem is configured well.
- Not repairing permissions, which would guess at an operator's intent.
