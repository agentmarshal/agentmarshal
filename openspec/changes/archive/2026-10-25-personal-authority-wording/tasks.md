# personal-authority-wording — Tasks

## 1. The change

- [x] 1.1 proposal.md, design.md, tasks.md and the extension-stages
      delta spec are written — the MODIFIED block carrying the
      requirement's heading byte for byte, the enforced bound and the
      same-user caveat in under 500 characters, every scenario kept —
      verify: openspec validate.

## 2. The release notes

- [x] 2.1 `CHANGELOG.md`'s 0.6.0 personal-extensions paragraph says a
      personal extension has no write path into the journal through the
      core and names the same-user caveat, every other statement
      unchanged — verify: the diff touches only that paragraph.
- [x] 2.2 `UPGRADING.md`'s personal-extensions bullet says the same —
      verify: the diff touches only that bullet.

## 3. Checks and archive

- [x] 3.1 Every scenario in the delta spec is demonstrated by a test
      whose docstring names it — verify: grep the test docstrings
      against the spec's scenario headings.
- [x] 3.2 Full check sequence passes: `uv run agentmarshal validate`,
      `uv run pytest -q`, `uv run ruff check`, `uv run ruff format
      --check`, `uv run mypy` — verify: run them.
- [x] 3.3 Archive with `OPENSPEC_TELEMETRY=0 npx -y
      @fission-ai/openspec@1.15.0 archive personal-authority-wording
      --yes` — verify: the requirement's new text lands in
      `openspec/specs/extension-stages/spec.md` and the change moves
      under `openspec/changes/archive/`.
