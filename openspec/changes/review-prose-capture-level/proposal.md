## Why

A review's prose is kept as a journal artifact and committed with its record
(CR-091) on every review `agentmarshal review` records. In an embedded journal
of a public repository that publishes it, and a reviewer process can read
beyond the snapshot it starts in, so the text can carry more than the diff.
There is no way to turn it off.

ADR-0005 Decision 2 already decides where that switch belongs: a capture
policy whose `reviews` class is `off`, `hash` (a private store) or `commit`,
with the default preset putting reviews at `hash` — not public. `capture.py`
parses the policy from the project file; nothing reads it, and the shipped
behaviour is `commit` regardless.

## What Changes

Both review paths read the `reviews` level from the capture policy of the
journal they write to. `commit` keeps today's behaviour. `hash`, the default,
writes nothing to the journal: `agentmarshal review` keeps the output in a
local temporary file and names it, until the private store exists. `off`
keeps nothing. `submit-review --prose` is refused unless the level is
`commit`. This repository sets `commit`, because it publishes its review
prose on purpose.

## Capabilities

- modified: `review-evidence`

## Impact

A project with no capture section stops committing review prose. Review
records written that way carry no artifacts, which every command already
reads. Nothing already committed changes. The economics and sessions classes
of the policy stay unread.
