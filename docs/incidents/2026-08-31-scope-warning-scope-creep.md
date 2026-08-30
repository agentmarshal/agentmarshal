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

## This has happened before, from the other side

A year earlier the same domain — filesystem paths, symlinks, TOCTOU — was
over-engineered in `backfill.py` (CR-031) and `project.py` (CR-001). An internal
audit found roughly 40% of a module given over to filesystem security under a
contract that asked for "pure mapping and validation", introducing a fail-closed
portability constraint the contract never sanctioned.

The mirror is the useful part:

|  | CR-031, a year ago | CR-049, now |
|---|---|---|
| Who added the hardening | the implementer, unprompted | the reviewer asked, the implementer complied |
| What review did | approved with no findings | escalated over five rounds |
| Signature | gold-plating | reviewer escalation |

Same domain, opposite mechanism, and in both cases the contract was the thing
that could have stopped it and was not consulted. Filesystem and path handling
is this project's recurring attractor for work nobody asked for.

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

## Cost

Five review rounds, roughly fifty lines of code written and removed, and one
contract amendment. No incorrect merge: the gate behaved correctly throughout,
and every version passed its tests. The loss was entirely in work that nobody
had asked for, which is the characteristic cost of this failure and the reason
it is easy to miss.
