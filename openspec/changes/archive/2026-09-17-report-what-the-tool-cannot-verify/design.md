## Context

`doctor_checks` in `doctor.py` is a list of named checks, each a callable
returning `(ok, detail)`; `run_doctor` runs them and the CLI prints a summary.
Adding checks means adding entries, which is the shape this change needs.

The shipped template's gate job carries `continue-on-error: true` and a comment
explaining that the review-bound lane needs evidence the head cannot have. The
workflow run stays green; the check-run does not, and that is what a provider's
merge UI and any wait-for-checks automation read.

## Decisions

- **Departed, during review: the precondition marker lives on the check.** This
  note first let the CLI hold the names of the precondition checks. Renaming one
  dropped it from that list and changed the exit status, which is how the
  duplication was proved rather than argued. `DoctorCheck` carries the flag now.
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
- **The template is not touched here.** An earlier draft of this change asked
  it to succeed without evaluating the review-bound lane. Review showed that
  needs a gate that can be told to leave that lane unexamined, and this task's
  contract forbids a gate change; skipping the whole gate instead would drop the
  scope, append-only, base-state and lifecycle checks it does enforce today.
  Both belong to a task of their own.

## Risks

- [The neutral path hides a genuine refusal] → neutrality is decided by the
  absence of a review record for the head SHA, which is a fact about the
  candidate, not about the gate's verdict.
- [`init`'s checklist becomes a wall of text] → it is a list of preconditions
  with one line each, printed once, at the moment the operator is configuring.
