+++
schema = 1
id = "CR-073"
title = "The review tests must not read the whole system temp directory"
scope = ["tests/test_review_launcher.py"]
acceptance = [
  "the snapshot assertion is scoped to the temporary directory the test itself controls, not the system one",
  "a leftover `agentmarshal-review-*` directory elsewhere in the system temp does not fail the suite",
  "the assertion still fails when the code under test genuinely leaves a snapshot behind",
  "the preserved-output assertions are scoped the same way",
]
+++

# CR-073: The review tests must not read the whole system temp directory

## Context

`_assert_no_snapshot` globs the **system** temporary directory for
`agentmarshal-review-*` and asserts the result is empty. Any such directory
anywhere on the machine fails it, whoever created it and whenever.

This has produced false failures four times in this repository — thirteen tests
at once each time, all in `test_review_launcher.py`, none related to the change
under test. The cause each time was a leftover from a real `agentmarshal review`
run, not from the suite.

It is not a local annoyance. An adopter who runs `agentmarshal review` in one
terminal and `pytest` in another gets thirteen failures with no relation to
their work, and the natural reading of that is that their change broke the
review launcher. A test that fails because of the world outside it is not
testing what it claims to.

The helpers that look for preserved reviewer output (`_kept_outputs`,
`_kept_findings_outputs`) read the same directory and have the same weakness;
they compare against a before-set, which narrows the window but does not close
it.

## Objective

Make these assertions look only at a directory the test owns.

## Acceptance Criteria

- The snapshot assertion inspects a temporary directory **the test controls**,
  not the system one.
- A leftover `agentmarshal-review-*` directory elsewhere in the system temp does
  not fail the suite. Demonstrate it: create one, and watch the suite stay green.
- The assertion still fails when the code under test genuinely leaves a snapshot
  behind. A test that cannot fail is worse than the one being replaced.
- The preserved-output helpers are scoped the same way.

## Threat model and boundaries

Test code. Nothing ships.

The hazard is specific and worth naming: **an isolation fix that quietly stops
testing anything**. Redirecting where the code writes must not also remove the
assertion's power to detect a real leak, which is why demonstrating that it
still fails is a criterion rather than an afterthought.

Not defects in this task: the tool leaving preserved output behind on purpose
(CR-054 decided that removal is the caller's decision), or the accumulation of
those files over time. That is a product question and not this one.

## Non-Goals

- **Changing any source file.** The code under test is correct; the test's
  reach is not.
- Cleaning up preserved reviewer output, or changing when the tool writes it.
- Touching any other test module.
