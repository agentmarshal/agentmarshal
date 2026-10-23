## Why

Proposal 035 measured the defect: commands write records into the
working tree and adopters stage the whole journal directory, so a
journal transaction sweeps whatever is uncommitted at that moment, for
every task — on the reporter's history, 28% of journal transactions
carried files of other tasks, including 23 contracts and 20 `opened`
records. `validate` accepts such records, and it should: they are valid
evidence wherever they arrive from. What was wrong is which transaction
carried them, and nothing in the tool says so. The same sweeping keeps
the coordinator from answering "is this contract published yet" without
its own git reading — which is what missed the record that had arrived
inside another task's pull request.

## What Changes

- `gate` on a transaction that adds `opened` or `amendment` records of a
  task it does not name prints one WARN line naming each such task and
  the kinds it added — `opened`, `amendment` or both. The records stay
  valid evidence: the candidate is not refused over them, the
  violations count does not move, and a candidate adding no such record
  produces today's transcript byte for byte.
- `agentmarshal status <task> --base <ref>` prints, after the detail
  view it prints today, one line per record present in the task's
  journal directory but absent from `<ref>` — the record's id and type —
  or one line saying there are none. The ref resolves in the journal's
  own repository: under a sidecar placement the sidecar's, never the
  host's. An unknown ref refuses naming it; `--base` without a named
  task refuses; without `--base` the command prints exactly what it
  prints today.
- Every value the warning and the listing print — task names, record
  ids, record kinds, the ref — is escaped on display like every other
  value these surfaces print.

## Capabilities

- modified: `gate-lanes`, `record-lifecycle`

## Impact

`src/agentmarshal/journal/gate.py` gains the warning;
`src/agentmarshal/journal/status_view.py` gains the ref comparison;
`src/agentmarshal/cli.py` gains the `--base` flag on `status`. The
transaction helper that stages only the named task's journal directory
rides on proposal 019's accepted work and is not part of this change.
