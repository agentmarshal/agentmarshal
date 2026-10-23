+++
schema = 2
id = "CR-218"
title = "One helper resolves a --commit reference for every command that takes one, and accept --pause/--operational is shown to resolve it in the journal's repository in a sidecar"
scope = [
  "src/agentmarshal/commits.py",
  "src/agentmarshal/journal/acceptance.py",
  "src/agentmarshal/record_ext.py",
  "src/agentmarshal/record_check.py",
  "src/agentmarshal/acknowledge.py",
  "tests/",
]
acceptance = [
  "a new module src/agentmarshal/commits.py holds the one function that resolves a `--commit` reference with `git rev-parse --verify <rev>^{commit}`, never through a shell, and refuses a reference that does not resolve to a full 40-character commit id, with the repository it was asked in named by the caller; the four private `_resolve_commit` copies in journal/acceptance.py, record_ext.py, record_check.py and acknowledge.py are removed and each module calls the shared function, keeping its own error class (each module converts the shared refusal into the exception it raises today)",
  "every message is unchanged byte for byte — `--commit <ref> does not resolve to a commit in the journal's repository` (and `... in the scanned repository` for acknowledge), git's error text appended after `: ` and escaped, `cannot run git: <error>` when git cannot be started; each command's existing tests pass unchanged, and a direct test of the shared function covers a full id, an abbreviated id, a name of a non-commit object, an unknown name and git not being startable",
  "a test of `accept --pause` and one of `accept --operational` in a sidecar placement show the commit resolved in the journal's repository: the sidecar's own head is accepted and recorded as its full id, and a commit only the host holds is refused with nothing written — the pattern of tests/test_record_ext.py's sidecar test",
  "no behaviour of any command changes; no OpenSpec change is needed, because no requirement changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/operator-acceptance/", "openspec/specs/extension-records/"]
decisions = ["ADR-0013", "ADR-0022"]
+++

# 0.6.0 tails: one commit resolver, the sidecar test for accept

## Context

CR-215's review left two advisory findings, both deferred to this task:

- `resolve-commit-duplicated` — journal/acceptance.py, record_ext.py,
  record_check.py and acknowledge.py each carry a private `_resolve_commit`
  that differs only in the exception it raises (and, in acknowledge, the
  name of the repository in the message);
- `sidecar-placement-untested` — the operator-acceptance spec says the
  commit resolves in the journal's repository in either placement, but the
  tests of `accept --pause` and `accept --operational` build only an
  embedded project, so resolving against the host would pass them; the
  sibling command `record ext` has such a test.

## Objective

One place decides what a `--commit` reference resolves to, and the
placement rule of `accept`'s new forms is demonstrated, not only stated.

## Acceptance Criteria

As in the header.

## Non-Goals

- Changing any message, refusal or record.
- Commit resolution in the gate, review or complete (they resolve with their
  own rules and are not part of the duplicated set).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
