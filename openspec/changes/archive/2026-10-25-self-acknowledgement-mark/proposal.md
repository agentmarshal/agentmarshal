## Why

Release audit 0.6.0, area commands, finding AUD-commands-3: ADR-0021
decision 5 requires the acknowledgement mark to identify an
acknowledgement by the candidate's declared writer, but only `status`
compares identities — the shared mark `leak-scan` and the gate print
carries the actor and reason only.

## What Changes

- Where an acknowledgement's acknowledging party is a declared author or
  committer, the mark `leak-scan` and the gate's advisory leak-scan line
  print says `self-acknowledged` — the term `status` already uses —
  derived through the writer lookup and comparison CR-237 made shared:
  the gate over the candidate range, `leak-scan` over the commit it
  scans.
- An acknowledgement by any other party prints exactly as today;
  `status`'s output is unchanged.

## Capabilities

- modified: `leak-scan`

## Impact

`report` gains `acknowledging_party_is_declared_writer`, the shared
acknowledgement-side derivation: the record's actor git identities —
resolved through the same `_actor_git_identities` `status` uses, plus
the recorded name itself — held against a writer set by the one
comparison `accepting_party_is_declared_writer`. `status`'s existing
check is that derivation applied to the record's commit; `leak-scan`
applies it over the scanned commit's writers through
`declared_commit_writers`, the gate over the range its
`_range_writer_identities` already reads — looked up lazily beside the
advisory where the verdict block did not run it first. `capture`'s
`_acknowledgement_mark` takes the check as a caller-supplied predicate —
the module stands under the comparison in the import order — and prints
`self-acknowledged` only where the answer is `True`: a check git cannot
answer, like any other party, leaves the mark byte-for-byte what it
prints today.
