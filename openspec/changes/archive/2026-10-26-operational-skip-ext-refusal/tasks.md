# operational-skip-ext-refusal — Tasks

## 1. The change

- [x] 1.1 proposal.md, design.md, tasks.md and the extension-stages
      delta spec are written — the MODIFIED block carrying the
      requirement's heading byte for byte, the `--skip-ext` refusal
      ordered ahead of the operational-lane exception, every scenario
      kept plus the new one — verify: openspec validate.

## 2. Checks and archive

- [x] 2.1 Every scenario in the delta spec is demonstrated by a test
      whose docstring names it — verify: grep the test docstrings
      against the spec's scenario headings.
- [x] 2.2 Full check sequence passes: `uv run agentmarshal validate`,
      `uv run pytest -q`, `uv run ruff check`, `uv run ruff format
      --check`, `uv run mypy` — verify: run them.
- [x] 2.3 Archive with `OPENSPEC_TELEMETRY=0 npx -y
      @fission-ai/openspec@1.15.0 archive operational-skip-ext-refusal
      --yes` — verify: the requirement's new text lands in
      `openspec/specs/extension-stages/spec.md` and the change moves
      under `openspec/changes/archive/`.
