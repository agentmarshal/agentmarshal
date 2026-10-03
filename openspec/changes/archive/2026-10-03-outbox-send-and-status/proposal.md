# Proposal

## Why

ADR-0020 decisions 4–5. `outbox new` and `outbox check` gave the outbox a
scaffold and a pre-send check, but the transaction proposal 023 measured is
still missing: nothing stages the batch or commits it, and nothing tells an
adopter which of their sent findings upstream has published. The operator
still sweeps findings into unrelated commits by hand, and still greps the
proposals directory for a sha256 by hand.

## What Changes

- `agentmarshal outbox send` runs the check first and refuses on any
  failure; refuses an outbox that holds no draft; refuses when anything
  outside `.agentmarshal/upstream/` is already staged; otherwise stages
  only the outbox — the README's exclude pathspec applied the other way —
  verifies the staged blobs are what the check vetted, and makes exactly
  one commit of the batch with a message naming the files, then prints
  the commit. A refusal leaves the index as the send found it; a made
  commit is never put back. In a sidecar the commit lands in the journal
  repository, never the host. The command transmits nothing and opens no
  network: delivery stays with the operator.
- `agentmarshal outbox status --index <file>` hashes each file in the
  outbox — the sha256 of the file as it is, lowercase hex — and compares
  the hashes with the `Source:` lines of an index file the operator
  obtains — each occurrence an entry identified by its digest — printing
  for each outbox file whether an entry claims it and which, and listing
  once each index entry that matches no file. A missing or unreadable
  index is refused with a message; no network.
- A file name that is not UTF-8 is named in the escaped printable form the
  leak scan uses for undecodable diff header lines — under the same
  masking — so it no longer crashes `check`, and cannot crash `send` or
  `status` either.
- The commands register from `src/agentmarshal/outbox.py`; `cli.py` keeps
  only the hook it already has.

## Capabilities

### Existing Capabilities

- `outbox`: gains the send transaction and the status report; the check's
  file-naming rule gains the escaped printable form for non-UTF-8 names.

## Impact

`src/agentmarshal/outbox.py` gains `send` and `status`; `tests/` gains the
scenario tests. Git is run with `subprocess` as elsewhere in the code —
`git diff --cached`, `git add`, `git commit`, `git rev-parse` — and the
hashing is `hashlib.sha256`; no new dependencies, no new configuration.
