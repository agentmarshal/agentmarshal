## Context

Proposal 035's accepted disposition is two surface changes plus the
per-task staging that rides on proposal 019's helper: the gate warns —
does not refuse — when a transaction adds `opened` or `amendment`
records of a task it does not name, and `status` lists a task's records
present in the working tree but not yet on a named base ref.

The gate already enumerates every record path the candidate adds —
`added_records` over `record_changes` — and already parses the record
kind and task directory out of the path for its lifecycle-consistency
checks. `status` already loads the task's stored records for the detail
view. Both changes are therefore listings over data the code already
holds; what is new is the second repository read `status --base` needs,
and the judgement call of which repository it runs against.

## Goals

- One WARN line for the whole anomaly, not one per record or per task:
  it names each task whose `opened`/`amendment` records the transaction
  added and the kinds it added them in — `CR-002 (amendment, opened);
  CR-003 (opened)` — so the operator sees the sweep at a glance.
- The warning is advisory in the proposal's own terms: the records stay
  valid evidence and nothing is refused because of it — no
  `changes_required`, no exit-status change, and a candidate carrying no
  such records emits the byte-for-byte transcript it emits today.
- `status <task> --base <ref>` answers proposal 035's coordinator
  question — "is this contract published yet" — as a listing of the
  task's records in the working tree whose paths the ref's tree does not
  hold: the record's id and type on a `-` line each, a header naming the
  ref as given, and one `(none)` line when the ref lacks nothing.

## Non-Goals

- Per-task staging. Proposal 019's transaction helper — which the
  disposition holds to "stages only the journal" of the task it is given
  — is separate accepted work; this change makes the sweep visible and
  keeps it harmless.
- Warning on other record kinds. Review, session and check records
  riding the wrong transaction are the bulk of the reporter's 28% and
  are bookkeeping noise; warning on them would train operators to ignore
  the line. `opened` and `amendment` are the agreement events the
  proposal names.
- Refusing. The disposition is explicit — the reporter's lesser option.
  A refusal would make a valid-evidence record arriveable only by
  rewriting history, against ADR-0004.
- Comparing record contents. The listing answers "is this record on the
  base yet" by path: a path the ref holds is published, whatever its
  bytes say there; a rewritten path is a question for `validate`, not
  for a read-side listing.

## Decisions

### The warning counts tasks, not paths

A record path's task directory — `.agentmarshal/journal/tasks/<task>/`
— decides belonging; the filename's `<id>-<type>.json` decides kind.
Both are what the record-validation checks already verify, so the
warning can trust them. Tasks are grouped in sorted order and each
task's kinds in sorted order, so the line is deterministic for a given
diff.

### Comparison is by path, in the journal's repository

`--base` resolves and lists inside the repository the journal lives in:
`find_git_root(journal_root)` — the project repository in the embedded
placement, the sidecar repository in the sidecar one. The host
repository's refs are deliberately never consulted: a sidecar's records
are not tracked in the host's tree, so a host ref could only answer by
accident. The ref is verified as a commit
(`rev-parse --verify <ref>^{commit}`) and the records the ref holds are
read with `ls-tree -r --name-only -z` under a literal pathspec of the
task's records directory — NUL-separated and literal so no record path
or ref spelling is re-interpreted. What the working tree holds comes
from the already-loaded task projection's stored paths, so nothing is
reread.

### Failure refuses before output

An unresolvable ref — unknown name, or no git repository above the
journal — returns nonzero naming the ref on stderr, and the detail view
prints nothing first: a partial view under a failure message would read
as a successful answer.

### Ordering in the view

The listing prints after the detail view `print_task_detail` produces
and before the overdue-steps lines, which report this machine's process
log rather than the journal — journal-derived lines keep their first
position in the view's contract. With `--base` absent nothing is
appended and the view is byte for byte what it is today.

## Risks / Trade-offs

- A transaction that sweeps another task's records now prints a WARN on
  every gate run until those records merge — the intended visibility,
  and the cost of an advisory line.
- `ls-tree` answers what a commit's tree holds; a ref naming an
  annotated tag is peeled to its commit by `^{commit}` before listing,
  which is the behaviour an operator expects from "the base branch".
