## Why

ADR-0021 decided an operator who has verified a leak-scan hit records an
`acknowledgement` of it — bound to the candidate's commit, the file and
the hit's identification exactly as the scan prints it, with a reason —
and CR-170 gave the journal the record type and its schema-7 rules. What
does not exist yet is the way an operator writes one: an acknowledgement
today is a record with no command, so the verification it exists to keep
still evaporates or is completed outside the tooling.

## What Changes

- `agentmarshal acknowledge --task <id> --base <ref> --commit <rev>
  --file <path> (--signature <id> | --marker <n>) --reason <text>`
  writes one `acknowledgement` record through
  `create_acknowledgement_record`, the commit resolved to its full
  40-hex id in the scanned repository — the host's under a sidecar —
  and is registered from its own module the way `agree` is.
- Before writing, the command runs the same added-content scan
  `agentmarshal leak-scan --base --commit` runs — the same merge base,
  the same per-file diff, the project's private markers read from the
  same trusted side, the same `scan_diff_for_leaks` — and writes only
  when the scan reports a hit with exactly that file, as the scan prints
  it, and that identification: a signature id or `private-marker #N`.
  Otherwise it refuses, naming the file and the identification it was
  given and how many hits the scan did report — never the matched text.
- An unknown or terminal task, a commit or base that does not resolve,
  both or neither of `--signature` and `--marker`, a value the record
  rules refuse — the reason's 1000-character bound included — and a hit
  the scan does not report are each refused writing nothing. A recorder
  that is not a declared actor is accepted and the output says so.
- `leak-scan`'s exit status and output are unchanged: honouring and
  marking acknowledged hits on the hit surfaces is a later task. The
  requirement text that said the writing command comes with its own
  task is updated to name it.

## Capabilities

- modified: `leak-scan`

## Impact

One new command and one new module; no other command's behaviour or
output changes. The scan stays advisory and the record stays what
ADR-0021 made it: an acknowledgement does not suppress a hit here —
nothing reads acknowledgements back yet but `status` — and no role or
authentication is added beyond the declared-identity boundary the
threat model publishes.
