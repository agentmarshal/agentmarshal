## Context

`doctor_checks` in `doctor.py` is a list of named checks, each a callable
returning `(ok, detail)`; `run_doctor` runs them and the CLI prints a summary.
Adding checks means adding entries, which is the shape this change needs.

The shipped template's gate job carries `continue-on-error: true` and a comment
explaining that the review-bound lane needs evidence the head cannot have. The
workflow run stays green; the check-run does not, and that is what a provider's
merge UI and any wait-for-checks automation read.

## Decisions

- **New checks join the existing list.** Same shape, same summary line. The
  three added are the ones the tool can reach without a network: the actor
  variable, whether the reviewer command's placeholders resolve, and whether a
  CI definition invoking `validate` exists.
- **`doctor` does not query a provider.** Proposal 014 asks for a merge-method
  check when the provider CLI is present. That crosses into the harness and
  provider layer ([ADR-0001](../../../docs/adr/ADR-0001-governance-plane.md)),
  needs credentials, and would make `doctor` depend on a network. `init`'s
  checklist states the requirement instead; the reporter explicitly did not ask
  for a wizard.
- **A missing precondition does not change `doctor`'s exit status.** It is a
  report. Operators and CI already treat a non-zero `doctor` as a broken
  project; a newly unset variable is not that.
- **`doctor` never prints the reviewer command's value.** It reports whether the
  placeholders resolve. A vendor template often carries a key, and CR-097
  removed the one place this tool echoed it.
- **The template decides neutrality by looking for the review record, not by
  catching a failure.** The job asks whether the head carries a review record
  for its own SHA before running the gate, and exits neutral with a message when
  it does not. Catching the gate's refusal and reinterpreting it would swallow
  every other reason the gate refuses.
- **`continue-on-error` goes away with it.** A job that succeeds when it has
  nothing to judge and fails when the gate refuses needs no blanket tolerance,
  and the check becomes meaningful enough to require later.
- **"Neutral" is not available, so the job succeeds and says so.** An earlier
  draft of this change asked the template for a neutral result. A workflow job
  has no such conclusion — the mechanism that once produced one was withdrawn,
  and the Checks API path needs an app. The job therefore exits zero with a line
  saying it judged nothing and why, which is what an operator and a
  wait-for-checks automation can both read.

## Risks

- [The neutral path hides a genuine refusal] → neutrality is decided by the
  absence of a review record for the head SHA, which is a fact about the
  candidate, not about the gate's verdict.
- [`init`'s checklist becomes a wall of text] → it is a list of preconditions
  with one line each, printed once, at the moment the operator is configuring.
