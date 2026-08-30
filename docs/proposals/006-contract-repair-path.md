# 006 — A defective contract can only be abandoned

- **Reporters:** Adopter A, Adopter B (Python web service on Linux and business-application project on Windows) · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

Twice on one project the work was sound and review kept refusing, because the
defect was in the **contract**, not in the code. There is no way to repair a
contract once a task is under way, so the only exit is to abandon the task and
reopen it.

Verbatim from the report:

- One task's criterion predicted the conclusion of an analysis ("there is one
  cause"); the analysis found two. **Six refusals in a row.** Closed as
  `abandoned`, reopened with a criterion that does not dictate the count.
- Another criterion admitted two readings, one of which was impossible to
  satisfy honestly. **Three refusals**, and on the second run the remarks became
  **mutually exclusive** — one clause required what another forbade. Closed as
  `abandoned`, reopened, and accepted **on the first run with the same code**.

Adopter B raises the same shape from the other end: a completed task sometimes
needs to be reopened, and the model has no path for it.

## Proposed

A contract amendment path — a repair that is recorded rather than a lifecycle
restart — and a defined way to reopen a completed task.

## Disposition — accepted

"Accepted with the same code after reopening" is the decisive evidence: the
cost was pure process, and the journal now records an abandonment that
misattributes the defect to the work. That is an evidence-quality problem, not
only an ergonomic one.

The design constraint is that records are append-only and a contract is read
from the base side so a candidate cannot widen its own scope — so a repair must
be an appended, reviewable amendment, never an edit. That is compatible with the
model; the planned contract-schema RFC is the right vehicle. Note that this and
proposal 007 are linked: an amendment path reduces how often an operator needs
to overrule a reviewer, but does not remove the need.
