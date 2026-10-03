# Proposal

## Why

ADR-0020 decided the `outbox` command group: `init` scaffolds
`.agentmarshal/upstream/` — one file per finding for upstream — but nothing
fills or checks the files. Proposal 029 measured the cost: of thirteen
findings written by an operator who had read and agreed with the convention,
the full Environment line survived in one, and the only field that survived
in all thirteen is the one a command fills in.

## What Changes

- `agentmarshal outbox new "<gist>"` writes a new draft into the project's
  outbox — numbered with the next free number and a slug of the gist —
  carrying the five fields of CONTRIBUTING's finding form as headings, with
  Version and Environment filled from the machine the command runs on.
- `agentmarshal outbox check` reads every draft, names the file and each
  missing or still-unfilled field for each one that does not conform, runs
  the merge boundary's leak scan — with the project's configured private
  markers — over what would be sent, and refuses by exit status so a batch
  wrapper can refuse to send.
- The group registers itself from `src/agentmarshal/outbox.py`; `cli.py`
  gains only the hook.
- `outbox send` and `outbox status` are ADR-0020 decisions 4–5 and a later
  task.

## Capabilities

### New Capabilities

- `outbox`: the scaffold and the pre-send check for upstream finding drafts
  — what a draft is named, the fields it must carry, what counts as
  unfilled, the leak scan over what would be sent, and the exit-status
  refusal a batch wrapper relies on.

## Impact

A new module `src/agentmarshal/outbox.py`, a one-line hook in the parser
setup and one in the dispatch of `cli.py`, and tests under `tests/`. The
scan reuses the existing leak-scan helpers (`capture.py`) and the private
markers already configured in `project.json` — no new configuration and no
new dependencies.
