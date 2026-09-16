# 016 — Reviewer prose is not durable in the published release, contrary to the quickstart

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:932ed62a172073c8192969ce8a1810b2d72acee644cc956d3b18e09173d19265` · **Disposition:** accepted *(in part; the third request is met in another shape)*

## Finding

The quickstart says a successful model review pins the reviewer's prose under
the task's artifacts directory and prints where it landed. The published release
does not do that. For a review that names findings it writes the prose to a
temporary file and says so; for an approval with no findings it keeps nothing
and says nothing. The finding identifiers are in the record; the sentences
explaining them are in a temporary directory.

For a fix loop this is not cosmetic: the implementer needs the prose to act on a
non-approving verdict, and the operator has to know to fetch the temporary file
before anything else runs.

Measurements, as reported:

- Reviews with blocking or advisory findings on one task: **8 of 8** kept in a
  temporary file, **0 of 8** under the artifacts directory, which the tool never
  created.
- Reviews approved with no findings at all: **1 of 1** left no prose anywhere.
- Workaround cost: about **60 lines** of shell and Python, in which the
  reporter's own wrapper saves the model's output and a collector copies it into
  the journal at completion — code that exists only to keep what the tool
  already had in hand.

## Proposed

Either publish the pinning behaviour that is already on the default branch, or
mark the quickstart paragraph as unreleased so an adopter on the published
release does not build on it. Until then, print the kept-at path for approved
reviews too: the reasoning behind an approval is evidence as much as the
reasoning behind a refusal.

## Disposition — accepted

The behaviour the quickstart describes exists, is tested, and has been on the
default branch since shortly after the release. That is not a defence. Our
documentation lives in the same repository as unreleased work and describes the
branch rather than the release, and the version number does not separate them: a
build from the default branch reports the same version as the published one, so
neither the reader nor the tool can tell which set of promises applies.

The reporter paid sixty lines for that, which is the honest measure of the
defect. Two things follow, and both are accepted. The behaviour ships in 0.4.0,
which this proposal has moved earlier in the plan. And the documentation stops
describing unreleased behaviour as though it were current:
a paragraph that describes work not in the latest release says so, in the
paragraph, until the release catches up.

The reporter's third request — print the kept-at path for approved reviews as
well — is met on the default branch in a different shape, and the difference is
worth stating rather than folding into a blanket acceptance. On the path the
request is about there is no kept-at file any more: an approving review with no
findings pins its prose in the journal like every other model review, and the
command names the artifact instead. A verdict that fails to parse, or one
refused by record validation, still keeps its output in a temporary file and
says where — the one place that line survives. What the request was for, the
reasoning behind an approval surviving the run, is what ships. What it asked for literally is what
0.4.0 removes.
