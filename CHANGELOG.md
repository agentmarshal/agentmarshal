# Changelog

Notable changes to AgentMarshal. Dates are **PyPI upload dates**, checkable
against <https://pypi.org/project/agentmarshal/#history> — a git tag carries a
local timestamp that can read a day either side of it. The journal under
`.agentmarshal/` carries the per-task evidence behind every entry.

This project describes what it does and not what it intends to do. Where a
capability is partial, the entry says so.

## 0.6.0 — unreleased

The headline is the executing half of
[ADR-0013](docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)'s
extension execution model: wave B ships the shared extension run — local
grants, stage planning and execution, the isolation the platform allows,
base-side switches, a pre-gate pause and its acceptance, and the
operational lane — and adds the personal-in-clone scope beside the shared
one. No record schema, contract-header schema or extension-manifest
schema changes: every record a 0.6.0 writer stamps stays within the
schemas 0.5.0 declared, so a 0.5.0 installation reads a 0.6.0 journal and
0.6.0 reads a 0.5.0 one. What an upgrade asks of a project is in
[UPGRADING.md](UPGRADING.md).

### Shared extensions run their declared stages under local grants (CR-206, CR-209, CR-211)

`agentmarshal extension trust <name>` grants a directory-form shared
extension locally: it hashes every regular file the extension's directory
holds and records the grant — the directory hash, the per-file hashes,
the granter and the time — in the clone's `trust.toml`, writing a
`trust-changed` event to the process log; `extension untrust <name>`
removes the grant, and `extension list` recomputes the hashes and prints
`granted`, `not granted` or `changed after approval: <path> (<kind>)`
for each directory-form shared extension — a manifest in the
single-file form gets no line. `agentmarshal stage run` —
`--phase <pre-gate|post-gate>`, `--task <id>`, `--commit <rev>` and
`--base <ref>` — materializes the base tree's extensions — each
manifest is read at the merge base, and the gate reads a directory-form
manifest at the tree it is declared on, so a candidate cannot change
the extension that runs — and plans their stages. Every stage the plan
names gets one result line — `checked`, `failed (exit <n>)`,
`did not finish (timeout)`, `not run (<reason>)` or
`switched off (<task>, <reason>)` — and every result is written to the
process log as an `extension-event`; the journal holds no stage output.
A command-level refusal — an unknown phase, an invalid task id, a
sidecar journal, an unreadable base extension manifest — prints no
stage line; a stage the plan names that cannot run is `not run` with
the reason. On a workstation a stage runs only when a local grant's
per-file hashes match the stage's own fresh materialization of the
base's directory — an extension changed after its approval is
`not run (changed after approval: <path>)` — while in CI (`CI=true`)
no grant is consulted. A `pre-gate-stop` stage that fails or does not
run pauses the command — `stage run` exits 3 — and a `pre-gate-warn`
failure warns.

### Extension results and declarations are read (CR-212, CR-213, CR-214, CR-216)

`agentmarshal record-ext` — `--task <id>`, `--commit <rev>`,
`--kind '<name>/<kind>@<version>'` and `--payload-file <json>` —
writes an `ext` record for a kind the shared extension's manifest
declares: the payload is leak-scanned and masked, keys included,
canonically serialized and bounded at 64 KiB, and `payload_sha256`
pins the masked form; a kind no shared extension declares, or a
manifest that cannot be read, refuses. `agentmarshal doctor` checks
each shared extension's manifest under an
`extension manifest <name>` check whose detail reads
`<form> form, manifest schema <n>`, and a manifest declaring
`[wraps].runtime` gains an `extension runtime <name>` check that
finds the runtime on `PATH` and compares its version to the declared
minimum; beside the checks, a section prints one
`extension <name>: …` line per shared extension — its form and
manifest schema, declared stages and ext kinds, grant state and
switch. `agentmarshal validate` prints a
`WARN: <task>: ext record <id> kind '<kind>': addressee not found`
line when an `ext` record's kind is declared by no manifest — a
warning, never a refusal.

### A shared extension is switched off at the base, on the operational lane (CR-217, CR-219, CR-220, CR-222)

A shared extension's switch lives in the base's
`.agentmarshal/switches.toml`: a stage of an extension the trusted side
switched off reports `switched off (<task>, <reason>)` and does not
run, a candidate cannot silence its own extensions, and a switches file
that cannot be parsed against the base's extension names blocks the
stages it names with `not run (shared switches file unreadable)`.
`agentmarshal extension switch off <name> --reason <text>` opens an
operational task whose generated contract declares
`scope = [".agentmarshal/switches.toml"]` — the switches file alone —
and writes the `off` entry; it refuses in a sidecar. Such a candidate
takes the gate's operational lane: only `.agentmarshal/switches.toml`
and anything inside the task's own journal subtree — its records and
an amended contract alike — may change, the candidate's switches file
is checked against the base's — every changed entry must name the
task, a dropped entry refuses, and the other top-level keys must stay
identical — and the verdict is
`PASS: operational transaction (operational lane; review not required)`,
with the agreement, review and independence checks not examined;
pre-gate stages do not run on the lane. `status` prints
`switched off: <name> since <task> (<reason>)` for each shared
extension switched off — `switches: unavailable` when the file cannot
be read — and `doctor` lists the same state beside the grant's.

### Isolation is enforced as far as the platform allows (CR-221, CR-223, CR-227)

A stage that does not declare `network = true` runs in a new user and
network namespace on Linux — network access is the manifest's opt-in,
not the default — and every capability the namespace granted is
dropped before `execve`. At pre-gate the candidate the stage receives
is bound read-only over itself — a bind remount keeps the mount's
locked flags, and the stage's working directory is re-entered after the
setup — and the declared provider-secret names are withheld even when
`isolation.env` names them. `writes` beyond the candidate is never a
guarantee: what the platform or the stage's own setup cannot enforce is
named `not enforced` on a `stage run: note:` line for the stage, and
the stage still runs.

### A pre-gate pause can be answered; `complete` runs the stages (CR-215, CR-218, CR-224, CR-225)

`agentmarshal accept --pause <name> --commit <rev>` records an
`accepted_pause` acceptance for an extension's pause, and
`accept --operational --commit <rev>` records an operational
acceptance; each binds a revision resolved in the journal's repository
and consults no review. An `accepted_pause` naming the extension at
the resolved commit stands a `pre-gate-stop` pause down: the result
line keeps the stage's outcome with
`pause accepted by <party> (<reason>)` appended.
`agentmarshal complete` runs the declared pre-gate stages before its
gate check — the same run `stage run` performs — and the post-gate
stages once the `completed` record exists; a post-gate stage cannot
pause, and its outcome informs nothing. A `pre-gate-stop` pause
refuses the completion while the candidate is not merged —
`complete` exits 3 — and `complete --target <branch>` names the
branch the candidate merges into, distinct from `--base`, so that a
wrapper completing after the merge sees the same pause warn rather
than refuse.

### The personal-in-clone scope joins the shared one (CR-233)

An extension manifest placed under the clone's
`.git/agentmarshal/extensions/<name>/` — directory form only — is the
developer's own: it plans beside the shared manifests, needs no grant,
and runs on the workstation only — CI plans and prints nothing
personal. Its command runs directly as a program rather than under the
core's interpreter, its result lines are marked `(personal)`, and its
process log events carry the `personal` scope. A personal manifest
carries no `footprint`, `documents` or `artifacts` — a personal
extension has no write path into the journal through the core, and its
process runs with the developer's rights, so the same-user caveat of
[docs/threat-model.md](docs/threat-model.md) applies — and a shared
extension of the same name wins: the personal stage reports
`not run (a shared extension of this name wins) (personal)`.
`agentmarshal extension disable <name>` writes `state = "off"` to the
clone's switches — `extension enable <name>` clears it — for a
`disabled (personal)` result line, and `--skip-ext <name>` on
`stage run` or `complete` reports
`skipped for this run (personal)`; naming a shared extension to
either refuses. A personal `pre-gate-stop` pause pauses the local run
like a shared one.

### Status and the gate say more (CR-208, CR-210)

The additions 0.5.0's CR-200 through CR-203 began — a session-absent
status, findings the completion consumes, required agreement, named
reviewers and implementers — gain three details. `status` prints
`Reviewed commit <sha7>: implementer session <id>`, naming the
implementer session whose `commit` equals the latest review's — its
actor and outcome on the same line, and a
`(did not end 'implemented')` mark when it ended otherwise.
`status <task> --base <ref>` lists the task's records the base ref does
not hold under `Records absent from <base>`, and the gate warns
`candidate adds opened/amendment records of other tasks` — a warning
only: the record stays valid evidence of the task it names; the
refusal the warning stops short of is an audit fix below.

### A journal transaction stages only its own task (CR-207)

`templates/journal-transaction.sh` stages
`.agentmarshal/journal/tasks/<task-id>/` by literal pathspec — nothing
outside the task's own records enters the commit — lists the working
tree's other journal changes and leaves them alone, and refuses a task
id that is not a CR, a run that is not on the default branch and a call
with nothing to stage. The recipes that once swept the whole journal —
the quickstart's, the sidecar guide's and the outbox README's — now
stage one task's directory.

### The outbox skips files it already sent (CR-228)

`agentmarshal outbox send` maintains a `SENT` manifest inside the outbox,
recording each file it sent by name and digest; `outbox check` and
`outbox send` skip the files a send already reported —
`skipped as sent: <n>` — and `outbox check --index <file>` treats the
`Source:` digests a passed index names the same way. The leak scan still
covers every file `send` stages, sent or not.

### Sessions an exporter did not measure read as unmeasured (CR-229)

A session record carrying zero token counts and no `usage` block is the
record of a session the exporter did not measure: `status` renders the
session line with `tokens=unmeasured`, and `report` carries
`unmeasured=<n>` as the last field of the task line, the Summary line
and each Cost line — on a Cost line the count covers only the
unmeasured sessions that recorded no cost, the sessions the line's
sums left out. The cost sums themselves admit every session: an
unmeasured session that carries a cost still sums, and one carrying
none is counted rather than silently folded into a zero.

### OpenSpec's pin rises to 1.15.0 (CR-231)

The extension manifest that pins the OpenSpec release this repository's
contributor tooling works against —
`.agentmarshal/extensions/openspec.toml`, a schema-1 manifest in the
single-file form — names `version = "1.15.0"`, and the skills it
manages under `.agents/skills/` are regenerated from that release.

### A release asks for its audit before it builds (CR-232)

The release workflow runs a check the project itself keeps —
`.github/scripts/check_release_audit.py`, documented in
CONTRIBUTING.md — before it builds: a `release/audit-<version>.toml`
must name an allowlisted model, an audited commit that is an ancestor of
the tag, and a disposition for every blocking finding — `fixed` against a
task whose last lifecycle record is `completed`, or `deferred` /
`rejected` with a reason — and nothing may have landed since the audit
but the fixes it named, the release notes and the version bump. It is a
gate on this project's release process; the package gains no command.

### Fixes from the release audit (CR-235, CR-236)

The audit filed findings against the gate's journal handling; the two
tasks named here are its fixes that completed before these notes.
Where the CR-210 warning ends, refusal begins: for every other task
the candidate adds records to, the gate projects that task's merged
records — target plus candidate — with the same lifecycle projection
and the same closed-at-base admission rule it applies to the judged
task, and names the task and the projection's reason on its FAIL line
(the audit's reproduction: a candidate for an open task that adds a
reopening to a task abandoned at base is refused). The write-time
text refusal now covers the fields it missed: a `created_at`,
`started_at`, `ended_at` or `resets_at` carrying a character the
forgeable-text rule refuses is refused at write time naming the field
— `fromisoformat` accepts any single character as the date-time
separator, so the refusal lands before the parse — and a review
record's `artifacts` reference is refused by the same write-time
validation; both rules bind past today's schemas, so they reach no
record a read can load — an earlier journal's timestamps parse as
they always did, and an artifact reference it holds stays
`validate`'s to report. `write_record` encodes the record to bytes
before its file is created, so a write that fails at that step — an
encoding or serialization failure — leaves no record file behind; a
failure while writing or closing the created file is not rolled back.
And the reviewer output kept on a refused verdict is now the
reviewer's bytes exactly — the preserved file holds what the
reviewer printed, including bytes that are not valid UTF-8, while
parsing still uses the decoded text.

### What 0.6.0 leaves out

The release task's contract names what this release does not carry; each
item names the decision or proposal that holds it. **Record schema 8 and
the work waiting on it** stay refused (ADR-0022 — the schema table still
ends at 7): the unfinished-candidate refusal proposal 036 holds, the
review-by dates on acceptances and deferrals 0.5.0's notes already
named, and the write side of proposal 044 — optional token counts and
an explicit unmeasured marker — all arrive under a later record schema.
**The user extension scope** — an extension under
`~/.config/agentmarshal/extensions/` (Windows: `%APPDATA%`) shared by all
a developer's repositories — is decided but not implemented: ADR-0013
reserves it for "when an adopter asks", and 0.6.0 ships the shared and
personal-in-clone scopes only. **`next` and the plan file** stay decided
but unshipped while the queue model is under review (ADR-0023, ADR-0022
section 7): there is no `agentmarshal next` and nothing reads
`plan.toml`. **The watchdog and the monitor** (proposal 042 — supplied
components the harness runs; the core launches no background process) and
**the merge slot with the resolution-mode review** (proposal 043 —
`mode: resolution` and `carried_approval` are not fields this release's
record model carries) are held by the same review of the queue model.

Documentation-only and process tasks: CR-205, CR-226, CR-230.

## 0.5.0 — 2026-10-23

The headline is the record model of ADR-0022: one transition carries record
schema 7, contract-header schema 3 and extension-manifest schema 2, together
with the record types, fields, commands and checks that write and read them —
the decisions of ADR-0016 through ADR-0021 become commands, records and
checks, apart from the pieces the last section names, and the reading half of
ADR-0013 lands. A task opened on 0.5.0 carries a schema-7 record from its
first write — the `opened` record pins the contract's hash — so the
transition is immediate, not opt-in, and a 0.4.x installation cannot read it.
**Every clone and every CI job moves to 0.5.0 before the first 0.5.0 record
is written:** [UPGRADING.md](UPGRADING.md) has the rule and the procedure.

### Records are read by their own schema's rules (CR-145, CR-151, CR-154)

Every rule record validation makes now names the schema it applies from, in
one table — a record is read by the rules of the schema it declares and
written by the current ones, and a writer stamps the minimum schema a record
needs from the same table. Record schema 7 is known, the record types come
from one registry, and schema 8 is refused. `project.json` gains
`review.finding_classes` (the vocabulary finding classes are checked
against), `review.changes_required_threshold` (default 3) and
`contract.require_agreement` (default false); `doctor` names a malformed
value rather than failing or guessing.

### The contract is pinned and can name who may work on it (CR-147, CR-163, CR-171, CR-177, CR-180, CR-182, CR-186, CR-191, CR-200, CR-202, CR-203)

An `opened` or `amendment` record written on 0.5.0 carries the sha256 of the
contract text it establishes — the record names the exact contract text by
its hash, and `status` and the gate compare against it: `open` and `amend`
pin it, `migrate` pins each contract it writes, `open --contract-file` opens
a task from a contract already written, `status` says when a contract has
drifted from its last pin, and the gate holds an agreement the project
requires to the hash of the contract it judges. Contract
header schema 3 declares `implementers` and `reviewers` — ordered lists of
actor ids, in fallback order — and the `independence` rules in
force: `reviewer-not-writer` (the existing check), `distinct-actor`,
`distinct-vendor` and `distinct-model`. The gate judges each declared rule
against the implementer sessions whose `commit` falls in the candidate's
range, checks the latest review's `reviewer.actor` against the declared
`reviewers` and the in-range implementer sessions against `implementers`,
and says `not checked` where a rule's field is absent. An `agreement`
record records an actor's agreement with the contract at a stated hash —
any recorder is accepted, and `status` shows one that is not a declared
actor. `agentmarshal agree` writes it for the contract's current text,
`status` shows it — including that a task holds none, or one for an earlier
contract text — and when
`contract.require_agreement` is set the gate refuses a candidate whose task
holds no agreement with the contract it judges against. `review` and
`submit-review` take `--actor` to record the reviewer's declared actor.
`status` shows the declared assignment and the rules in force beside what
actually ran, and `none` on the ran side when nothing did.

### Review findings have a lifecycle (CR-168, CR-174, CR-175, CR-185, CR-192, CR-194, CR-201)

A review the launcher writes links the task's previous review, so a task's
reviews form a chain — `submit-review` writes no link — and a verdict may
carry `classes`: one class per finding id from the project's vocabulary,
with a class outside it recorded as `other` and a warning, never a refused
verdict. `complete` takes a recorded disposition for each advisory finding
of the review the gate passed on — `fixed`, `deferred` with a reason and an
optional follow-up task, or `rejected` with a reason — kept in the
`completed` record's `advisory_dispositions`, and refuses before writing
`completed` when one is missing, so an approval is no longer a
silence about known defects; it reads the findings needing a disposition
from the review the gate's own report names, so a review appended after the
gate ran cannot change what is required. The gate's output and `status`
carry the task's count of `changes_required` verdicts, flagged at the
project's threshold — it decides nothing — and `status` lists the
deferrals still open.

### A check outcome and an acknowledged hit are evidence (CR-167, CR-170, CR-178, CR-183, CR-187, CR-189, CR-190, CR-193, CR-195, CR-197)

A `check` record records what a pipeline check found on a commit — the
observer's declaration, not proof; the gate decides nothing from it. It is
admitted after any terminal record, a measurement on a par with `session`.
`record-check` writes it, keeps the check's full output under the clone's
local state announced by a `check-output` event, and carries a masked
excerpt passed through the leak scan before writing. A review's verdict may
carry `verification` — what the reviewer executed, read and could not run —
and `evidence` for its findings, and the reviewer's prompt asks for both
and for each criterion's place in the diff; a
finding about an external fact the reviewer could not check lands as
advisory. An `acknowledgement` is a recorded statement that an operator
verified a reported leak-scan hit, bound to the commit, the file as the scan
prints it and the hit's identification — a new commit or a renumbered marker
list fails visible. `agentmarshal acknowledge` writes it only against a hit the scan
reports. The hit stays printed, marked with who acknowledged and why: on
`leak-scan`, which now exits 1 only on a hit nobody acknowledged; on
`status`; and on the gate's advisory line within its existing bound.
`brief` names the task's last failing check — and says when a later run of
the same name passed, so a fix round is not sent after a failure already
fixed.

### Sessions record time, resets and money (CR-160, CR-166, CR-176, CR-188, CR-196, CR-199)

A session may carry `started_at`/`ended_at` — `created_at` stays the write
time — `resets_at` on a `provider-limit` session, a `cost` of
`{amount, currency, source}`, and the fields the loop readers need:
`commit`, `model`, `trace`, `cli_session`, `report_ready` and
`fallback_reason`. `record-session` writes them all through new flags, and
`--if-missing` makes a repeat write under the same
`task + role + actor + activity` a no-op, so recording cost after
completion is safe to repeat. `report` shows a task's lead time and its
phases — opened, first implementer start, first review, approval,
completion — and the review rounds, `unknown` where a record cannot say;
sums cost per currency and converts nothing; counts the candidates a
`check` record marked `failed` or `error`; and with `--findings` lists the
finding classes across tasks with counts and the deferred advisories still
open.

### The extension manifest's new schema is read; nothing executes (CR-152, CR-158, CR-173, CR-179)

Manifest schema 2 is parsed — stages, dependencies, a wrapped product,
record kinds and isolation — and an extension may live in a directory
(`<name>/manifest.toml` with `bin/` and `lock/`), found beside the
single-file form by the readers that work from a working tree: `brief`,
`review` and the sidecar gate. The `ext` record type exists — a declared
kind, the commit, an opaque payload and its hash — and the `acceptance`
record admits `accepted_pause` and `operational` forms which `status`
already prints and no command writes — readers keep "acceptance over
findings" to the acceptances that carry findings.

### Local state has one home, and the process log is a format (CR-148, CR-153, CR-157, CR-162, CR-165, CR-169)

The clone's local state resolves to one place — the git common directory of
the repository the journal lives in, shared by all worktrees — and the
process log under it is one JSON event per line, one file per writer, read
tolerating a torn last line and rotation. `step start` and `step end` write
a step's events, its deadline included; `status` marks an open step past
its deadline — on the task list and the task view, naming this machine's
process log as the source — and `doctor` reports overdue steps across
tasks. `status` and `doctor` print where the journal, the process log and
the local state actually are, and `doctor`'s git check names the minimum
version local state needs. At capture level `hash` a review's prose and
diagnostics are kept under the local state and announced by
`review-prose`/`review-diagnostics` events instead of sitting in temporary
files.

### The outbox is a command group (CR-150, CR-156)

`agentmarshal outbox new` scaffolds a finding draft in
`.agentmarshal/upstream/` carrying the five fields of the finding form;
`outbox check` names what each draft lacks and runs the merge boundary's
leak scan over what a batch would carry; `outbox send` runs the check and
commits the outbox as one batch — it transmits nothing and opens no
network; `outbox status` reports which drafts an upstream index file
claims.

### The surfaces escape what a record could forge (CR-155, CR-161, CR-164)

`status`, `report`, the gate's transcript, the brief and the reviewer prompt
escape on display the characters the forgeable-text rule refuses at write —
a record written around the tool cannot make its text forge a line or
reorder what is read — and the gate escapes candidate paths and the values
in its error messages the same way, so a file name cannot forge a line of
the transcript.

### Robustness and smaller corrections (CR-121, CR-127, CR-129, CR-149, CR-184)

One file of bytes that do not decode no longer switches the leak scan off
for every other file, and no longer ends `review` in a traceback: the scan
works per file and names what it could not read, and the diff reaches the
reviewer per file with the undecodable one named. `status` renders each new
record type on a line of its own — `check`, `agreement`, `acknowledgement`,
`ext` — naming the recorder and marking one that is not a declared actor,
and states the task's agreement state on a line of its own; the per-task
view lives in a module with one renderer per record type. The journal rule
the brief prints now says what the gate holds — nothing under
`.agentmarshal/journal/` is the implementer's to edit, and another file
under `.agentmarshal/` may change only when the scope names it — and each
rule sits under a heading that says truthfully whether the gate checks it.

### What 0.5.0 leaves out

The operator decided on 2026-10-23 what this release does not carry; each
item names the decision that holds it. **Executing extensions** — the
stages, the isolation enforcement, the local trust, the switches, an
extension's pause and its acceptance, and the operational lane — is not
shipped (ADR-0013; what this release reads is said above: manifest schema 2
and the directory form are read since CR-152 and CR-158, and the `ext`
record exists since CR-179). **`next` and the plan file** stay decided but
unshipped while the queue model is under review (ADR-0023, ADR-0022 section
7): there is no `agentmarshal next` and nothing reads `plan.toml`. **The
watchdog and the monitor** (proposal 042 — supplied components the harness
runs; the core launches no background process, and this package ships
neither) and **the merge slot with the resolution-mode review** (proposal
043 — `mode: resolution` and `carried_approval` are not fields this
release's record model carries) are held by the same review of the queue
model. **The unfinished-candidate work of proposal 036** — the refusal of
a candidate whose producing session did not end `implemented`, and the
explicit override that is the operator's way through — **and the review-by
dates** on acceptances and deferrals arrive after 0.5.0 under a later
record schema, which will need another coordinated upgrade. **Raw provider
exports to the process log** stay a named event kind in the decided format
(ADR-0019 decision 7, ADR-0022 section 7) — nothing writes a
`provider-export` event.

Documentation-only and process tasks: CR-116, CR-117, CR-118, CR-119,
CR-120, CR-122, CR-123, CR-124, CR-125, CR-126, CR-128, CR-130, CR-131,
CR-132, CR-133, CR-134, CR-135, CR-136, CR-137, CR-138, CR-139, CR-140,
CR-141, CR-142, CR-143, CR-144, CR-146, CR-159, CR-172, CR-181, CR-198.

## 0.4.1 — 2026-09-24

A patch release for one defect an adopter hit on 0.4.0, plus the documentation
and release machinery that landed with it.

### `validate` reads a journal 0.4.0 refused (CR-114)

0.4.0 refused a finding id, an acceptance field, a finding summary, an artifact
reference or a contract header entry containing any character Python's
`str.isprintable()` calls unprintable. That test is false for every space
separator but a plain space, so a journal an earlier release had written could
be refused for a narrow no-break space inside a finding id — and the records of
a closed task cannot be repaired. The rule now names what it refuses: Unicode
categories `Cc`, `Cs`, `Zl`, `Zp` and the bidirectional marks, embeddings,
overrides and isolates. One predicate decides it for records, contract headers
and the artifact reference `validate` checks, so the three cannot drift. **If
0.4.0's `validate` refused a record your earlier release accepted, this release
reads it again** — see [UPGRADING.md](UPGRADING.md). Records written on 0.4.0
are unaffected: where the rule refused a write, nothing was written.

### The default branch says it is not a release (CR-112)

Between releases the version carries a `.dev0` suffix, so a build from the
default branch no longer reports the same version as the published release;
CONTRIBUTING states the rule, and the release workflow refuses to publish a
development or local version.

### Token counts are not what a provider charges (CR-113)

Proposal 024 is published with its disposition: a session the provider refused
to continue is recorded with the outcome `provider-limit`, a documented value
that the tool neither checks nor counts, and the quickstart and README no longer
present token counts as what a task cost. The reset time a provider states in
its refusal still has no field: it waits for the same rework of accounting that
proposal 018's cost field waits for.

## 0.4.0 — 2026-09-18

The headline is that work which is not a source diff can now be recorded and
reviewed as evidence, while the ordinary diff lane has gained more explicit
inputs and checks. The release also closes several paths where the tool's
writer, gate, or diagnostics disagreed with the evidence model.

Three record schemas are new (CR-086, CR-096, CR-106), and 0.3.0 cannot read a
journal containing any of them: schema 4 for a finding and the records bound to
one, schema 5 for a review carrying the hash of its contract — every review
`agentmarshal review` records — and schema 6 for a coordination session. Read
[UPGRADING.md](UPGRADING.md) before any of them is written to a shared journal.

### Findings land as evidence, not a diff (CR-085, CR-086, CR-101)

ADR-0009 defines the findings lane. An empty-scope research task can record a
hash-pinned `finding`, review and accept it by finding rather than commit, and
gate and complete it with `--findings`; a task with declared scope remains in
the diff lane. `agentmarshal review --reviewed-finding` launches the configured
reviewer on locally verifiable artifacts and refuses the launch if their bytes
drift from the recorded hashes. Artifacts that cannot resolve locally are
reported as not verified; a finding with none that can be verified is refused.

### Process tools have a declared footprint (CR-087, CR-088, CR-089, CR-090)

Contract-header schema 2 adds declared `decisions`, `documents`, and
`extensions`. Briefs and reviewer prompts carry that named material; the gate
reads the base-side manifest to add an extension's footprint to effective scope,
require named documents to be touched, and check a removed manifest's former
footprint. It executes no manifest command. OpenSpec 1.12.0 is the first
declared extension in this repository, with its git-visible footprint and the
machine-local files it does not commit recorded in its manifest.

### Review evidence names both prose and contract (CR-091, CR-092, CR-095, CR-096, CR-111)

The capture policy's `reviews` class decides what happens to a review's prose.
By default (`hash`) it stays out of the journal: the private store that level
names is not built, so `agentmarshal review` keeps the reviewer's standard
output in a local temporary file and names it. With
`capture.overrides.reviews = "commit"` the output is written and pinned as a
journal artifact, and `submit-review --prose FILE` attaches human prose the
same way; at any other level `--prose` is refused. Only the `reviews` class is
read; the `economics` and `sessions` classes are not. Pinned artifacts are validated
under the same collision and append-only rules as records, and a foreseeable
refusal leaves no orphan artifact. Briefs and review prompts show that a
contract was amended, when, and why, and reviews record the hash of the contract
text they judged.

### The gate reads one candidate listing and can state its limits (CR-093, CR-099, CR-103, CR-105)

Every path-sensitive gate check reads one listing in which a rename has both
its deletion and addition. `--without-review` evaluates the checks independent
of review and marks the two review-bound checks as not examined when no review
exists; it never relaxes a review record that does exist. A reopening of a
completed task now passes the gate's additive-record rule. The gate's leak-scan line
shows at most twenty hits and counts the rest; the standalone command prints
every hit. The shipped GitHub workflow uses the
review-free mode rather than tolerating a check that cannot carry its own review.
That is partial coverage: on GitHub, nothing shipped enforces the
approved-independent-review requirement, because the required check runs
before the review exists (see `docs/github-enforcement.md`).

### Reviewer setup reports its actual preconditions (CR-097, CR-098)

The reviewer-command contract, rejected placeholder, and a no-recording
`review --dry-run` exercise are documented. `agentmarshal init` prints the
preconditions the tool cannot verify — provider merge settings, the agent's
declared actor, the reviewer command, a CI step that runs `validate` — with what
skipping each costs. `agentmarshal doctor` checks the last three and reports an
unmet one as a `TODO` line, never printing the reviewer command's value; an unmet
precondition does not change its exit status, and its summary line counts the
preconditions left instead of claiming that every check passed.

### Writers preserve journal readability (CR-102)

Commands that add records to an existing task now ask the lifecycle projection
whether it admits the record. A write that would make the projection refuse the
task is rejected instead of leaving an invalid append-only journal; sessions
and a permitted reopening retain their projection-defined exceptions.

### Coordination is a recorded session activity (CR-106)

`record-session` accepts `coordination` beside implementation, review, and
other. Only a coordination session uses record schema 6; the other activities
retain their prior schema.

### Adopter findings made diagnostics actionable (CR-094, CR-100)

Ten sanitized adopter findings and their dispositions are published with a way
to follow each accepted item. A leak-scan hit now identifies the file and a
built-in signature or configured marker position without printing the secret;
the scan does not report a marker where it occurs in the configuration that
declares it, and reports every occurrence anywhere else. A reviewer command's
diagnostics on a successful run are kept outside the journal with their path
named, and the generated upstream outbox says it is not evidence.

### Documentation and reporting are easier to enter (CR-084, CR-107, CR-108)

The documentation was reconciled with the released tool and its workflow. New
contributors can find the security-reporting channel, structured finding and
gate-refusal forms, the pull-request requirements, and a documentation map.

### Internal consolidation (CR-104)

The review launcher paths share their tail and identity resolution has one
home; this changes no command behaviour.

## 0.3.0 — 2026-09-01

The headline is that a journal no longer has to live inside the repository it
records evidence about. Everything else in this release follows from making that
honest: an arrangement that cannot enforce anything must not read as if it does.

### A journal can live in a repository of its own

`agentmarshal init --host PATH` creates a **sidecar** journal: the same journal
structure, the same records, the same commands, in a repository of its own that
names one host repository. The host is read and never written — not its working
tree, not its Git metadata. `init` refuses the two arrangements that would break
that: a journal inside the host's working tree, and a journal that is a linked
worktree of the host, whose commits would land in the host's own object database.

This exists for two situations the embedded placement cannot serve: evidence that
must stay private while the project is public, and a repository you work in but
cannot install anything into.

**The placement is experimental**, and two limits are part of the design rather
than gaps to be closed later:

- **A sidecar gate decides no merge.** It computes every check it can — scope,
  the latest review of the exact commit, reviewer independence, pipeline
  attestation, its own append-only integrity — and says on every run that its
  result is advisory. The merge belongs to the host's process, which a sidecar
  operator does not control. An advisory pass never prints the wording an
  embedded pass prints.
- **A sidecar contract is not pinned to a base commit.** Embedded, the gate reads
  the contract from the base side of the same history as the candidate, so a
  change cannot widen its own scope. A sidecar's contract is not in the host's
  history at all, so it is read from the sidecar working tree, and the gate's
  transcript says so on the scope line. Scope discipline there rests on the
  sidecar's own history.

The surfaces that present evidence say which regime produced it: `status` and
`report` print the placement on stderr, leaving their machine-readable stdout
unchanged, and the gate and `complete` transcripts say it in words.

`open`, `gate`, `complete`, `review`, `prune` and `leak-scan` resolve the host
and the journal as two separate roots. `validate` is the exception, and not an
oversight: it checks the journal it is run in, and a sidecar's host has no
journal to check. `prune --delete` is refused in a sidecar, because deleting
branches and worktrees would write to the host.

The design and its boundaries are
[ADR-0008](docs/adr/ADR-0008-journal-placements.md); the second
install-and-operate path is [docs/sidecar.md](docs/sidecar.md).

### A session record is accepted after a task closes

`record-session` refused a task that was not open. A task's cost is known when it
ends, so that guard made the one moment worth recording the one moment refused —
and this repository ran forty-eight tasks with no live session record before the
guard was found. The gate has always had a measurements-only lane for exactly
this: a session record changes no state, so accepting one cannot revive or alter
a finished task.

Nothing in the record format changed. What changed is when the tool accepts one.

### The package says where it comes from

`pyproject.toml` declares `[project.urls]`, so the source repository is
discoverable from the package and from the index rather than only from
documentation. It was missing entirely through 0.2.0.

It is metadata and nothing more: it changes no behaviour, it does not establish
that a given build came from that repository, and it cannot be backfilled into
0.2.0 — the metadata of a published release is immutable.

### Compatibility

**No record-format change.** The record schema is 3, as in 0.2.0, so every
**record** either release writes is read by the other. That is a statement about
records, not about the tool as a whole — the paragraph below is the part it does
not cover.

One arrangement does not travel backwards: a **sidecar journal requires 0.3.0 on
every checkout that reads it**. A 0.2.0 install does not know the `placement` and
`host` keys. It reads the records correctly — the format is the same — but it
gates the journal repository against itself, classifies the candidate as a
journal-only transaction because everything in that repository is under
`.agentmarshal/`, waives the review requirement that follows from that, and
prints `gate: passed`. Verified against the published 0.2.0. Embedded journals
are unaffected; [UPGRADING.md](UPGRADING.md) has the procedure and the
transcript.

## 0.2.0 — 2026-09-01

The headline is that the operator, not the reviewer, now owns the acceptance
decision — and that a task's lifecycle has a way back. The per-task evidence for
everything below is in the journal.

### Before you upgrade

**A journal written by 0.2.0 cannot be read by 0.1.0.** Records carry fields
and types 0.1.0 does not know, and it refuses records it does not understand —
by design, because a record we cannot validate is not evidence. `validate`,
`status` and the gate all fail closed on the first such record.

The break is one-directional: **0.2.0 reads everything 0.1.0 wrote**, so no
journal needs migrating and nothing is rewritten. Records keep the schema they
were written at.

Everything that runs AgentMarshal against a shared journal must therefore be
upgraded together, before any of them writes a record.
**[UPGRADING.md](UPGRADING.md)** has the procedure and what it means for each
installation method — in particular for an unpinned `pip install`, which moves
on its own schedule and breaks the coordination this requires.

A version mismatch now reports `record has an unknown or missing schema
version` rather than naming an unrecognised field, so the failure says what it
is.

### The operator can accept work over findings

The gate passed an implementation candidate only on an `approved` verdict — the
journal-only lane for openings and completions has never required review — which
meant the acceptance decision belonged to the reviewer while the operator
carried the accountability. (The gate decides; the provider performs the merge.) When review does not converge — remarks changing from round to
round while the verdict stays `changes_required` — the only exits were to
abandon the task or to keep re-running until a verdict happened to approve.

- **`agentmarshal accept`** records that a named party accepted a specific
  commit over specific findings, with a reason.
- It requires the **latest review of that commit to be non-approving**, and
  names exactly the blocking findings that review raised. Review is not
  optional; agreeing with the reviewer is.
- The gate accepts it in place of an approving verdict — **that check and no
  other**. Scope, reviewer independence, pipeline attestation and append-only
  integrity are unchanged.
- An accepted task never reads as an approved one. The gate says
  `accepted over findings … by …; not an approving review`, `status` says it in
  the task summary, and `report` marks the task `decision=accepted-over-findings`.
- Accepting your own work is permitted, and `status` labels it `self-accepted`
  — in the task summary and in the record trail. Where the accepted commit is
  not readable in the current checkout the label cannot be derived, and `status`
  says that rather than falling silent. `report` distinguishes an accepted task
  from an approved one but does not carry the self-acceptance label.

The reasoning, including what an acceptance does *not* establish, is in
[ADR-0007](docs/adr/ADR-0007-operator-acceptance.md).

### The lifecycle has repairs

- **`agentmarshal amend`** records the claim that a task's contract was
  repaired, with the reason. Like every identity and provenance field in this
  project, it is a declaration: nothing detects an unrecorded edit. Previously a defective contract could only be escaped by abandoning
  the task, which left the journal blaming the work for a defect in the
  specification.
- **`agentmarshal reopen`** returns a completed task to `open` with a reason.
  Nothing is rewritten — the completion stays in the trail and the history reads
  as the cycle it was. An abandoned task is not reopenable.

### Contracts reach the implementer

- **`agentmarshal brief`** prints what the journal knows about a task — the
  scope, the acceptance criteria, the rules the tool enforces, and the contract
  body verbatim — to stdout, to be piped into whatever agent does the work. It
  does not know your project's own commands; add those yourself.
  AgentMarshal bundles no implementer and takes no position on which one you use.
- `open` warns when a scope entry names nothing on disk, names a directory
  without its trailing slash, or when a task declares **no scope at all** —
  which forbids every path rather than none.

### Reviews keep their reasoning

- The review prompt names the permitted verdicts, describes `advisory_findings`,
  and asks the reviewer to state each finding's claim in one line of prose.
- The reviewer's raw output is kept when a verdict is refused **or** when a
  recorded verdict names a finding, and the path is reported on stderr. Keeping
  it is **best-effort**: if the file cannot be written the review is still
  recorded, because the record is the evidence and the prose is not. And what is
  kept is what the reviewer wrote — one that emits an id with no prose leaves a
  file with no prose in it.
- A verdict carrying an unsupported field is refused with that field named.

### Records say who wrote them

- Records written by this version carry `recorded_by` and `recorded_by_source`,
  derived from `AGENTMARSHAL_ACTOR` or the invoking checkout's git identity,
  optionally mapped through an `actors` table in `project.json`. Where no
  identity can be determined at all, both fields are **omitted rather than
  guessed**; records written before this release do not carry them.
- This is a **declaration, not authentication** — like `vendor` and `email`. It
  makes the honest case expressible and a false attribution require a second,
  explicit lie. See [ADR-0006](docs/adr/ADR-0006-actors-and-identity.md).
- An agent running the rails should declare itself; the reasoning is in the
  [harness guide](docs/harness-setup.md).

### Economics say where the numbers came from

- A session record may carry `usage.provider` and `usage.method`, where `method`
  is `reported` (the provider stated these counts) or `measured` (they were
  reassembled afterwards, for example from logs).
- `report` carries the distinction through as
  `usage=reported|measured|unrecorded|mixed`, appended after the existing
  fields so a caller splitting on tabs is unaffected.

### Housekeeping

- **`agentmarshal prune`** reports, and with `--delete` removes, the local
  branches and worktrees of tasks the journal says are done. A branch must be
  merged and a worktree must be clean; neither the main worktree nor the one you
  are standing in is ever eligible; deletion never forces, so git's own refusal
  is preserved and reported. No remote is contacted in either mode.
- Renamed from `prune-branches`, which was never released.

### Leak scanning

- **`agentmarshal leak-scan`** scans a candidate diff's **added** content for
  secrets and configured private markers, and the merge path warns on what it
  finds.
- **Advisory and best-effort by design** (ADR-0005): no pattern list can
  enumerate every secret, so a clean scan is never authorization to publish.
  Making it blocking is not in this release.

### Robustness

- `init` reads back the project file it wrote, and `open` reads back the
  contract and the record it wrote; either fails with the path and the
  underlying error instead of reporting success on something nobody can read.
  Reported by an adopter on Windows, where a task directory inherited a
  sandbox's ownership. The outbox README is scaffolded best-effort and is not
  part of that check — a project that could not write it is still initialized,
  and `init` says so.
- `find_git_root` refuses a repository path git reports as non-UTF-8 through the
  project error type instead of raising a decode error out of a function
  contracted to return a path.
- `init` creates `.agentmarshal/upstream/` with a README stating the convention
  for sending findings upstream, and never overwrites one you wrote.

### Documentation

- `CONTRIBUTING.md`, a [quickstart](docs/quickstart.md) and an
  [overview](docs/overview.md) with an explicit implemented-vs-roadmap boundary.
- [`docs/proposals/`](docs/proposals/) — the first adopter batch, digested with
  a stated disposition for every proposal, including the one we declined.
- ADR-0006 (actors and identity) and ADR-0007 (operator acceptance).
- A published [incident record](docs/incidents/) of a warning that grew into a
  path taxonomy over five review rounds, and what it cost.

### Journal format

- Records written by this version carry `schema = 3`. Schemas 1 and 2 keep
  validating.
- New record types: `amendment`, `acceptance`, `reopened`.
- Fields added: `recorded_by`, `recorded_by_source` (any record, when an
  identity is resolvable); `usage` (session records, optional).

## 0.1.0 — 2026-07-30

First public release. The governed loop end to end: contracts with declared
scope, append-only SHA-bound records, state as a projection, and a
provider-agnostic gate that decides fail-closed.

An implementation candidate passes only when scope, an independent review,
pipeline attestation and journal integrity all hold. A journal-only transaction
— an opening or a completion — takes a deterministic lane and needs no review,
since it carries no work to review.
