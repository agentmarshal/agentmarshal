## Context

The gate's two review-bound checks sit together: the approval check, and the
comparison of the declared reviewer's identity against the candidate's writers.
The second already runs only when a review record exists. The first refuses when
none does, with `no review record for <sha>`.

## Decisions

- **The mode is a flag on `gate`, not a placement or an attestation setting.**
  Attestation says who vouches for the pipeline; this says which checks the
  caller is in a position to ask for. Conflating them would make one flag mean
  two things.
- **The mode only changes the no-review case.** When a review record exists it
  is evaluated, whatever the caller asked for. This is the property that keeps
  the mode from being a bypass: it cannot turn a refusal into a pass, only
  report an absence as an absence.
- **Not examined is a line, not a silence.** The transcript says which checks
  were not examined and why, in the same shape as the findings lane's existing
  `NOT EXAMINED:` lines. A reader of a transcript can always tell what was
  judged.
- **The default transcript does not move.** The lines appear only when the mode
  is requested, so the pinned byte-for-byte test and every sidecar transcript
  keep their expectations.
- **The template asks for the mode; it does not decide anything itself.** Its
  guard is gone: deciding what is judgeable belongs to the gate, which can see
  the journal, and not to a shell condition over a tree.

## Risks

- [The mode becomes the habit] → it reports what it did not examine on every
  run that uses it, so a merge authority that uses it by mistake says so in its
  own output. The merge step in this project's own tooling does not use it.
- [An operator reads "not examined" as "passed"] → the transcript names each
  unexamined check on its own line, in the wording the findings lane already
  uses. The gate has no summary line to count them in, and this note earlier
  claimed it did.
