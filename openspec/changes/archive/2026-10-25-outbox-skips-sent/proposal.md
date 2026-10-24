# Proposal

## Why

An adopter's finding (digest 045): an outbox created by hand before the
`outbox` group existed holds ten findings, nine already sent. Their sha256
links each to its public digest, so they cannot be rewritten into the
draft form — but `outbox check` judges every regular file but README.md
as a draft and refuses the batch, and `outbox send` runs the check
first, so it cannot be used at all. `outbox status --index` already
matches outbox files against an index's `Source:` lines by sha256; the
same matching can say which outbox files are already sent.

## What Changes

- The outbox gains a sent manifest — the file `SENT` in the outbox, one
  `<sha256>  <name>` line per file sent — which `outbox send` updates in
  the same batch commit as the drafts it sends, pinned by the same
  checked bytes as every file the commit carries.
- `outbox check` and `outbox send` gain an optional `--index <file>` —
  the same index file `outbox status` parses — and treat as already
  sent, and do not check, a regular file whose sha256 a manifest line
  lists or a `Source:` line of the index claims. A skipped file still
  leaves with the batch, so it is still read and still goes through the
  leak scan; it is only not judged as a draft. Each command prints
  `skipped as sent: <n>` when it skipped any, so skipping is never
  silent.
- A file whose name the manifest carries beside a different sha256 is
  not skipped — its bytes changed since it was sent: it is checked like
  a draft and the check names it as changed after sending.
- The manifest is parsed strictly: a line that is not exactly
  `<sha256>  <name>` does not parse, and `check` and `send` refuse it,
  naming the manifest and the line's number.
- With no new draft, `send` still commits a change the outbox holds to
  a file already sent — a rename, a move inside the outbox — as the
  outbox-only commit, and the manifest follows the new name; with no
  draft and no such change it refuses saying there are no drafts to
  send.
- A refused send leaves the manifest's bytes as it found them, as it
  leaves the index.

## Capabilities

### Existing Capabilities

- `outbox`: the check's notion of a draft gains the already-sent
  exception; `check` and `send` gain the skip and the manifest; `send`
  gains the manifest update inside its batch commit.

## Impact

`src/agentmarshal/outbox.py` gains the manifest read, the index reuse,
the skip and the send-side manifest write; `tests/` gains the scenario
tests. The index parse `status` already runs is factored into a helper
both callers share; `cli.py` is untouched — `check` and `send` gain
`--index` inside the group's own registration. No new dependencies, no
new configuration, no network.
