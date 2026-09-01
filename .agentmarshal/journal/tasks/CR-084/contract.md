+++
schema = 1
id = "CR-084"
title = "0.3.0 is published: the documentation installs it and was run against it"
scope = ["README.md", "docs/quickstart.md", "docs/sidecar.md", "CHANGELOG.md", "UPGRADING.md"]
acceptance = [
  "every install command in the changed files names 0.3.0 and was executed against the package index, not composed",
  "the whole quickstart was run end to end on a 0.3.0 install, and its verification sentence says that and nothing wider",
  "docs/sidecar.md installs from the index; the pre-release route through a git pin is gone, along with the caveats that existed only because of it",
  "the changelog's 0.3.0 heading carries the PyPI upload date, 2026-09-01, and the entry is otherwise unchanged",
  "no statement remains that is true only of the interim state between the tag and the upload",
  "every statement about what 0.2.0 does is left alone: those describe the released 0.2.0 and are still true",
]
+++

# CR-084: the documentation installs what shipped

## Context

0.3.0 is on the package index — wheel and sdist uploaded 2026-09-01T16:01Z,
verified by installing `agentmarshal==0.3.0` into a clean environment and
finding `--version` at 0.3.0 and `init --help` carrying `--host`.

CR-083 deliberately left every install command naming 0.2.0, because a command
that cannot be run cannot be verified, and this project has repeatedly paid for
writing an unverified claim and repairing it afterwards. That reservation is
now spent: the commands can be run, so they are written and run.

Three findings recorded against CR-083 were left for this task because
publication is what resolves them: the quickstart's step 8 describes output that
presumes step 7 succeeded (it fails on 0.2.0), and UPGRADING verifies an upgrade
by `--version` where `docs/sidecar.md` calls that the wrong probe — true only
while the pinned pre-release build was the only one carrying the placement.

## Objective

Make the documentation install the released 0.3.0, and say only what was run
against it.

## Acceptance Criteria

- Every install command in the changed files names `0.3.0`, and each was
  **executed** against the index before being written down.
- The quickstart is run end to end on a 0.3.0 install — including the session
  record after completion, which is the step that could not run on 0.2.0 — and
  its opening sentence claims exactly that scope: no wider, and with no
  remaining exception carved out for a step that now works.
- `docs/sidecar.md` installs from the index. The git-pin route and everything
  that existed only to support it goes: the pin's rationale, the note that the
  pinned build's metadata carries no repository URL, and the paragraph that
  disowns `agentmarshal --version` as a probe. The capability check
  (`init --help | grep -- --host`) may stay as a check; it must stop being
  presented as a substitute for a version that could not be trusted.
- `CHANGELOG.md` heading reads `## 0.3.0 — 2026-09-01`, the PyPI upload date, in
  the convention the file's own header states. Nothing else in the entry changes.
- `UPGRADING.md` drops the sentence scoping its procedure to after publication,
  because publication happened.
- Statements **about 0.2.0's behaviour** — the gate transcript it prints against
  a sidecar journal, its refusal of a session record on a closed task, what it
  does not know about `placement` — are untouched. They describe a release that
  exists and are still true.

## Threat model and boundaries

The hazard is the one this release has already produced twice: **a document that
claims a capability is present in a release where it is not**. CR-083 shipped a
quickstart that could not be completed with the install it named, and the
measurement channel caught it after two deciding approvals. The defence is not
care, it is execution — every command in this diff runs before it is written.

The second hazard is over-correction: sweeping `0.2.0` out of the text because
the number now looks stale. Most of those statements are about the released
0.2.0 and are the evidence a reader upgrading from it needs. Only the ones that
describe *the reader's own install* change.

Not defects in this task: that the sidecar placement stays experimental; that
`docs/sidecar.md` is longer than its content warrants, which is recorded in the
backlog as a restructuring of both guides.

## Non-Goals

- **Any code change.** The package is published; its contents are fixed.
- The Russian sidecar guide, which lives in another repository and is already
  written for the published release.
- Retiring the size debt in `docs/sidecar.md`. Removing the pre-release install
  route will shorten it by itself; nothing further is cut here, because the last
  three cuts in that file each removed an operational rule a reviewer had to
  hand back.
- Adopter upgrades, which are operational work outside the release.
