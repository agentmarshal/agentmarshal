+++
schema = 1
id = "CR-050"
title = "incident record: a warning grew into a path taxonomy over five review rounds"
scope = ["docs/incidents/"]
acceptance = [
  "docs/incidents/ holds a record of the CR-049 escalation: what was built, over how many rounds, and what was rolled back, with the measured numbers",
  "it names the precedent — the same filesystem/path domain was over-engineered a year earlier from the opposite direction, gold-plated by the implementer and approved by review with no findings",
  "it states the cause it can support and says plainly which hypothesis the data did not support, rather than presenting a tidy explanation",
  "it states the rule adopted: a finding is tested against the contract's stated threat before it is implemented, with the three dispositions",
  "no adopter, client or third-party product name appears; downstream tasks are referred to by pseudonym (this project's own name is not such a name)",
  "no code change; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-050: incident record: a warning grew into a path taxonomy

## Context

CR-049 added a warning for a scope entry that cannot match — a defect an adopter
reported, whose whole content was a missing trailing slash. It went through five
rounds of review and arrived at 87 lines handling repeated slashes, symlinked
ancestors, backslashes in filenames and whitespace-only names. None of that was
in the contract, and no stated threat required it. The operator stopped the work
and asked why it had happened.

The answer is worth publishing rather than filing privately. This project's
stated position is that its mistakes are part of what it offers, and this is a
governance tool failing at its own discipline: the contract existed, the audit
methodology for exactly this class existed, and neither was consulted while the
scope grew round after round.

There is also a precedent in the same domain, pointing the other way, which
makes the pattern rather than the instance the thing worth recording.

## Objective

Publish the incident: what happened with numbers, the precedent, the cause as
far as the evidence supports it, and the rule now in force.

## Acceptance Criteria

- [ ] Record of the escalation with measured numbers and the rollback.
- [ ] The precedent named, including that review missed it then.
- [ ] Cause stated honestly, including the hypothesis the data did not support.
- [ ] The adopted rule and its three dispositions.
- [ ] No adopter/client/third-party product names; pseudonyms for downstream
      tasks. This project's own name is not one of them.
- [ ] No code change; suite green.

## Non-Goals

- Not re-litigating CR-049's disposition — the rollback has landed.
- Not a policy for the reviewer's behaviour; this records our own.
