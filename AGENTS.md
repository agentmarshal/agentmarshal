# AGENTS.md

Rules for an agent implementing a task in this repository. The human-facing
version of this workflow is [CONTRIBUTING.md](CONTRIBUTING.md); where the two
disagree, the task contract wins.

## Reading the task

A task is a contract at
`.agentmarshal/journal/tasks/<task-id>/contract.md`. It declares a scope —
the paths that may change — and acceptance criteria, which are the definition
of done. `agentmarshal brief --task <task-id>` prints the same material plus
the decisions and documents the contract names; run it for the full picture.

If the contract names an OpenSpec change — a directory under
`openspec/changes/` in its scope or its documents — the task implements that
change: work through the change's tasks and tick them off. Archive the
change only when the contract's scope names `openspec/changes/archive/` and
the affected `openspec/specs/<capability>/` directory, and then only with
the archive command (`openspec archive`); never edit a file under
`openspec/specs/` by hand. A new capability's Purpose is written in the
change's delta — the archive command leaves it as a placeholder otherwise.

## Boundaries

- Change only the paths in the contract's scope. If the work needs a path
  outside it, do not change that path — name it in the final report as a
  departure instead.
- Create, change or delete nothing under `.agentmarshal/` — the evidence
  journal is append-only and is written by `agentmarshal` commands, never by
  the implementer.
- When a harness commits the result for you, run no `git commit`, `push`,
  branch switch or history rewrite.
- Check every statement you make about what code or a document does against
  the file itself — read it or grep it — not from memory.

## Checks

Before you finish, run the check sequence CONTRIBUTING.md's Development
section gives, from the repository root, with no path arguments:

```sh
uv sync --locked
uv run agentmarshal validate
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

Make it pass. If a check fails for a reason outside the task's scope, report
the failure rather than widening the diff.

## Report

Finish with a report covering:

- what changed in each file,
- the result of each check above,
- any acceptance criterion not met, with the reason.
