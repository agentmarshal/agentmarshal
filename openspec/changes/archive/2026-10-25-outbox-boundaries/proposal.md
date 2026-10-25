# Proposal

## Why

Release audit 0.6.0, area commands, found three holes at the outbox's
boundary. AUD-commands-1 (blocking): the outbox follows a symlinked
`.agentmarshal` or `.agentmarshal/upstream`, so a sidecar whose outbox is
linked into its host writes the host — which `docs/threat-model.md`
forbids ("a sidecar never writes its host"). AUD-commands-2 (blocking):
the leak scan reads raw bytes while `git add` applies clean filters and
end-of-line conversion, so a batch can commit content the scan never
saw. AUD-commands-6 (advisory): `outbox status` prints names without the
display-escaping every other subcommand applies.

## What Changes

- Every `outbox` subcommand refuses — one line naming the path, before
  creating or writing anything — when `.agentmarshal/upstream` or a
  component between it and the project root is a symbolic link, and
  `init`'s outbox scaffold refuses the same.
- `outbox send` refuses, naming the file, when the blob id a checked
  file stages as under its path — clean filters and end-of-line
  conversion applied — differs from the blob id of the bytes the check
  read; the sent manifest's update is held to the same rule.
- `outbox status` prints every name through the masked,
  display-escaped rendering the other subcommands use.

## Capabilities

### Existing Capabilities

- `outbox`: the commands gain the linked-path refusal; `send` gains the
  transformed-staging refusal; `status` gains display escaping.

## Impact

`src/agentmarshal/outbox.py` gains the component check in `_locate` and
the two-id pin in `_pinned_blob`; `src/agentmarshal/project.py` gains
the same component check in `_scaffold_outbox`; `tests/` gains the
scenario tests. No new dependencies, no new configuration, no network.
