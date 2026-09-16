# 021 — A reviewer command cannot report anything: its stderr is discarded on success

- **Reporter:** Adopter D (greenfield project on Linux, GitHub, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:a1d75dd936bfc61a` · **Disposition:** accepted

## Finding

The reviewer command is executed with its output captured, and on a zero exit
only its standard output is returned. The captured error stream is used
exclusively to build the message for a non-zero exit. A wrapper therefore has no
channel to report anything on the success path: every diagnostic it writes is
collected and dropped.

This is not hypothetical for a wrapper that does more than print a verdict. The
reporter's saves the reviewer's prose, the review prompt and the token usage as
evidence, and warns on the error stream when one of those saves fails or a
placeholder does not expand. Those warnings reach nobody. The verdict still
arrives, so the run looks healthy while the evidence it was supposed to leave
behind is quietly missing.

The asymmetry is the surprising part: a wrapper that fails loudly is heard, a
wrapper that degrades gracefully is not.

Measurements, as reported:

- Diagnostics the wrapper emits on the success path: several, one per artifact
  saved plus an unexpanded-placeholder case. Number that can reach the operator,
  the calling script or the journal: **0**.
- Defects in the reporter's own wrapper that this masked, found by an
  independent reviewer reading the code rather than by running it: **2** — a
  silently skipped prompt artifact, and a command group whose failure was
  reported as success.
- Workaround: about **15 lines** of shell that duplicate every diagnostic into a
  file and check afterwards for the absence of each expected artifact.

## Proposed

Forward the reviewer's error stream on the success path — print it, or retain it
beside the reviewer output that is already kept. If the stream must stay
suppressed, say so where the reviewer command is documented, so wrappers are
written with a side channel from the start.

## Disposition — accepted

The reviewer command is operator-configured and already trusted to produce the
verdict that gates a merge. Trusting it with a merge decision while discarding
its warnings is not a defensible split.

The stream will be forwarded on the success path. Where it goes is the one open
question: printing it keeps it visible to the operator, and retaining it beside
the kept reviewer output makes it evidence. The second is more in keeping with
the rest of the project, and it is cheap now that a review record can carry
pinned artifacts. Accepted for the next release; the placement will be stated in
the change that makes it.
