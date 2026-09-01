+++
schema = 1
id = "CR-083"
title = "0.3.0: the version, the changelog, and the documentation that must be true at the tag"
scope = ["pyproject.toml", "uv.lock", "src/agentmarshal/__init__.py", "tests/test_smoke.py", "CHANGELOG.md", "UPGRADING.md", "README.md", "docs/overview.md", "docs/quickstart.md", "docs/sidecar.md", "docs/adr/ADR-0004-journal-data-model.md", "docs/adr/ADR-0005-evidence-capture-and-format.md"]
acceptance = [
  "every place that encodes the version reads 0.3.0: pyproject, __init__, uv.lock and the smoke test that pins it",
  "the changelog entry names what actually landed since 0.2.0 and says plainly what each capability does not do",
  "UPGRADING states what upgrading from 0.2.0 requires, including the one arrangement that breaks: a sidecar journal read by a 0.2.0 checkout",
  "no document says a capability is active in a release where it is not; every 'Status in 0.2.0' note either still holds or is corrected",
  "docs/sidecar.md drops its duplicated argument and keeps its operational content; the three advisory findings recorded against CR-082 are fixed",
  "no install command is changed to name 0.3.0, because 0.3.0 is not published yet and this task cannot verify one",
  "the release date is not written anywhere by this task",
]
+++

# CR-083: the documentation the release ships

## Context

Since 0.2.0 the repository closed wave P (CR-078, the deferred proposals
re-read), all of wave J (CR-077 ADR-0008, CR-079 the sidecar placement, CR-081
the advisory gate, CR-082 the second install-and-operate path), and part of
wave M (CR-080, which made live session recording possible at all, plus the
economics backfill). That is a release.

Two debts ride with it. CR-082's completion record names three advisory
findings that shipped deliberately rather than through a ninth review round.
And the over-engineering audit of the same document found it at 424 lines — 27%
of the whole documentation set, for an experimental placement whose gate decides
nothing — with a third of that restating ADR-0008 and its own opening.

## Objective

Make every version-bearing file and every version-bearing sentence say 0.3.0
truthfully, write the changelog and the upgrade procedure, and pay the two
documentation debts in the same pass rather than in two review cycles.

## Acceptance Criteria

- The version reads `0.3.0` in `pyproject.toml`, `src/agentmarshal/__init__.py`,
  `uv.lock`, and `tests/test_smoke.py`, which pins it. `uv sync --locked`
  accepts the tree afterwards.
- `CHANGELOG.md` gains a 0.3.0 entry naming what landed: the sidecar placement
  and its advisory gate, session records after a task closes, the economics
  channels, the second documentation path, and the package's declared
  repository URL. Each entry says what the capability does **not** do — in
  particular that a sidecar gate decides no merge and that a sidecar contract is
  not pinned to a base commit.
- `UPGRADING.md` states the procedure from 0.2.0 and names the one arrangement
  that genuinely breaks: a sidecar journal is unreadable to a 0.2.0 checkout,
  which sees `placement`/`host` as unknown keys and treats the journal
  repository as its own host. Record formats are otherwise unchanged in both
  directions, and the guide says so rather than implying a break there is none.
- No document claims a capability is active in a release where it is not. Every
  "Status in 0.2.0" note in the ADRs is checked: corrected to name 0.3.0 where
  it still describes the shipped state, left alone where it is a historical
  statement about 0.2.0.
- `docs/sidecar.md` loses the argument it duplicates — the closing placement
  comparison, the expanded restatement of ADR-0008's context, and the
  justification prose already in ADR-0008 Decision 3 — and keeps every
  operational instruction, transcript and rough edge. The three advisory
  findings against CR-082 are fixed: the outbox notice goes to stdout and not
  stderr; the `open` example's scope warning is shown or explained; the gate's
  own advisory leak-scan and its `WARN` line are named.
- **No install command names 0.3.0.** The version is not on the index when this
  task runs, so no command here can be verified against it. Switching the
  install instructions is the publication task's work, together with running
  them.
- No release date is written. The date belongs to the upload, which has not
  happened.

## Threat model and boundaries

The hazard is a **release that claims more than it ships**. The capabilities in
this release are unusually easy to overstate: an advisory gate reads like a
gate, a placement that records evidence reads like a placement that enforces it,
and a changelog is where that overstatement would be most durable. Every entry
therefore carries its own limit, in the same sentence rather than in a footnote.

The second hazard is the one this project keeps meeting: a documentation claim
that outruns its verification. This task deliberately cannot verify an install
from the index, so it changes no install command — a claim we cannot check is
not written and then repaired later.

Not defects in this task: that the sidecar placement stays experimental; that
the capture policy and attestation projection remain roadmap; that a 0.2.0
checkout cannot read a sidecar journal, which is a consequence of the feature
rather than a fault in it.

## Non-Goals

- **Publishing.** The tag, the build, the upload, the install-command switch and
  the smoke test against the index are the next task's, not this one's.
- **Any code change beyond the version constant.** No behaviour changes in a
  release-preparation task.
- Wave S (opt-in DSSE signing), M1 (the session fields that do not exist),
  D2 and E′. They are not in this release, and the changelog does not pretend
  otherwise.
- Rewriting the Russian sidecar guide, which lives in another repository.
