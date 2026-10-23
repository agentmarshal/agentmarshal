# gate-operational-lane — Design

## Context

ADR-0013 decision 17 defines the operational lane: a candidate whose
diff touches only `.agentmarshal/switches.toml` and its own task's
records requires no review, and an extension's `pre-gate` stages do not
run for the candidate that switches it off. CR-217 built the parts the
lane stands on — the `switches.toml` file and its parser
(`parse_switches` over the shared extension names declared at the
base), the `Switch` entries carrying `state`, `task` and `reason`, and
the stage runner's pre-gate phase — but the lane itself was left for
this change. The threat model records it: ".agentmarshal/switches.toml
and the task's own records, requires no review" — the one exception to
the rule that configuration is reviewed.

## Goals

- One shared decision of what an operational candidate is, used by both
  the gate and `stage run --phase pre-gate`.
- A transcript that says what the lane did: one PASS line for the
  transaction, the switches checks, and NOT EXAMINED for every check
  that exists to serve a review the lane requires none of.
- Fail-closed refusal where it matters: a file the parser refuses, an
  entry naming another task, an entry naming no shared extension the
  base declares, an entry the base held and the candidate drops — each
  refuses naming the file and the entry. A base file the read or the
  parse refuses keeps the lane itself closed: the change needs a
  review rather than being judged against a guessed base.
- Every other lane's transcript byte for byte.

## Non-Goals

- `extension switch off` — the command that opens an operational task
  and writes the entry is CR-220's work; this lane only judges the diff
  such a task produces.
- Reading `accept --operational` — nothing here consumes acceptance
  records; the lane's qualification is a property of the diff and the
  contract alone.
- A sidecar operational lane. ADR-0008 keeps host evidence out of the
  sidecar's judgement and the predicate is not offered there.
- Personal switches, `switch off --local`, or a local override file —
  the lane judges the shared file only.
- Moving where review checks live in `run_gate`; the lane is a sibling
  branch, not a refactor of the regular one.

## Decisions

### One predicate owns the lane's shape: `operational_candidate`

The gate and the stage runner ask the same question — is this candidate
operational — so one function in `gate.py` answers it and `stages.py`
imports it. It returns the bundle the lane is judged under — the
contract, the base's shared extension names and the base's parsed
switches — or `None` when the candidate does not take the lane;
returning them keeps the lane block from re-deriving the reads the
qualification already made.

Qualification, in order:

1. The diff carries `.agentmarshal/switches.toml` — without it the
   candidate is journal-only or regular as today.
2. Every changed path is either that file or under
   `.agentmarshal/journal/tasks/<task>/` — the task's whole subtree,
   contract included, mirrors the journal-only lane's trust of a task's
   own journal paths. A manifest, any configuration, code, another
   task's records — any of it returns the candidate to the lane it
   takes today, where a review is owed.
3. The task's contract parses and declares `scope` exactly
   `[".agentmarshal/switches.toml"]`. Any other scope — empty, wider,
   naming the journal — is not an operational contract.
4. The base's switches file parses under the shared parser against the
   base's own shared extension names — an absent file parses as no
   entries. A file the read or the parse refuses keeps the lane
   closed: the candidate takes the lane it takes today and needs a
   review, because a removal or an unchanged entry cannot be judged
   against a base that cannot be read. The same is true when the
   base's extension enumeration itself is refused — the names the
   parser checks entries against cannot be enumerated.

The caller guards placement: `run_gate` asks only when `not sidecar`,
so the lane can never be offered in a sidecar even though a host diff
could spell the same paths.

### The contract is read from a tree, base first

`load_task_status` reads the working tree; the lane needs the contract
the candidate was written under, so the predicate reads it with the
gate's `ls-tree`/`git show` helpers instead. Two cases:

- The task exists at the base — its `contract.md` is in the merge-base
  tree — so the base's contract decides. A candidate that amends the
  contract inside its own journal subtree stays operational: the lane
  already bounds the diff, so the amended contract governs only the
  *next* transaction, which is how the regular lane reads scope today.
- The task is opened within the candidate — no `contract.md` at the
  base — so the candidate's added `contract.md` is read from the
  candidate's tree. This mirrors how the journal-only lane treats an
  opening transaction: the diff is bounded, so a contract the candidate
  itself publishes cannot widen what the lane admits.

An absent contract, a link or non-blob at its path, a blob git cannot
read, or text the contract parser refuses each return `None`: not
operational. The regular lane then reports the same contract's own
refusal — "contract not present in base tree", "invalid" — which is
the failure the candidate was always going to have.

### The lane's transcript

In place of the regular lane's scope-through-implementers block:

```
PASS: operational transaction (operational lane; review not required)
PASS|FAIL: <switches checks>
NOT EXAMINED: agreement (the operational lane requires none)
<named-documents check, when the contract names documents>
NOT EXAMINED: latest review (the operational lane requires none)
NOT EXAMINED: reviewer independence (the operational lane requires none)
NOT EXAMINED: independence rule '<rule>' (the operational lane requires no review)   — per declared rule
NOT EXAMINED: declared reviewers (the operational lane requires no review)           — when declared
<implementers check, when the contract names implementers>
```

Review, verdict, independence and agreement are what the lane requires
none of — each says so. "Latest review" names the single regular-lane
check that carries both a review's presence and its verdict. The
NOT EXAMINED lines for agreement and the two review checks print
unconditionally: the lane requires them never, whatever the project or
contract configures — the same shape the findings lane's constant
NOT EXAMINED lines have.

Checks that do not depend on a review still run as they do today:
named documents (`FAIL` when a named document goes untouched) and
declared implementers (`PASS`/`NOT CHECKED`/`FAIL` on session records
in the range) come out of the contract the lane read, so a contract
that asks for them still gets them. Named extensions load manifests
from the base with the regular lane's unreadable-refusal; extension
removal can never occur on the lane — a manifest path is never inside
the admitted diff.

Everything outside the lane block runs untouched: the
closed-at-base/admitted-records checks, the warn on other tasks'
records, pipeline attestation, append-only, added-record validity,
record-path collisions, lifecycle consistency, leak scanning.

### The changes_required count line stays silent

The count line exists to tell a converging review loop how many
`changes_required` verdicts stand. The operational lane has no review
loop, so it prints no line — the same suppression `journal_only`
already applies, by the same condition extended with `operational`.

### The switches checks

The candidate's file is read at the resolved commit and parsed by
`parse_switches` against the shared extension names enumerated at the
merge base — the same enumeration `stages.py`'s `_base_extensions`
performs, split into a shared `_extension_names_at_tree` helper so the
gate names extensions without loading manifests:

- No file at the candidate — the candidate deleted it — parses as no
  entries. A link or a non-blob at the path is `FAIL: <ref>:... not a
  file`, the refusal `stage run`'s base read already makes.
- A file `parse_switches` refuses — malformed TOML, a wrong `format`,
  an entry outside its shape, an entry naming no declared extension —
  is `FAIL` with the parser's own message, which names
  `<commit>:.agentmarshal/switches.toml` and, where the parse reached
  one, the entry.
- A parsed file is compared entry by entry against the base's file —
  parsed the same way when the base has one, treated as no entries when
  the base file is absent. A base file the read or the parse refuses
  never reaches this comparison: the predicate has already kept the
  lane closed, so the comparison judges entries against entries, never
  a guessed base. Every entry the candidate adds or changes relative to
  the base must carry `task` equal to this task; one naming another
  task refuses naming the file and the entry.

**A removal refuses.** An entry the base held and the candidate drops
refuses the candidate naming the file and the entry — and a candidate
that deletes the file while the base held entries drops every one,
refused the same way. Removing is a change like any other: it carries
the task that made it or it does not happen, so a dropped entry that
can no longer name a task is refused rather than waved through — a
bare drop is indistinguishable from forgetting to carry an entry
forward, and refusing makes the silent shape of that mistake a loud
one. The intended recovery is not a drop but a change: an entry with
`state = "on"` naming this task, which the added-or-changed rule
already admits. The dropped entry's `task` at the base is not
consulted — it is the absence that refuses.

An unchanged entry's `task` is likewise not consulted: the candidate
carries it from a change already admitted; it is not the candidate's
claim.

Every value the checks print — the ref, the file, entry names, tasks —
goes through the transcript's escaping, as every other line does.

### `stage run --phase pre-gate` skips before reading anything extension-side

Inside `_run_stages`, after the merge base is computed and before
`_base_extensions` is read: for `phase == "pre-gate"` only, the command
calls `operational_candidate` with the same arguments the gate will —
the task, the merge base, the resolved commit, the same
`diff --name-status` decomposition — and on a contract prints

```
stage run: pre-gate stages do not run on an operational change
```

then returns 0 having run nothing. Placing the check before the
extension enumeration is decision 17's point: a broken extension cannot
block the candidate that switches it off — no manifest is read, no
stage builds, no pause can stand. The predicate's own reads — the
base's contract, extension names and switches file — are gate inputs,
not extension code. Other phases fall
through to today's behaviour; a non-operational candidate is unchanged.

## Risks / Trade-offs

- A review record written for an operational candidate is not judged —
  the lane's admission is a property of the diff and contract, and the
  record stays evidence for `status`/`doctor` to show. Consistent with
  "requires no review".
- A contract declaring scope `[".agentmarshal/switches.toml"]` but
  naming documents the operational shape can never touch refuses
  itself — the documents check runs and fails. The contract is
  incoherent; refusing is the conservative read.
- The predicate does a small amount of extra git reading on every
  embedded candidate — two `ls-tree` lookups and, only when the diff
  qualifies, a `git show` — a cost in subprocesses on the order of the
  reads run_gate already makes per check.
- A candidate that amends its own contract to a different scope still
  takes the lane (the base contract decides) — the amended contract
  binds the next transaction only. Deliberate, matching how the regular
  lane reads scope at the base.
