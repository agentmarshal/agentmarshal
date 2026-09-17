## Why

CR-100 bounded the rendered leak-scan line at twenty hits because the merge
transcript is a document people read, and shared one renderer between the gate
and the standalone command so the two could not drift. Both reviews of its last
round pointed out the consequence: the bound now also applies to the command an
operator runs precisely to learn where every leak is, and past the twentieth hit
that command answers "and N more not shown" with no flag and no way to see the
rest. The cap was justified by an argument about the gate's line.

Three smaller debts from the same task travel with it: two design notes the
capability spec never carried, the sidecar document still describing the gate's
warning in its pre-CR-100 shape, and `LaunchedReview` missing from the journal
package's exports although the function that returns it is exported.

## What Changes

The bound belongs to the caller that renders into a document of its own. The
gate keeps it and says how many hits it did not show; the standalone command
prints every hit. One renderer still serves both, so the shape of a hit cannot
drift — only the bound differs, and each caller declares its own.

`docs/sidecar.md` describes the gate's warning as it is. `LaunchedReview` joins
`__all__`. The capability spec carries the bound, so the behaviour is specified
where it is published rather than argued in a commit message.

## Capabilities

- modified: `leak-scan`

## Impact

An operator running `leak-scan` on a large candidate sees every hit. The gate's
transcript line is unchanged for any candidate with twenty hits or fewer, and
for more it says what it left out. No record schema changes.
