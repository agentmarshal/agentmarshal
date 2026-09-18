## Before you open this pull request

- [ ] This work is a `CR-NNN` task, and every changed path is inside its contract's declared scope.
- [ ] This change does not alter the contract, an existing evidence record, or prior task state; evidence records are append-only.
- [ ] If an agent contributed, its session set `AGENTMARSHAL_ACTOR`.
- [ ] Public artifacts, the commit messages, and this pull request's title and description are in English.
- [ ] I ran these project-wide checks successfully:

  ```sh
  uv sync --locked
  uv run agentmarshal validate
  uv run pytest
  uv run ruff check
  uv run ruff format --check
  uv run mypy
  ```

- [ ] I agree that this contribution is licensed under Apache-2.0.

## Before it can merge — nothing to tick here

The process requires these, and you cannot supply them yourself when you open
the pull request:

- an **independent review** of the exact commit, recorded with a reviewer
  identity that differs from the commit authors';
- a **pipeline attestation** for that exact commit, from CI.

See [CONTRIBUTING.md](https://github.com/agentmarshal/agentmarshal/blob/master/CONTRIBUTING.md#this-repository-governs-itself). For a
pull request from a fork, who records the independent review is not yet
settled; say in the description that you need one.
