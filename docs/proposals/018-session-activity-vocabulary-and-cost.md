# 018 — `record-session` has no activity for a coordinating role, and no place for cost

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:c0208b8f26d061716570ce9c2790d3fa7f3ec83c69050a36c83fedaea5164049` · **Disposition:** accepted *(in part; the cost field is deferred)*

## Finding

The session record's activity vocabulary offers implementation, review and
other. The reporter's loop has three paid roles: an implementer, a model
reviewer, and a coordinator — the interactive agent that writes contracts,
launches the implementer, reads the verdict and reports to the operator. It is
the most expensive of the three per task, and the only activity it fits is
other, which reporting cannot distinguish from anything else.

Separately, providers that report a monetary cost per run have nowhere to put
it: the session record carries tokens and provenance, so cost lives in a side
file.

Measurements, as reported:

- Roles in the loop: **3**. Roles that fit the vocabulary: **2**.
- Share of one task's total tokens attributed to the coordinator on the first
  fully measured task: about **75 %**, all recorded as other.
- Cost figures per task the journal cannot hold: **1 per review**,
  provider-reported, kept in a sidecar file pinned by hash.

## Proposed

Add a coordination activity, or make the vocabulary a documented registry the
operator can extend. Consider an optional cost argument with a currency code,
reported separately from tokens, since providers disagree on what a token costs.

## Disposition — accepted for the activity, deferred for the cost field

The activity gap is real and the measurement makes it undeniable: three quarters
of a task's tokens landing in a bucket named other is not accounting, it is a
shrug. We see the same proportion in this project's own journal, where the
coordinating agent dominates every task. Coordination joins the vocabulary.

The cost field is deferred, with a reason rather than a maybe. Money in an
evidence record is a stronger claim than tokens: it depends on a price list
that changes without notice, on a currency, and on a billing account nobody
reviewing the record can see. Recording it makes the journal assert something it
cannot attest. The work it belongs with is the accounting rework already in the
plan, which has to answer how a per-task figure is attributed when one agent
session spans several tasks; the currency question is cheap to add once that is
settled, and premature before it.
