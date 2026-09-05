+++
schema = 1
id = "CR-086"
title = "The findings lane: a finding record, a review bound to it, and completion without a diff"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/status.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/complete.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/submit_review.py",
  "src/agentmarshal/journal/acceptance.py",
  "src/agentmarshal/journal/report.py",
  "src/agentmarshal/journal/brief.py",
  "src/agentmarshal/journal/__init__.py",
  "src/agentmarshal/journal/backfill.py",
  "src/agentmarshal/cli.py",
  "tests/test_journal.py",
  "tests/test_backfill.py",
  "tests/test_migrate.py",
  "tests/test_attestation.py",
  "tests/test_gate.py",
  "tests/test_placement.py",
  "tests/test_findings.py",
  "docs/overview.md",
  "docs/sidecar.md",
  "docs/adr/ADR-0008-journal-placements.md",
  "docs/adr/ADR-0004-journal-data-model.md",
  "docs/adr/ADR-0009-research-findings-lifecycle.md",
  "docs/proposals/005-research-findings-have-no-record-type.md",
]
acceptance = [
  "a `finding` record type exists with a non-empty `artifacts` list and a `summary`, registered in the five places a record type is known, and projects to no state",
  "a review record names exactly one of `reviewed_commit` or `reviewed_finding`, an acceptance exactly one of `accepted_commit` or `accepted_finding`, a completion exactly one of `completed_commit` or `completed_finding`; a record naming both, or neither, is refused with a message that says so",
  "a task with an empty scope and at least one finding record can be gated and completed without a commit, through a lane whose transcript prints every line the diff lane prints today — scope, pipeline attestation, record-path collisions, the advisory leak scan — as not examined with its reason, so no diff-lane PASS wording appears over a check that did not run",
  "in that lane the latest review must bind to the latest finding; an approving review of an earlier finding is refused with a message naming both",
  "an artifact whose ref resolves under the journal project root and no longer hashes to its recorded value refuses the lane, naming the artifact; a ref that does not resolve is reported as not verified; a finding none of whose refs resolve is refused, because a pass over nothing verifiable is a pass over nothing examined — all three demonstrated in tests",
  "a task with a declared scope cannot use the findings lane, and the refusal names the scope as the reason",
  "the lane is chosen by what is offered: `gate --task X --findings` enters the findings lane only for an empty-scope task with a finding, and `gate` without that flag keeps today's defaults (candidate = HEAD, task from the branch, base = default branch) and runs today's lanes unchanged on any task, so a branch carrying a change outside `.agentmarshal/journal/` under an empty-scope task takes the diff lane and is refused there exactly as in 0.3.0 — both paths demonstrated in tests",
  "ADR-0008 Decisions 5 and 6 each gain a one-line pointer to ADR-0009 Decision 4, so the exception is discoverable from the rules it qualifies; ADR-0004's description of schema 3 is extended so it does not read as the complete schema history once schema 4 exists; ADR-0009's one reference to \"wave S\" — a label from the operator's private plan — is replaced by the term the public ADRs use for the in-toto projection and signing work",
  "in the findings lane the append-only, added-records and lifecycle checks read the journal's own working tree and commit history — the input the sidecar gate already uses — in both placements, and a test shows a record rewritten in the journal's history refuses the lane",
  "a finding record carries `source` and requires `recorded_by` and `recorded_by_source` (optional on every other record); a finding without a resolvable recorder is refused at write time, and the lane's independence check resolves the recorder to git identities through the actors table as ADR-0009 Decision 3 specifies — an override string is never itself compared — refusing when it resolves to none",
  "acceptance over findings works for a review bound to a finding under the same rules as for one bound to a commit: latest review non-approving, all its blocking findings named",
  "each record is stamped with the schema its content requires, with 3 as the floor: a record carrying neither the new type nor any of the three binding fields is written at schema 3 exactly as today, never lower; a finding, or a review, acceptance or completion bound to one, at schema 4 — and a journal that never uses the lane is written in the same shape and at the same schema stamp as 0.3.0 wrote it, `tool_version` aside, and validates under 0.3.0",
  "a schema-3 record written by this build validates under the published 0.3.0; a schema-4 record is refused by it with the unknown-schema message — both demonstrated in a test that runs the released 0.3.0 when it is installed and skips, saying so, when it is not",
  "the embedded diff lane's gate transcript is unchanged byte for byte, final line included",
  "the journal-only lane treats a commit adding a `completed_finding` record exactly as it treats one adding `completed_commit` — shape, append-only integrity, lifecycle consistency, no re-verification of a preceding gate pass for either — and a test pins that parity so no guard is added for one binding that the other lacks",
  "brief for an empty-scope task says the task lands through findings and no longer says it is implementing or that no change can land",
  "the diff is confined to the scoped files of this repository; closing the two research tasks in the operator's sidecar journal is the operator's act afterwards, not this task's",
]
+++

# CR-086: the findings lane

## Context

ADR-0009 (CR-085) decided how a task whose output is a conclusion, not a diff,
completes: a `finding` record pins its artifacts by sha256; a review may bind
to that record instead of a commit; the gate has a findings lane admitted by
an empty scope plus a finding. The reasoning, the claim boundary and the
alternatives are the ADR's and are not restated here.

Where the pieces already are: `artifacts: [{ref, hash}]` is validated for
every schema-2 record in `records.py`; its only writer is the import path in
`backfill.py`, which no CLI command reaches;
`PREDICATE_TYPES` in `attestation.py` registers a URI per record type;
`_RECORD_TYPE_STATES` in `status.py` projects state; the gate's sidecar
handling already prints "none examined" lines with a reason; `complete.py`
runs the gate and writes `completed` only on a pass.

Where the change reaches — derived from what reads the fields, not from where
the change is expected: `reviewed_commit` is read in `gate.py`,
`acceptance.py`, `review.py`, `submit_review.py`, `report.py` and `cli.py`;
`completed_commit` in `report.py` and `cli.py`. Each of those must understand
the finding-bound variant or say clearly that it does not.

## Objective

Build the three parts ADR-0009 decided, so that a research task can be
recorded, reviewed and completed without a commit — and nothing about the
diff lane changes.

## Acceptance Criteria

- **The record.** `finding` is a record type with `artifacts` (non-empty, each
  `{ref, hash}` — the field from ADR-0005 D5's matrix as `records.py` validates
  it, the hash being sha256 as ADR-0009 D1 decides) and `summary` (non-empty
  string); `recorded_by` and `recorded_by_source` are required on it, and a
  finding whose recorder cannot be resolved is refused at write time. It is
  registered in `_RECORD_FIELDS`, validated in `_validate_record`, has
  `PREDICATE_TYPES["finding"] =
  "https://agentmarshal.dev/attestations/finding/v1"`, projects to `None` in
  `_RECORD_TYPE_STATES`, and has a factory plus `agentmarshal finding --task
  --summary --artifact REF=HASH …` (repeatable). It is refused after a terminal
  record like any lifecycle record.
- **The binding.** A review names exactly one of `reviewed_commit` (40 hex) or
  `reviewed_finding` (a record id present in the same task); an acceptance
  exactly one of `accepted_commit` or `accepted_finding`; a completion exactly
  one of `completed_commit` or `completed_finding`. Both or neither → refused,
  and the message says "exactly one". `submit-review` and `accept` take
  `--commit` or `--finding ID` as a mutually exclusive pair, one required —
  today `--commit` alone is `required=True`, and that changes only by adding
  the alternative. `review` (the model-reviewer path) may reject `--finding`
  for this release with a clear message; if it does, the message says the human
  path is `submit-review`.
- **The lane.** `gate --task X --findings` enters the findings lane when the
  contract scope is empty and the task has a finding; otherwise it refuses
  naming the reason (a declared scope, or no finding). `--findings` is mutually
  exclusive with `--commit` and `--base`; without it, `gate` behaves as in
  0.3.0, defaults included. `complete --task X --findings` is the completion
  form; `complete`'s `--commit`/`--base`, required today, become one side of a
  mutually exclusive pair with `--findings`. The lane computes: the task is not
  closed, read from its projected state in the journal as the sidecar gate
  does; latest review binds to the **latest** finding and is approving — or,
  when it is not, an acceptance record bound to that same latest finding
  through `accepted_finding` exists and satisfies ADR-0007's rules; the
  reviewer is independent of the finding's recorder on git identities — the
  recorder resolved through the actors table per ADR-0009 D3, the lane refusing
  when it resolves to none; each artifact whose `ref` resolves under the
  journal project root re-hashes to its recorded value, and at least one must
  resolve — a finding with no verifiable artifact is refused; append-only,
  records valid and lifecycle consistent, all read from the journal's own
  working tree and commit history (as `_sidecar_tampered_records` does) since
  there is no candidate diff. It prints scope, pipeline attestation, the diff,
  record-path collisions and the advisory leak scan as **not examined**, each
  with its reason — every line the diff lane prints today is accounted for — in
  the wording pattern the sidecar gate uses. `complete` in this lane writes
  `completed` with `completed_finding` (record id) instead of
  `completed_commit`.
- **Acceptance.** `accept --task X --finding ID` records acceptance over the
  latest review of that finding, with the same rules as for a commit.
- **Schema.** There is no schema constant today: `"schema": 3` is a literal in
  the two factory sites of `records.py` and in `backfill.py`. This task
  introduces the notion of the **schema a record needs**: a record carrying
  neither the new type nor any of the three binding fields is written at 3; a
  `finding`, or a review, acceptance or completion bound to one, at 4.
  `_validate_record` admits the new type and field at schema ≥ 4 only.
  Consequence, and the reason the ADR's compatibility promise holds: a journal
  that never uses the lane is byte-identical in what 0.4.0 writes to what 0.3.0
  wrote. `backfill.py` keeps writing 3. The tests asserting `schema == 3`
  (`test_journal.py`, `test_backfill.py`, `test_migrate.py`) keep asserting it
  for the records that stay at 3, and new tests assert 4 for the records that
  need it. CR-069 did the opposite for 2→3 — stamped every record 3 — and that
  is where the 0.1.0→0.2.0 coordination break came from; this task does not
  repeat it.
- **Unchanged.** An embedded diff-lane `gate` transcript is identical byte for
  byte to 0.3.0's, including `gate: passed`. Adopters grep it.
- **Brief.** With an empty scope, `brief` says the task lands through findings
  and what a finding must carry, and drops "You are implementing" and "no
  change can land".
- **Report / status.** `status` shows `finding` records with their summary and
  artifact count; a review shows `reviewed_finding=<id>` where it applies;
  `report`'s `decision` column works for finding-bound reviews.
- **Docs.** `docs/overview.md` lists `finding` among record types and the
  findings lane among lanes; `docs/sidecar.md` gains the findings-lane loop for
  a research task — including that a finding needs at least one artifact that
  resolves inside the journal repository, so an external source is pinned by a
  local copy beside its URL rather than referenced alone — and its rough-edges
  section is updated — two of its three frictions are resolved by this task and
  it says so, and the third (`doctor`) stays. ADR-0008 Decisions 5 and 6 each
  gain a one-line pointer to ADR-0009 Decision 4; ADR-0004's schema-3 sentence
  is extended to name schema 4 and the floor-3 rule; ADR-0009's "wave S"
  becomes the public ADRs' term for the projection-and-signing work, with no
  other change to that file. Proposal 005's disposition gains a dated
  "implemented" note pointing at ADR-0009 and this task.
- **Not touched.** The two research tasks in this project's sidecar journal are
  left as they are; closing them is the operator's act after this lands.

## Threat model and boundaries

**A task that promised a diff landing without one.** The lane is admitted by
the contract's empty scope, never by a flag; a declared scope refuses it
naming the scope. Tested.

**Host changes riding under an empty-scope task.** The findings lane examines
no diff, so it must not be a way to merge one — and it is not, because it has
no candidate: the lane is entered only when none is offered. Any candidate,
on any task, runs today's lanes unchanged: journal-only when every changed
path lies under `.agentmarshal/journal/` (`_JOURNAL_PREFIX`), otherwise the
diff lane, where an empty scope refuses every path. The commit carrying the
finding/review/completed records is such a candidate and merges through the
journal-only lane. A test puts a host change on a branch under an empty-scope
task and shows the diff-lane refusal is the same as in 0.3.0. In a sidecar the
records commit is not gated by this tool; that is ADR-0008 Decision 7's
boundary and is not this task's to change.

**A verdict surviving a changed conclusion.** Two guards, both tested: a
review must bind to the *latest* finding (a new finding invalidates an old
approval, as a new commit does), and every locally resolvable artifact is
re-hashed at gate time (an edited document refuses the lane). An unresolvable
ref is *reported* as unverified, never silently treated as verified.

**A findings-lane pass read as a diff-lane pass.** The transcript names what
it did not examine with the reason, in the pattern already used for the
sidecar; the final line is distinct. Tested against the exact strings.

**The independence check is a comparison of declared identities** — the
reviewer's email against the finding's `recorded_by`. This is ADR-0006's
boundary and is stated in the docs next to the lane, not hidden.

Not defects here: that a finding's content might be wrong (the tool does not
judge conclusions); that `review` may decline `--finding` this release; that
the sidecar dogfood tasks are still open when this merges.

## Non-Goals

- The in-toto projection of a finding (wave S). The predicate URI is
  registered; nothing is emitted.
- Any change to the diff lane's checks or wording.
- A `research` value for session `activity`; sessions record cost, not lane.
- `doctor` awareness of placement or of findings.
- Migrating or reinterpreting any existing record.
