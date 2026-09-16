# 017 — In the GitHub template the gate check is red on every implementation pull request, not advisory

- **Reporter:** Adopter D (greenfield project on Linux, GitHub, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:ee68faf9b69d3145` · **Disposition:** accepted

## Finding

With the documented flow, a review record is written into the working tree and
committed to the default branch only at completion, so the head of an
implementation pull request never contains its own review record. The shipped
template runs the gate on that head with CI attestation, and it fails on the
review check every time. Marking the job as tolerated keeps the workflow run
green, but the check-run itself reports failure, and that is what the provider's
merge UI and any wait-for-checks automation see.

The documentation calls the check advisory. The provider has no advisory state.
It has red.

Measurements, as reported:

- Implementation pull requests with the gate check-run red: **1 of 1**, with the
  validation workflow green on the same head. Journal-only pull requests:
  **0 of 2** red, because the journal-only lane passes.
- The reporter's completion wrapper originally waited for all checks and would
  therefore never have merged anything; it now polls one check-run by name.
  Rounds of independent review spent on that wrapper before the flaw surfaced:
  **1**, and it was a model reviewer that found it, not a person.

## Proposed

Until review materialisation lands, the template job should be neutral when the
pull-request head carries no review record for its SHA — skipping the
review-bound lane and saying so — or it should carry the word advisory in the
check name, so operators and tooling do not require it. The self-hosting
document should also state the branch-naming requirement the template silently
imposes: the task identifier is extracted from the head reference, so
journal-only branches must contain it too.

## Disposition — accepted

This one is uncomfortable to read, because we run into it ourselves on every
implementation pull request in this repository and solved it privately: our
merge tooling polls the validation check by name and ignores the red one. We
never carried that back into the template we ship, so every adopter meets the
defect on their first implementation pull request and writes the same
workaround, as this reporter did.

A check that is structurally red is worse than no check. It trains an operator
to ignore red, and it defeats exactly the automation an evidence tool should be
compatible with. The template will report neutral when the head carries no
review record for its SHA and say why in its output, which is the reporter's
first option and the one that keeps the check meaningful when a review record
*is* present.

The branch-naming requirement will be stated where the template is documented.
Accepted for the next release.
