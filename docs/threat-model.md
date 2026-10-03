# Threat model

What AgentMarshal protects against, what it does not, and what the
published material leaves open — collected in one place so a reviewer, an
implementer or a finder can tell a security defect from a hardening
suggestion.

This document decides nothing itself. Every statement cites the material
it restates — a decision record by its number and decision or section, a
specification under `openspec/specs/` by its capability and requirement,
or README.md, SECURITY.md or another document by name and section — and
where this text and a source differ, the source wins. A statement marked
*decided, not yet implemented* is design the published decisions fix but
the code does not yet carry out: a promise about direction, not about what
the tool does today. The decision records from ADR-0007 onward mark their
own boundary the same way in their opening lines.

## What the tool protects

**A candidate cannot widen its own scope.** In the embedded placement the
gate reads the contract, the extension manifests, the leak-scan markers
and the lifecycle state at the base from the base side of the history the
candidate belongs to, never from the candidate; the journal's records it
reads from the calling checkout's working tree, where the review attesting
the candidate may still be uncommitted. A candidate therefore cannot widen
its own scope, silence a documents check by rewriting the manifest it
ships with, or be judged against a contract it has not incorporated. The
scope check holds the candidate's diff to `diff ⊆ scope`, computed from
one listing in which a rename contributes its source as a deletion and
its destination as an addition, and matched by the path itself, never by
git's quoted form. In a sidecar the same inputs come from the journal
repository's working tree, pinned to no commit, and the gate advises
rather than decides — the findings lane excepted. (ADR-0014, decision 3,
as amended; ADR-0013, decision 6, as amended; ADR-0003, "Decision";
ADR-0006, "Context"; ADR-0010, decision 2; ADR-0011, "Context"; ADR-0008,
decision 5; scope-enforcement specification, "A candidate's change set
names every path it touches".)

**Records are append-only, collision-checked and fail-closed.** Evidence
records are written exactly once, with exclusive-create semantics; a
candidate introducing a record path that already exists on the target
does not merge, and one that modifies or deletes an evidence record or a
review artifact already in the journal is refused. A task's state is a
projection of its records, never a stored field, so a closed task admits
only what the projection admits — an abandoned task cannot be reopened
through the gate, and a review on a closed task is refused. An
unparseable record, an unknown schema version or an internally
inconsistent one is an error, not a warning, and a reader refuses a
record stamped with a schema it does not know rather than misreading it.
(ADR-0004, decisions 1, 2 and 4; review-evidence specification, "Review
artifacts are evidence and follow the record rule" and "Artifact paths
follow the record collision rule"; record-lifecycle specification, "A
closed task admits only what its projection admits" and "The merge gate
admits what the projection admits after a terminal record"; ADR-0022,
decision 1.)

**The verdict binds the exact commit — or the exact finding.** The gate
binds a review's verdict to the exact commit SHA, so no verdict about an
earlier commit speaks for a new one. On the findings lane the review
binds to a `finding` record's hash-pinned artifacts; the lane verifies
every reference that resolves and refuses on drift, and a finding none of
whose references resolve is refused as a pass over nothing examined.
(README.md, "Trust boundary"; ADR-0011, decision 3; ADR-0009, decisions 1,
2 and 3; findings-review specification, "The reviewer is given the
pinned bytes, and drift refuses the launch".)

**Reviewer independence is enforced — as a declared-identity check.** The
gate requires the recorded reviewer's email to differ from the
candidate's declared authors and committers over the `merge-base..candidate`
range, and refuses the merge otherwise. On the findings lane the reviewer
is compared, on git identities, with the finding's recorder; a recorder
that resolves to no git identity leaves independence unestablished and the
lane refuses — and the review launcher refuses the same cases before it
spends a reviewer run. What this comparison is — and is not — is stated
in the next part. (README.md, "Trust boundary"; docs/overview.md,
"Terminology"; ADR-0009, decision 3; findings-review specification, "The
launcher refuses before it spends a reviewer run".)

**An acceptance is not a bypass.** An acceptance is a record, not a mode:
there is no flag, no environment variable and no configuration that makes
the gate lenient. It is valid only when the latest review of that exact
commit or finding is non-approving, and it must name every blocking
finding that review raised — all of them, and nothing else. It
substitutes for the approving-verdict check and nothing else: scope,
reviewer independence, pipeline attestation, append-only integrity,
record validity and lifecycle consistency apply unchanged. Accepted work
is never displayed as approved, and an acceptance by a writer of the
candidate is permitted and always marked as self-acceptance. (ADR-0007,
decisions 1, 2, 3, 4 and 5; docs/overview.md, "Terminology".)

**Forgeable text cannot forge output.** Values a record or a contract
header carries — finding ids, acceptance fields, artifact references,
header entries — are refused at write time when they contain a character
that could add a line to rendered output or reorder it: the control,
surrogate, line- and paragraph-separator categories and the bidirectional
marks, embeddings, overrides and isolates. A record that carries such a
character anyway — one a later read rule does not reach — is escaped on
display in `status`, `report`, the gate's transcript, the brief and the
reviewer prompt, which covers a record written around the writer with a
lowered schema. The gate escapes every value it did not write itself —
candidate paths, refs, git's error output — so nothing a candidate
controls can add a line to what the gate prints. (record-text-safety
specification, "A record's text may not forge a line or reorder what is
read", "A refused character a record still carries is escaped on display"
and "The gate escapes every value it did not write itself"; ADR-0015,
decision 5.)

**Leak-scan output does not print what it exists to withhold.** A hit
names the file and the identification of what matched — a built-in
signature's id or a configured marker's position in the project's marker
list — never the matched text or the marker's value, and a path that
itself carries a secret is described, not printed. A private marker is
not matched against the project file that declares it. A file that does
not decode is still searched and is named as only partially readable,
never passed over in silence, and a name the scan prints is masked the
same way. The outbox check applies the same masking to every name it
prints. (leak-scan specification, "A leak-scan hit names where it matched
and what matched", "A marker is not matched against the declaration that
configures it" and "A file that does not decode costs its own
readability, not every file's scan"; outbox specification, "`outbox
check` scans what would be sent and refuses by exit status"; ADR-0021,
decision 2 and "Alternatives considered".)

**The symlink refusals the specifications state.** A symlink at an
extension's manifest, at the extension's directory or in any component of
the path is refused as a link, dangling or not; every `bin/` or `lock/`
path a directory-form manifest names must be a regular file reached
through no `..` component and through no symlink; a stage `command` runs
as an argv path inside the extension's own `bin/`, never through a shell
and never through `PATH` lookup — the wrapped product's declared runtime
being the one exception. The process-log sweep never follows a symlink,
and a local-state location that resolves outside the root after `..`
segments or symlinks are resolved is refused. A non-regular file in the
outbox is named as not checked rather than scanned or silently skipped.
The stage runner these manifest rules serve is decided, not yet
implemented; the manifest-level refusals themselves are. (extension-manifest
specification, "An extension is found in the file form or the directory
form", "A path the directory form names exists in the extension's
directory", "A stage entry declares a phase and a command under bin/" and
"A wrapped product is named with its verified version, ecosystem, lock,
runtime and license"; process-log specification, "The log directory is
bounded as a whole" and "Creating a location is contained to the local
state root"; outbox specification, "`outbox check` scans what would be
sent and refuses by exit status"; ADR-0013, decision 13.)

**A sidecar never writes its host.** The host repository carries no
reference to, and no marker of the existence of, any sidecar; a sidecar
lives outside the host's working tree; local state lives in the git
common directory of the repository that holds the journal, leaving the
host's working tree and git directory byte-for-byte what they were. The
step commands and `outbox send` write the journal repository, never the
host; `next` — decided, not yet implemented — is decided to write
nothing, running its conflict check in a temporary object store. (ADR-0008,
decisions 3 and 4; ADR-0014, decision 5; local-state specification, "The
local state root is the journal repository's git common directory" and
"In a sidecar, nothing reaches the host"; process-log specification, "the
step commands write only the journal repository's process log"; outbox
specification, "`outbox send` commits the checked batch"; ADR-0023,
decision 1 — decided, not yet implemented.)

**No extension can change the gate's decision.** An extension is a
declared manifest, not code the tool executes; nothing extension-defined
runs inside the gate — no extension can add, remove or alter a gate
check — and the gate's decision depends on the journal and the diff, not
on third-party code. The core does not run someone else's code in a way
that could permit a merge, and an extension cannot push through what the
gate refused — by construction. The extension stages this rule protects
are decided, not yet implemented — no extension code runs today. Where
they exist, an extension's manifests, modes, isolation, shared switches
and the code of shared extensions are to be taken from the base commit,
so a pull request cannot weaken them for itself (decided, not yet
implemented). (ADR-0010, decisions 4 and 6; ADR-0013, decisions 5 and 6 —
decided, not yet implemented; ADR-0012, decision 7.)

**The gate reads nothing local.** The gate reads neither the process log
nor any of the local state placed outside the journal — importing the
gate does not import the process-log module — and it decides nothing
from a `check` record: what a check observed is a trace, not a proof.
(ADR-0014, decisions 1 and 3; process-log specification, "The gate never
reads the log"; ADR-0017, decision 2.)

**The output claims only what was examined.** The gate's independence
line names what is compared — a declared identity — so an unenforceable
claim does not print as a `PASS`; a sidecar's advisory pass never prints
as the authority's pass, and a sidecar completion states that its checks
passed advisorily — a findings-lane completion states instead that they
passed on the sidecar's own evidence, naming the lane that produced it.
Asked to judge what does not depend on a review, the
gate reports the review-bound checks as not examined, with the reason —
and the mode never weakens a candidate that has been reviewed. The
findings lane prints each check it cannot run as not examined with the
reason, and every extension gets a result line — checked, failed, did
not finish, switched off, not run — with its output in its own frame
(decided, not yet implemented). (ADR-0006, decision 2; ADR-0008,
decisions 5 and 6; gate-lanes specification, "The gate can be asked to
judge what does not depend on a review" and "The mode never weakens a
candidate that has been reviewed"; ADR-0009, decisions 3 and 4; ADR-0013,
decision 7 — decided, not yet implemented.)

## What the tool does not protect against

**Identity is declared, not authenticated.** Actors are declared, never
authenticated: `vendor`, `model`, `email` and `recorded_by` are labels
chosen by whoever ran the command, a `human` reviewer is a
self-declaration, and the independence check is a string comparison that
establishes nothing about a person having read anything. Anyone with
write access to the repository can author a record — a review, an
acceptance, a completion — under any identity they choose, and that is
out of scope: the line is whether the gate's own checks hold, not whether
a record's author is who it says. Signing is on the roadmap, and roles
arrive with it — a permission over unauthenticated identity would be the
appearance of a control. A recorder that is not a declared actor is still
accepted and shown as such, and a rule whose field is absent reads "not
checked" rather than refusing or silently skipping. Self-acceptance and
self-acknowledgement are permitted and marked — visible rather than
impossible; an acknowledgement establishes that someone claiming to be
the named actor recorded it — declared and durable, not proven (the
record type exists; the surfaces that mark acknowledged hits are decided,
not yet implemented). The tool cannot detect a determined false
attribution. (README.md, "Trust boundary"; SECURITY.md; ADR-0006,
decisions 1, 2 and 5 and "Consequences"; ADR-0007, decisions 4 and 6;
ADR-0018, decision 2; ADR-0021, decision 5 — the marking surfaces are
decided, not yet implemented; ADR-0022, decisions 3 and 5.)

**The checkout, the reviewed tree and the pipeline are trusted.** The
gate reads the journal's records from the calling checkout's working tree
and trusts it: the merge-authority wrapper, not the gate, guarantees the
checkout matches the candidate, and an untrusted caller can run the gate
on a mismatched tree. The reviewer works on a metadata-free snapshot that
bounds where the command starts, not what the process may read;
confining reads belongs to the adapter. Pipeline attestation is the
invoker's assertion that a green pipeline ran for the exact commit — the
default mode trusts the SHA the invoker reports — and `init` names the
preconditions the tool cannot establish, including that squash and rebase
merges rewrite a reviewed SHA and that a harness must declare its actor;
`doctor` reports what it can reach and is a report, not a gate.
(ADR-0004, "Consequences"; ADR-0014, decision 3; docs/overview.md,
"Terminology"; ADR-0017, "Context" and decision 2; reviewer-adapter
specification, "The reviewer command's contract is documented where it
is configured"; trust-preconditions specification, "`init` names the
preconditions it cannot verify" and "`doctor` checks the preconditions it
can reach".)

**Local state and the process log do not resist a process running as the
same OS user.** The process log promises no protection against forgery —
a process running as the same user rewrites it whole — no visibility
between machines, and no durability. The local protection the extensions
design describes rests on two things — that a personal extension has no
authority, and that the executor's sandbox keeps managed agents out of
the local-state places — and it does not hold against an agent or a
process running with the user's rights and no sandbox: such a process
rewrites both the extension and the grants file. Signing the local state
from the OS keychain was rejected as complexity without protection, and
running an agent without a sandbox removes the protection outright. (The
extension machinery is decided, not yet implemented.) (ADR-0014,
decisions 2, 8 and 12; ADR-0013, decision 15, "Consequences" and
"Alternatives considered".)

**The leak scan is best-effort and advisory.** It warns and never blocks
a merge; its heuristics miss content, so a hit is not proof of a leak and
a clean run is not proof of safety; it is not authorization to publish,
and it does not run on the findings lane. An acknowledgement, once its
surfaces exist, changes what the standalone command refuses and adds a
mark — it never removes a hit from a surface that shows it, and the scan
stays advisory with or without one. Mandatory block-on-leak enforcement
is roadmap. (ADR-0005, implementation-boundary note and decision 2;
ADR-0021, "Context", decision 3 and "The readers and the advisory follow
from what is already there" — the marking is decided, not yet
implemented; ADR-0009, decision 3; docs/overview.md, "Direction
(roadmap)".)

**Nothing is signed, and no SLSA level is claimed.** Review records carry
no signature; signing and provenance are roadmap. The in-toto Statement
projection is a derived output the current code does not emit, and the
unsigned Statement it describes is schema-valid, not a verifiable
attestation; SLSA Source alignment is adjacency and roadmap, never
asserted as a derived level, and the completeness invariant is normative
intent, not a property a validator enforces. Imported evidence is marked
and is provenance-weaker than live capture. (README.md, "Trust boundary";
ADR-0005, decisions 1, 4 and 5; ADR-0006, decision 5; docs/overview.md,
"Direction (roadmap)".)

**Records written around the tool get checked, not trusted.** The gate
still checks records another tool wrote, and a record a candidate adds is
checked by every current rule; but the journal-only lane verifies shape,
append-only integrity and lifecycle consistency — it does not verify
that a gate pass preceded a completion record, for either binding. A
record written around the writer with a lowered schema is checked by its
own schema's rules — later rules do not reach it — and is escaped on
display rather than refused. A contract edited in a journal transaction
without an amendment record is a change the visibility mechanism cannot
show, and two open tasks may declare overlapping scope and nothing checks
it. (ADR-0009, decision 3; record-schema specification, "A record is
checked by the current rules at write time and by the rules of its own
schema at read time"; ADR-0015, decisions 4 and 5; ADR-0011,
"Consequences"; ADR-0006, decision 4.)

**A sidecar's evidence rests on the sidecar's own governance.** In a
sidecar the gate runs advisory and does not decide a merge — the
findings lane excepted, and that lane decides over the sidecar's own
records without making them tamper-proof. The append-only property of a
sidecar is protected only by the sidecar's own governance, and no
property of the host is attested beyond what its SHAs pin. Sidecar
contract text can change under an approved candidate with no host commit
anywhere — the decision gives the evidence to see it afterwards, not a
gate line — and a hash-pinned reference to private content discloses
that the private evidence exists. (ADR-0008, decisions 3, 5, 6 and 7;
ADR-0009, decision 4; ADR-0011, decision 3.)

**Extensions and the execution environment are outside the core's
protection.** Defects in the harness are out of scope by design, and
provisioning and enforcement of the execution environment stay with the
harness. A manifest's presence records a declaration — the tool does not
verify that `install` or `remove` ran, succeeded or produced the files
the footprint names — and nothing pins an extension's version; a
supplied extension is guaranteed for compatibility with the task cycle at
the pinned version, not for quality or security. Where stages exist the
core is to enforce declared isolation as far as the platform allows,
naming what it cannot enforce, and it restricts only the extension
processes it launches itself — decided, not yet implemented; the local
protection further rests on the executor sandbox the adopter kit's
implementer-launch template is to provide — decided, not yet
implemented. (ADR-0001, "Consequences"; ADR-0002, "Decision"; ADR-0010,
decisions 1 and 6; ADR-0012, decision 3; ADR-0013, decisions 8, 11 and
15 — decided, not yet implemented; ADR-0014, decision 12.)

**Several visible things are declarations or reports, not enforcement.**
A `check` record is a trace of what its observer declares — the gate
decides nothing from it, and nothing downstream re-verifies it; the
`record-check` command that writes one is decided, not yet implemented.
The `changes_required` count reports and decides nothing — it blocks no
merge. Why a run fell back to a later entry in an assignment list is
shown, not verified. A documents check checks the presence of a change,
not its truth. The session outcome vocabulary is documentation, not
code — `outcome` accepts any non-empty string. An `ext` record's body is
opaque to the core — the type is decided, not yet implemented. The
outbox is neither evidence nor journal — not append-only, not
task-scoped and not gated — and the tool transmits nothing and opens no
network for it. And nothing in the tool can tell an honest acceptance
from a convenient one. (ADR-0017, decision 2 and "Consequences";
gate-lanes specification, "The transcript reports the task's
changes_required count"; ADR-0016, decision 4; ADR-0018, decision 3;
ADR-0010, decision 3; ADR-0019, decision 5; ADR-0013, decision 18 —
decided, not yet implemented; ADR-0020, decision 6 and "Alternatives
considered"; ADR-0007, "Consequences".)

## Open questions

Each of these is open: the sources cited pull in different directions or
stop short, and this document does not resolve them.

1. **A completion record with no gate pass behind it.** A completion
   record the task's lifecycle does not allow is a vulnerability by
   SECURITY.md's list, while the journal-only lane does not verify that a
   gate pass preceded a completion record — for either binding — and the
   decision leaves the question for both lanes together and "not decided
   here". The boundary between a lifecycle-valid record and a gate-earned
   one is not drawn. (SECURITY.md; ADR-0009, decision 3.)

2. **Records read from the working tree.** The gate projects the
   journal's records — reviews, acceptances, the lifecycle state — from
   the calling checkout's working tree, where the review attesting the
   candidate may still be uncommitted, and an untrusted caller can run
   the gate on a mismatched tree. Where "bypassing the gate" ends when
   the working tree is itself the untrusted input is not delineated.
   (ADR-0014, decision 3; ADR-0013, decision 6, as amended; ADR-0004,
   "Consequences"; SECURITY.md.)

3. **Pipeline attestation is the invoker's assertion.** The default
   attestation mode trusts the SHA the invoker reports — an assertion
   spoofable by the invoker by design — while "bypassing the gate" is a
   vulnerability by SECURITY.md's list. Whether a false attestation is a
   bypass or a trusted input the boundary assigns to the invoker is not
   stated. (docs/overview.md, "Terminology"; ADR-0017, "Context" and
   decision 2; SECURITY.md.)

4. **Symlinks inside the journal.** Symlink refusal is specified for the
   extension manifest and its `bin/` and `lock/` paths, for the
   process-log sweep, for local-state creation and for non-regular
   entries of the outbox. No published statement covers a symlink inside
   `.agentmarshal/journal/` — at a record or an artifact — or at
   `.agentmarshal/switches.toml`. (extension-manifest specification, "An
   extension is found in the file form or the directory form" and "A path
   the directory form names exists in the extension's directory";
   process-log specification, "The log directory is bounded as a whole"
   and "Creating a location is contained to the local state root";
   outbox specification, "`outbox check` scans what would be sent and
   refuses by exit status".)

5. **Block content the reviewer prompt carries.** A value taken from a
   record or a contract prints escaped where it joins a line, but
   material the tool presents as a block — a contract document inlined
   into a brief or a prompt, a diff, an artifact's embedded content — is
   shown as it stands. Neutralizing the verdict protocol's sentinels is
   specified for finding-artifact content; for a commit review's diff no
   such statement exists, and the commit prompt is pinned byte for byte.
   (record-text-safety specification, "A refused character a record
   still carries is escaped on display"; findings-review specification,
   "Artifact content cannot introduce a verdict" and "The commit path is
   unchanged".)

6. **A sidecar contract that changes under an approved candidate.** A
   review record may name the contract it judged, and in a sidecar the
   contract text can change under an approved candidate with no host
   commit anywhere. Whether the sidecar gate should say anything when an
   approving review's `reviewed_contract` differs from the contract it
   reads — and what the findings lane does with any of it — is left open
   by the decision itself. (ADR-0011, decisions 3 and 4 and "Left open".)

7. **What the scan covers, and what a defeat of it means.** The
   added-content scan reads the `merge-base..candidate` diff's added
   lines; a file that does not decode costs its own readability while
   the rest are still scanned; the gate's line may bound how many hits it
   shows provided it says how many it did not; and the scan stays
   advisory. Whether a candidate crafted to leave the scan reporting
   nothing is a defect or the stated best-effort limit is not classified.
   (ADR-0021, "Context"; leak-scan specification, "A leak-scan hit names
   where it matched and what matched" and "A file that does not decode
   costs its own readability, not every file's scan"; ADR-0005,
   implementation-boundary note.)

8. **A record written around the writer with a lowered schema.** Read
   time checks such a record by the rules of its own schema — a rule
   bound to a later schema does not apply — so what the design promises
   for it is escaping on display, not refusal. Whether anything beyond
   escaping is warranted is unstated. (record-schema specification, "A
   record is checked by the current rules at write time and by the rules
   of its own schema at read time"; ADR-0015, decisions 4 and 5.)

9. **A shared extension switched off without review.** The operational
   lane — decided, not yet implemented — admits a diff touching only
   `.agentmarshal/switches.toml` and the task's own records, requires no
   review, and skips the extensions' `pre-gate` stages; the reason is
   mandatory and `status` and `doctor` show the switch — "easy, but not
   silent". That file is the one exception to the rule that
   configuration is reviewed, and whether its visibility substitutes for
   review is not assessed. (ADR-0013, decisions 16 and 17, header and
   "Consequences" — decided, not yet implemented; ADR-0010, decision 2.)

10. **`next` reads local, forgeable inputs.** `next` — decided, not yet
    implemented — reads the process log for an open step and for an
    extension pause standing without its acceptance, and the plan file;
    the log promises no protection against forgery and no visibility
    between machines, so two machines can print different actions for the
    same task. `next` is not the gate and substitutes for none of its
    checks — `complete` still re-runs the gate — and whether a forged input can
    mislead a driver beyond printing a different action is unstated, as
    is what a consumer may assume of `--json`, which prints the same
    strings unescaped. (ADR-0023, decisions 2 and 6 and "Consequences" —
    decided, not yet implemented; ADR-0014, decision 8.)

## How to classify a finding

**A security defect breaks a promise of the first part** — in agreement
with SECURITY.md's list: a way of bypassing the gate; a candidate the
gate admits although its own documented checks, run on that candidate,
should refuse it — one that changes or removes an evidence record
already in the journal, adds a review, acceptance or completion record
the task's lifecycle does not allow, or makes a verdict count for a
commit it does not name; leak-scan output that prints what it exists to
withhold, such as a matched secret or a private marker's value; or a
command that leaves a journal invalid or unreadable. A statement marked
*decided, not yet implemented* is a promise about the design, so a
finding that shipped code lacks the mechanism reports the roadmap, not a
defect — the defect would be the mechanism, once present, failing its
own rule. (SECURITY.md.)

**A weakness the second or third part covers is a hardening suggestion,
not a vulnerability.** The documented trust boundary is out of scope: a
person with write access authoring a record under any identity they
choose, a mismatched checkout, a forged process log, a leak the
best-effort scan misses — each is stated, and each is reportable as a
hardening suggestion rather than a vulnerability. Where the boundary
truly is not drawn, the third part says so and names the sources.

**Report a vulnerability** only through GitHub private vulnerability
reporting — the **Report a vulnerability** button on the repository's
**Security** tab — never in a public issue. (SECURITY.md, "Reporting a
vulnerability".)
