+++
schema = 1
id = "CR-084"
title = "0.3.0 is published: the documentation installs it and was run against it"
scope = ["README.md", "docs/quickstart.md", "docs/sidecar.md", "CHANGELOG.md", "UPGRADING.md"]
acceptance = [
  "every install command a reader is told to run names 0.3.0 and was executed against the package index; a mention of the unpinned form as the subject of a sentence is not such a command",
  "the whole quickstart was run on a 0.3.0 install, and its verification sentence claims no more than what was run",
  "docs/sidecar.md installs from the index; the pre-release route through a git pin is gone, along with the caveats that existed only because of it",
  "the changelog's 0.3.0 heading carries the PyPI upload date, 2026-09-01, and the entry is otherwise unchanged",
  "no statement remains that is true only of the interim state between the tag and the upload",
  "no statement about what 0.2.0 does is removed or weakened; the framing around one may change where the reader own install changed",
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

- Every install command a reader is told to run names `0.3.0`, and each was
  **executed** against the index before being written down. A sentence *about*
  the unpinned form — "plain `pip install agentmarshal` installs the latest
  published release" — is prose describing a behaviour, not an instruction, and
  pinning it would make it say the opposite of what it means.
- The quickstart is run on a 0.3.0 install — including the session record after
  completion, which is the step that could not run on 0.2.0 — and its opening
  sentence claims **no more than what was run**. Naming a branch that had to be
  run separately, because one pass cannot reach it, makes the claim narrower and
  is required rather than forbidden.
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
- No statement **about 0.2.0's behaviour** is removed or weakened — the gate
  transcript it prints against a sidecar journal, its refusal of a session record
  on a closed task, what it does not know about `placement`. They describe a
  release that exists and are the evidence someone upgrading needs. The framing
  around such a statement may change where the reader's own install changed: an
  exception written for a reader who had 0.2.0 is not the same sentence as the
  fact it carried.

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

## Amendment 1 (2026-09-02)

Three criteria said less than they meant, and two reviewers read them literally,
which is their job.

**"Every install command … names 0.3.0."** Five places name the unpinned form as
the *subject* of a sentence — `README.md:74`, `docs/quickstart.md:26`,
`UPGRADING.md:64,114,116` — explaining what happens when you do not pin. Pinning
those would produce "plain `pip install agentmarshal==0.3.0` installs the latest
published release", which is false and self-contradicting. The criterion now
distinguishes an instruction from prose about a behaviour.

**"Its verification sentence says that and nothing wider."** Aimed at overclaim,
it forbade the correction that removed one: a single end-to-end pass structurally
cannot exercise `accept`, which needs a non-approving latest review, or `reopen`,
which undoes the state that pass arrives at. Both were run separately against the
published 0.3.0, and saying so is narrower than the sentence it replaced. The
criterion now asks for no more than what was run, which is what it meant.

**"Every statement about what 0.2.0 does is left alone."** Aimed at stopping a
sweep of `0.2.0` out of the text because the number looks stale, it also froze
the framing around those facts — including an exception written for a reader who
had 0.2.0 installed and now does not. The fact and its exact message are kept;
the criterion now says so precisely.

This is the third criterion repair across two releases, after CR-083's
"economics channels" and 0.2.0's three. The pattern is consistent enough to be
worth naming: a criterion written as an absolute is read as an absolute, and the
review rounds it costs are spent on my wording rather than on the work.
