## Why

ADR-0021 decision 3 decided what an acknowledgement changes on the
hit's surfaces: the hit stays printed, marked — acknowledged, by whom,
and the reason — and an acknowledged hit no longer makes `leak-scan`
exit 1, while a hit nobody acknowledged still does. CR-170 landed the
`acknowledgement` record and CR-187 the `acknowledge` command that
writes it after checking the hit against the same scan. What does not
exist yet is the honouring itself: today the command prints every hit
and exits 1 whether or not the journal carries an acknowledgement
bound to the candidate, so the operator who verified a hit still has
nothing but the record to show for it.

## What Changes

- `agentmarshal leak-scan --base <ref> --commit <rev>` reads the
  journal's `acknowledgement` records whose `commit` equals the
  resolved candidate commit — `git rev-parse --verify <rev>^{commit}`
  in the scanned repository — from every task of the journal, or from
  the one task an optional `--task <id>` names. The records are read
  where the gate reads them: the calling checkout's working tree in
  the embedded placement, the journal repository's working tree under
  a sidecar.
- A record acknowledges a hit only on ADR-0021 decision 2's binding:
  same commit, same file exactly as the scan prints it, same
  identification — a signature id or `private-marker #<n>` — with no
  other matching. A new commit or a renumbered marker list shows the
  hit again as unacknowledged.
- Every hit still prints in today's order and form; an acknowledged
  hit's entry additionally carries a mark naming who acknowledged it
  and the reason, each escaped on display. Nothing is removed, and the
  matched text is never printed.
- The command exits 0 when the scan finds hits and every one is
  acknowledged, 1 when any hit is unacknowledged, and exactly as today
  when the scan finds nothing. When the journal or a task's records
  cannot be read, no hit counts as acknowledged and the command says
  why on stderr.
- The specification's exit-status sentence is revised the way
  ADR-0021 named it: the exit status answers whether a hit nobody has
  acknowledged was found, and the interim sentence that had
  `leak-scan` unchanged while `acknowledge` landed is retired.

## Capabilities

- modified: `leak-scan`

## Impact

The standalone command's output gains the mark on acknowledged hits
only; a run with no acknowledgement prints and exits byte for byte as
today. The gate's leak-scan line and its bound are untouched —
marking there is a later task — so the pinned merge transcript stands.
`status` already shows the record's own line and the
self-acknowledgement mark, both unchanged here. No record type, no
scan behaviour and no other command changes; the acknowledgement stays
what the threat model published it as — declared and durable, not
proven.
