# ADR-0022: The 0.5.0 record model — one transition

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (a record declares its
schema; a writer stamps the minimum schema a record needs; an unknown schema
fails closed), [ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)
(the `ext` envelope and the manifest's forms — the envelope's schema was left
to this decision), [ADR-0014](ADR-0014-where-things-live.md) (the process log
and where local state lives),
[ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md) (a
new field arrives under the schema that introduces it; this model arrives
under a single record schema) and
[ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md)–[ADR-0021](ADR-0021-an-acknowledged-leak-scan-hit.md)
(the decisions that settled what is recorded and deferred the field names,
record types and schema numbers to this one), and on the dispositions of
[proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md),
[proposal 042](../proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md)
and
[proposal 043](../proposals/043-review-before-integration-makes-every-merge-stale.md).
**It revises the
[record-lifecycle](../../openspec/specs/record-lifecycle/spec.md) and
[gate-lanes](../../openspec/specs/gate-lanes/spec.md) specifications** — a
`check` record is admitted after any terminal record, so the requirement on
what a terminal task admits gains a measurement and the pinned default
transcript's line "(session records accrue post-terminal)" no longer names
every admitted kind — **ADR-0014's decision 9** — a step is still closed by
the record it ends with, with `step end` admitted as an optional addition —
**and the `step` stage form** that proposal 042's disposition gave the step
events: they arrive as process-log events the `step` commands write, not as
an extension invocation stage. The texts of ADR-0014 and proposal 042 are
amended by the documentation-tail task; this ADR names the revisions.

This ADR records a decision. The schemas, fields, record types, commands and
local formats it describes are **not implemented by this document**; they
follow in their own tasks. The present tense below is how a decision is
written, not a claim about shipped behaviour.

## Context

How it works today:

- the highest record schema is 6, which only a `coordination` session
  stamps; 5 is a review carrying `reviewed_contract`; 4 is a `finding`
  record or a record bound to one; every other record stamps 3 — the
  minimum-schema rule of
  [ADR-0004](ADR-0004-journal-data-model.md) and
  [ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)
  (`records.py`);
- a record's file name is `<id>-<type>.json`, where the id is a
  26-character ULID-class identifier and the type is one word of lowercase
  letters — `[a-z]+` (`records.py`);
- the contract header knows schemas 1 and 2; schema 2 introduced three
  fields — `decisions`, `documents`, `extensions` — each refused in a
  schema-1 header (`contracts.py`);
- the extension manifest knows schema 1 only, and lives at a single file,
  `.agentmarshal/extensions/<name>.toml` (`extensions.py`);
- a reader fails closed on a schema it does not know: `read_records` raises
  "record has an unknown or missing schema version", so the `status`
  listing and `report` fail outright on a journal holding such a record,
  `validate` reports a FAIL line for each task that carries one, and the
  gate — which loads the task's records to project its status — refuses a
  candidate whose task does (`records.py`, `status.py`, `report.py`,
  `validate.py`, `gate.py`, `cli.py`);
- `project.json` is read by named keys; a key the reader does not know is
  ignored (`project.py`, `capture.py`, `actors.py`);
- a session's `usage` block is optional and, when present, carries both
  `provider` and `method` (`records.py`).

ADR-0016 through ADR-0021 and the dispositions of proposals 041–043 decided
what is recorded — the contract's hash on `opened` and `amendment`, finding
classes, review chains, advisory dispositions, an agreement record, `check`
and `acknowledgement` records, the `ext` envelope, session times and cost,
the assignment of implementers and reviewers in the contract header — each
deferring names and numbers to a later decision on the record model. This
is that decision.

## Decision

### 1. One transition, and it is immediate

The new fields and record types arrive under one record schema — **7** —
the contract header's new fields under one contract schema — **3** — and
the extension manifest's under one manifest schema — **2**
([ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)). A
writer still stamps the minimum schema a record needs
([ADR-0004](ADR-0004-journal-data-model.md),
[ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)),
**but the transition is immediate anyway**: the contract hash rides on
every `opened` and every `amendment` record, so a task opened on 0.5.0
carries a schema-7 record from its first write.

What a 0.4.x installation does with each, stated honestly:

- **a schema-7 record** — `read_records` raises; the `status` listing and
  `report` fail outright, and `validate` and the gate refuse on every task
  and every pull request carrying such a record — which, under the
  paragraph above, is every new task;
- **a contract header of schema 3** — contract parsing refuses it, so every
  surface that parses the contract refuses with it;
- **a manifest of schema 2, or an extension in directory form** — the
  0.4.x gate reports "named extension manifest unreadable": a refusal only
  where the contract names the extension, silence where it does not;
- **the new `project.json` keys** — ignored outright: a 0.4.x installation
  simply does not apply an agreement requirement.

**The upgrade rule** — for the release notes and the adopter handoff:
every clone and every CI job goes to 0.5.0 before the first 0.5.0 record is
written. A coordinated upgrade, as 0.4.0's was.

The symmetry holds in the other direction: a new reader refuses the
contract-schema-3 fields in a header stamped below 3, the way the schema-2
fields (`decisions`, `documents`, `extensions`) are refused in a schema-1
header today.

### 2. New fields on the existing record types (schema 7)

| Record | Field | Source |
|---|---|---|
| `opened`, `amendment` | `contract` — the sha256 of the contract text the record establishes, in the lowercase hex `reviewed_contract` already uses | ADR-0018 |
| `review` | `previous_review` — the id of the task's previous review, written by the launcher | ADR-0016 |
| `review` | `classes` — `{finding id: class}`; a class outside the project's vocabulary is recorded as `other`, not refused | ADR-0016 |
| `review` | `verification` — `{executed: [{what, result}], read: [strings], not_run: [{what, why}]}`, optional | ADR-0017 |
| `review` | `evidence` — `{finding id: a link, a file:line, or the command that checked the claim with the essential part of its output}`, optional | ADR-0017 |
| `review` | `mode: resolution` and `carried_approval` — the id of the approving review the resolution rests on; a review of the conflict resolution only | proposal 043 |
| `review.reviewer` | `actor` — the id of the declared reviewer actor, for the `distinct-actor` rule; schema 7 permits the key inside the `reviewer` object, which stays closed to anything else | ADR-0018 |
| `completed` | `advisory_dispositions` — `{finding id: {disposition: fixed \| deferred \| rejected, reason, follow_up?}}`; `reason` is required for `deferred` and `rejected` only, and `follow_up` exists on `deferred` only — as ADR-0016 decided | ADR-0016 |
| `acceptance` | `accepted_pause: {extension}` bound by the existing `accepted_commit` — acceptance of an extension pause, with no `findings` required; and `operational: true` with `accepted_commit` — acceptance of an operational CR, which has no review at all | ADR-0013 |
| `session` | `started_at`, `ended_at` — `created_at` stays the write time | ADR-0019 |
| `session` | `commit` — the commit the implementer run produced | ADR-0018 (decision 3) |
| `session` | `model` — the vendor is read from the existing `usage.provider`, no new field | ADR-0018 |
| `session` | `trace` — an external link to the trace, the field ADR-0004 declared; `cli_session` — the CLI session id a resume needs. Two fields, not one | proposal 042 |
| `session` | `report_ready` — the run's report was finished | proposal 041 |
| `session` | `resets_at` — the provider's stated reset time, on a `provider-limit` session | ADR-0019 |
| `session` | `cost` — `{amount, currency, source: reported \| estimated}`, optional | ADR-0019 |
| `session` | `fallback_reason` — why a run moved down the fallback list; optional — shown, never verified | ADR-0018 |

The resolution-only mode is introduced here, with
[proposal 043](../proposals/043-review-before-integration-makes-every-merge-stale.md)
as its source — its disposition had bound the mode to the
finding-lifecycle decision, which carried no field names. Proposal 043's
metric — rounds and reviews caused by integration conflicts — counts the
reviews that carry `mode: resolution`; no mark lands on sessions.

The `prior` field — the status of previous findings against the new round —
is **not** introduced; whether it pays waits on the experiment that
measures it.

### 3. New record types (schema 7)

The names are one word — the record file name pattern takes `[a-z]+` for
the type. Each type joins the predicate-type registry
(`PREDICATE_TYPES`, `attestation.py`) and the state projection
(`status.py`).

| Type | Fields | Admitted after a terminal record |
|---|---|---|
| `check` | `commit`, `name`, `result` (`passed` \| `failed` \| `error` \| `skipped`), `failed_step`, `excerpt` (up to 4 KiB, leak-scanned at write), `run_url` | **yes** — a measurement, admitted after any terminal record, completed or abandoned ([record-lifecycle](../../openspec/specs/record-lifecycle/spec.md), [gate-lanes](../../openspec/specs/gate-lanes/spec.md) — the revision [ADR-0017](ADR-0017-evidence-of-reviews-and-checks.md) announced and this ADR names) |
| `agreement` | `contract` — the hash agreed with | no |
| `acknowledgement` | `commit`, `file`, `signature` **or** `marker` (the marker's number), `reason` | no |
| `ext` | `kind` (`<name>/<kind>@<version>`), `commit` (required — ADR-0013 lists it in the envelope), `payload` (JSON, up to 64 KiB, leak-scanned at write), `payload_sha256` | no — post-gate results go to the process log |

On `check`, `agreement`, `acknowledgement` and `ext` the pair
`recorded_by` + `recorded_by_source` is **required**, as it already is on
`finding` (`records.py`): these records are the claim of who. A recorder
that is not a declared actor is still accepted — the record stands and
`status` shows the recorder as no declared actor — and `distinct-actor`
over an undeclared actor reads "not checked".

On `acknowledgement`: `file` is the path exactly as the scan prints it — a
path carrying a private marker arrives masked — and "acknowledged by the
candidate's author" is derived on display, never stored, the way ADR-0007's
self-acceptance mark is.

### 4. The session outcome vocabulary

Documentation, as before — `outcome` still accepts any non-empty string:
`implemented`, `failed`, `environment-failure` (the environment failed
before the model started — not a round), `provider-limit` (documented
since 0.4.1; carries `resets_at`), `output-limit`, `stalled`,
`safety-limit`, `time-limit` — where `report_ready` decides whether the
next step is a review or a new round.

### 5. The contract header (schema 3)

- `implementers`, `reviewers` — ordered lists of declared actor ids; the
  order is the fallback order
  ([ADR-0018](ADR-0018-governing-the-contract.md));
- `independence` — the rules in force, from a fixed vocabulary:
  - `reviewer-not-writer` — today's check: the reviewer is not an author
    or committer of the candidate's commits;
  - `distinct-actor` — the reviewer is a different declared actor than the
    implementer;
  - `distinct-vendor` — the review's `reviewer.vendor` differs from the
    implementer session's vendor, read from `usage.provider`;
  - `distinct-model` — the review's `reviewer.model` differs from the
    implementer session's `model`.

When the field a rule needs is absent — `usage.provider` is optional and
exists only together with `method` — the line reads **"not checked"**: not
a refusal, and not a silent skip.

### 6. `project.json`

`review.finding_classes` (the finding-class vocabulary of
[ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md)),
`review.changes_required_threshold` (default 3),
`contract.require_agreement` (default false). A 0.4.x installation ignores
all three.

### 7. The local formats — not the journal; the format version lives inside the file

- **The process log** (`.git/agentmarshal/log/`,
  [ADR-0014](ADR-0014-where-things-live.md)): one JSON object per line,
  `{format: 1, at, event, task?, …}` — the key is `event`, not `kind`; one
  file per writer, and a reader tolerates an unfinished last line and
  rotation. The event kinds at the start:
  - `step-started` — `step` (the step id `step start` prints), `activity`
    (the session `--activity` vocabulary), `pid` and `pid_started_at`
    (against pid reuse), `deadline` (required); and, optional, `actor`
    and `run_dir`;
  - `step-ended` — `step`, `outcome` (the vocabulary of section 4);
  - `check-output` — the check's full output (ADR-0017);
  - `provider-export` — the raw provider exports
    ([ADR-0019](ADR-0019-accounting-time-quota-resets-money.md));
  - `review-prose` — the path to the prose file and its sha256 — and
    `review-diagnostics`;
  - `extension-event` — `extension`, `scope` (shared or personal),
    `decision`, `reason`; post-gate results land here carrying a result
    field;
  - `heartbeat` — written by extensions and supplied components only,
    never by the core;
  - `trust-changed`.
- **The step commands:**
  `agentmarshal step start --task … --activity … [--pid …] --deadline …`
  prints the step id; `agentmarshal step end --task … --step <id>
  [--outcome …]` records its close. Both write only events to the log.
  `step end` is an **optional addition** — for a step that ends with no
  record, and to record an outcome; a step is still closed by the record
  it ends with. This revises
  [ADR-0014](ADR-0014-where-things-live.md)'s decision 9 and replaces the
  `step` stage form of
  [proposal 042](../proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md)'s
  disposition. The watchdog and the monitor are a supplied component the
  harness runs — **the core launches no background process**.
- **The plan file** (`.git/agentmarshal/plan.toml`,
  [proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)):
  `format = 1`; the tasks in order, each carrying an optional
  `implementer`, `not_before` and `hold` (a reason). The driver and `next`
  read it; the journal is untouched. It takes a line on ADR-0014's map of
  places.
- **The trust file and the switch files**, where ADR-0014's map already
  places them: `trust.toml` — a name to the directory hash granted, who
  granted it and when; `switches.toml`, shared and personal — a name to
  on/off and the reason.

### 8. Limits on the new fields only

Length limits apply to the **new** fields alone: `excerpt` at 4 KiB,
`payload` at 64 KiB, `reason` in the new record types at 1000 characters.
The existing `reason` fields are untouched — a rule over an existing field
applies under its own schema
([ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)).
Every displayed string the new fields introduce follows the same pair as
the rest: the forgeable-text rule at write time, escaping on display.

## Left open

- The `prior` field — each earlier finding's status against the new round —
  stays out of the model until the experiment measuring it reports.
- The texts this ADR names as revised — the `record-lifecycle` and
  `gate-lanes` requirements, ADR-0014's decision 9, proposal 042's
  disposition — are amended by the tasks that follow; this document is the
  decision, not the edit.

## Consequences

- The cutover is the one 0.4.0 already made adopters practise: every clone
  and CI first, then the first new record. Between the two, a 0.4.x
  installation fails loudly and in named places — `status` and `report`
  outright, `validate` and the gate on every new task and pull request —
  rather than misreading a record it does not know.
- The minimum-schema rule keeps its force — a writer still stamps no more
  than a record needs — yet grants no gradual transition: the contract
  hash on every `opened` and `amendment` makes every new task a schema-7
  journal from its first record, which is exactly the immediacy the
  upgrade rule assumes.
- One document now names what six decisions deferred: the field names,
  the four new record types and their admission rules, the contract and
  manifest schemas, and the local formats. The deferred texts say "a later
  decision on the record model" — this is the text that phrase meant.
- A journal holding `check`, `agreement`, `acknowledgement` or `ext`
  cannot be read by a version that predates them — the note
  [ADR-0007](ADR-0007-operator-acceptance.md) and
  [ADR-0021](ADR-0021-an-acknowledged-leak-scan-hit.md) carried, again.
- An undeclared actor stops being a silent ambiguity: the record is
  accepted and shown for what it is, and the rule that cannot check it
  says "not checked" — the declared-identity boundary of
  [ADR-0006](ADR-0006-actors-and-identity.md) held in the new machinery
  rather than implied away.
- The ephemeral gains defined shapes — step events, heartbeats, check
  output, provider exports, plan, trust, switches — all local, none read
  by the gate, and none costing the core a background process.

## Alternatives considered

**Write the contract hash only under a project setting.** Then the
transition defers to the first new feature a project turns on — but not
every task carries the hash, and two projects' journals stop meaning the
same thing. Refused: one immediate transition over a per-project split.

**A new session field for the vendor.** Refused: `usage.provider` already
declares it; a second field would say the same thing twice and could
disagree with itself. Where it is absent the rule reads "not checked",
which is the honest line for a field that was never promised.

**The local formats in a separate text.** Refused: the writers of the
process log, the plan, the trust and the switch files are decided by the
same model that decides the record fields — splitting them would publish
half a model.

**One `trace` field for both the external trace and the resume handle.**
Refused: a trace link and a CLI session id are different facts — one is a
reference for a person, the other a handle `next` reads to choose `resume`
— and one field serving both would guess at which it holds.

**Deriving the fallback reason from the previous session's outcome.**
Refused: the previous session does not always carry one, so the
derivation would be silent exactly when it matters; the optional
`fallback_reason` keeps the fact visible without pretending to verify it.

**An optional `commit` on `ext`.** Refused:
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md) lists the
commit in the envelope; an extension record bound to no commit could not
say which state of the tree it reports on.

**A `step` invocation stage** — proposal 042's original form, events passed
to extensions as ADR-0013 stages are. Not taken: the lifecycle events are
process-log records the `step` commands write, the watchdog and the
monitor are supplied components that read them, and the core launches no
background process — the same boundary that keeps live state out of the
core.
