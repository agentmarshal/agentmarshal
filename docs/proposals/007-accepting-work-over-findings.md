# 007 — The operator cannot accept work over findings

- **Reporter:** Adopter A · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

The gate merges only on an `approved` verdict. There is no other path. In effect
**the acceptance decision belongs to the reviewer, not to the operator** — while
the operator is accountable for the product and the reviewer is a tool.

While remarks find real defects this is correct and works. The problem appears
when review **does not converge**: the remarks change from round to round, the
verdict stays `changes_required`, and the work is fit for purpose. Verbatim from
the report:

| Task | Review runs | Outcome |
|---|---:|---|
| CR-121 | 6 | abandoned → reopened |
| CR-134 | 3 | abandoned → reopened |
| CR-140 | 3 | abandoned → reopened |
| CR-138 | 6 | driven to `approved` |
| CR-145 | **13** | **not closed** |
| CR-146 | 4+ | **not closed** |

The reporter checked and states plainly that the tool offers no bypass.

## Proposed

A recorded way for an accountable human to accept work over outstanding
findings — an override that is evidence, not a hole.

## Disposition — accepted

Thirteen runs on one task is not a reviewer being strict; it is a control loop
that does not terminate. We have independently measured the same root cause: the
reviewer is non-deterministic — five verdicts on one identical commit in our own
repository, one pass and four refusals with different findings each time. Gating
merge on a single non-deterministic verdict can both falsely refuse and, more
dangerously, falsely accept.

Accepted with an explicit constraint on the design: an override must be a
**first-class record** naming who accepted, over which findings, and why — never
a flag that makes a merge look reviewed. The honest framing is that the reviewer
is one input to a decision that a named human owns, and the journal should say
so. Related: proposal 006, and the reviewer-robustness work behind 001.
