# 014 — `init` leaves the trust preconditions unconfigured, and `doctor` does not check them

- **Reporter:** Adopter D (greenfield project on Linux, GitHub, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:df93c52e9b1a3e6d` · **Disposition:** accepted

## Finding

`init` writes the project file and the outbox README and stops. Everything that
makes a review record trustworthy is left to the operator, and no command
notices when it is missing. Two of the unconfigured settings break the guarantee
silently rather than loudly:

1. **Squash or rebase merges left enabled on the provider.** A squash merge
   rewrites the reviewed SHA, so the `review` and `completed` records keep
   pointing at a commit that is not in the default branch. Nothing reports it.
   The reporter caught it only because the SHA-binding rule is stated in the
   README, and disabled both merge methods by hand before the first task.
2. **The actor variable unset in the agent's harness.** Records written by an
   agent then resolve to the human's git identity, and `doctor` still says all
   four checks passed.

Measurements, as reported:

- Manual configuration steps needed after `init` before the first governed task
  could complete: **9** (CI workflow from the template with 3 placeholders;
  reviewer command; actor variable in the harness; harness allowlist; provider
  merge-method restriction; default-branch protection attempt; a wrapper to
  avoid command substitution in agent commands; a wrapper to run journal-only
  transactions through pull requests; branch-protection hooks because provider
  protection was unavailable on the plan).
- Of those 9, **2** cause silent evidence corruption if skipped; **0 of 9** are
  checked by `doctor`, whose four checks are git, repository, project file and
  schema.
- Launches of `agentmarshal review` that failed on configuration before the
  first success: **3 of 3**.
- Elapsed from `init` to the first gate pass on a throwaway task: about
  **6 minutes**, with the source of the review launcher open.

## Proposed

Print a checklist at `init` of the preconditions the tool cannot verify but its
guarantees depend on, and have `doctor` verify the ones it can: the actor
variable, a reviewer command whose placeholders are valid and whose dry launch
returns a parseable verdict, a CI definition that invokes `validate`, and — when
the provider can be queried — squash and rebase merges disabled with a warning
when branch protection is absent. Explicitly not a wizard: the harness and
provider layers age on their own schedule.

## Disposition — accepted

The two silent ones are the whole finding. A guarantee that fails loudly costs
an operator an hour; a guarantee that fails silently costs the evidence, and
this project's only claim is about evidence. That `doctor` reports four green
checks while both are unset is the defect, not the number of setup steps.

We will not configure a provider on an operator's behalf: execution and
provider configuration belong to the harness layer, and that boundary is what
keeps this tool from growing a wizard it would then have to maintain. Reading a
provider's merge configuration when its CLI happens to be present, and saying
what we found, is on the right side of that line.

Accepted for the next release, with the reporter's split kept: a printed
checklist for what we cannot check, real checks for what we can.
