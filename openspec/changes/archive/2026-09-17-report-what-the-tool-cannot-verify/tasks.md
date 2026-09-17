## 1. `init` states what it cannot verify

- [x] 1.1 `init` prints the preconditions once, each with what is lost if skipped, including the merge-method and actor cases — verify: test on the output of `init` in a new project.
- [x] 1.2 `init` configures no provider and no harness — verify: read the diff.

## 2. `doctor` reports what it can reach

- [x] 2.1 A check reports the actor variable, saying records resolve to the invoking git identity without it — verify: doctor test with the variable unset and set.
- [x] 2.2 A check reports whether the configured reviewer command's placeholders resolve, without printing the command — verify: doctor test asserting a secret in the template does not appear.
- [x] 2.3 A check reports whether a CI definition invoking `validate` exists — verify: doctor test with and without one.
- [x] 2.4 A missing precondition leaves `doctor`'s exit status as it was, and the summary line no longer claims all checks passed when one is unmet — verify: CLI test.

## 3. The provider template

- [x] 3.1 The gate job succeeds without judging, with a message, when the head carries no review record for its SHA, and runs the gate when it does — verify: read the template; the shipped file has no test harness, so the reasoning is in design.md.
- [x] 3.2 `continue-on-error` is removed from that job — verify: read.
- [x] 3.3 The self-hosting document states that the task identifier is read from the head reference, so journal-only branches must carry it — verify: read.
