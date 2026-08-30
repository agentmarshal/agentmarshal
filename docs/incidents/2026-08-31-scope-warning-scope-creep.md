# A warning grew into a path taxonomy over five review rounds

**Date:** 2026-08-31 · **Task:** CR-049 · **Outcome:** rolled back, contract amended

## What happened

An adopter reported one defect: `agentmarshal open --scope src`, written without
a trailing slash, produces a contract that matches nothing, because scope entries
are compared as prefixes only when they end in `/`. The failure is silent until
the merge gate refuses a change that is in fact correct.

CR-049 set out to warn about that at open time. Five review rounds later the
implementation was **87 lines** handling repeated slashes, symlinked ancestors,
backslashes in filenames, whitespace-only names, and the difference between a
symlink named directly and one named as an ancestor. The rolled-back version is
**36 lines** and warns about three things: a directory named without its slash,
an entry that names nothing on disk, and an empty entry.

Round by round, the finding that started it is visible:

| Round | Findings | In the contract? |
|---|---|---|
| 1 | empty entry; warning does not follow the gate's matching rule | yes — the reported failure |
| 2 | path normalisation mismatch | yes |
| **3** | **symlinked scope entry** | **no — first time symlinks are mentioned, by the reviewer** |
| 4 | repeated slashes; symlinked ancestor; backslash; whitespace names | no |
| 5 | symlink exact-match false positives | no — refining round 4's own additions |

Nothing in the contract mentioned symlinks, adversarial paths or normalisation.
The escalation began at round 3, when a finding outside the reported problem was
accepted and implemented; rounds 4 and 5 then refined the frame that acceptance
had created. Two of round 4's findings were false positives the earlier rounds
had introduced — a backslash and a space are legal characters in a git path, so
the "hardening" was warning about valid input.

## This happened once already, one month earlier

The same domain — filesystem paths, symlinks, TOCTOU — was hardened the same way
in `backfill.py` (CR-031, opened 2026-07-28) and `project.py` (CR-001, opened
2026-07-27). An internal audit at the time found roughly 40% of a module given
over to filesystem security under a contract asking for "pure mapping and
validation", introducing a fail-closed portability constraint the contract never
sanctioned.

That audit recorded the cause as gold-plating — the implementer over-building,
review failing to catch it. **The commit trail says otherwise**, and the
correction matters more than the original finding:

```
CR-031: address sol re-review F1 (reject symlinked ancestor components)
CR-031: address sol re-review F1 (component-by-component no-follow traversal)
CR-031: address sol re-review F1 (fail closed without O_NOFOLLOW)
CR-031: address sol re-review F1 (non-blocking open to reject FIFOs)
CR-031: address sol re-review F1 (bound the stat-file read)
```

Every piece of that hardening was an answer to a review finding, across roughly
eleven rounds. So this is not a mirror image of CR-049 — **it is the same
mechanism, one month earlier**: a reviewer escalating into filesystem hardening,
an implementer complying round after round, and a contract that mentioned none
of it going unconsulted.

Two things follow. Filesystem and path handling is this project's recurring
attractor for work nobody asked for. And an audit that diagnosed the mechanism
from the finished code rather than the commit trail reached the wrong conclusion
about how the code got there — which is why this record quotes the trail.

## Cause, and what the evidence does not support

The hypothesis worth stating first is the one the data **did not** support. It
looked like acceptance criteria containing universal quantifiers — "for **each**
entry that matches **nothing**" — invite falsification, since one counterexample
defeats them and a reviewer is very good at producing counterexamples. Within
this repository the correlation held: the code tasks with no such quantifier
were approved in a single round, while the two containing them ran to five and
seven rounds.

It did not hold on an independent sample. An adopter's longest review chains —
including one task that took fourteen rounds and never closed — have no such
quantifier at all. Their criteria instead predicted the *result* of an analysis,
which the analysis then contradicted.

What both share, and what this incident supports, is narrower and duller:

> **A criterion that cannot be demonstrated does not terminate.** Quantify over
> an unbounded space (paths, diffs) and a counterexample always exists; predict
> a conclusion and the work can always be argued to have reached a different
> one. Either way the reviewer can keep going, and nothing in the loop says stop.

The code shape is a secondary factor, not the trigger. `project_root / entry`
with `is_dir()` and `exists()` is the canonical shape of a path-traversal check,
but the record shows the reviewer raised symlinks *before* any symlink code
existed. What the shape did was hold the frame: once `is_symlink()` was written
in, the next two rounds stayed inside it.

## The rule now in force

An audit methodology for exactly this class already existed and was not used.
Its second step is the one that matters, and it now applies to every finding
before it is implemented:

**Is the threat or goal the finding names stated in the contract?**

- **Yes** → fix it.
- **No, but plausibly connected** → record it as follow-up; do **not** implement
  it in this task.
- **No and unconnected** → decline it, with the reason.

And criteria are written to be demonstrable: name the cases that must be caught,
rather than quantifying over every case that might exist. CR-049's contract was
amended to do that, and the boundary is now itself a criterion — the docstring
states which forms are deliberately not policed, so the omission reads as a
decision rather than an oversight.

## A footnote the record earned

Publishing this required amending its own contract twice. One criterion forbade
"product names", which literally forbids naming this project in its own incident
record. The other asserted what the investigation would find — that the earlier
occurrence was implementer gold-plating — so once the commit trail showed
reviewer-driven escalation instead, a record stating the truth *failed the
contract*, and review correctly said so.

That second one is the defect an adopter reported to us as proposal 005: a
criterion that predicts a conclusion cannot be satisfied by work that reaches a
different one, and without a repair path the task can only be abandoned and
reopened. We had the repair path — a journal-only amendment — and used it twice
while writing this. The adopter did not, and closed six tasks as abandoned
instead.

## Cost

Five review rounds, roughly fifty lines of code written and removed, and one
contract amendment. No incorrect merge: the gate behaved correctly throughout,
and every version passed its tests. The loss was entirely in work that nobody
had asked for, which is the characteristic cost of this failure and the reason
it is easy to miss.
