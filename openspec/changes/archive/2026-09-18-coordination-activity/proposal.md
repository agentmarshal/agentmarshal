## Why

Proposal 018 from the adopter batch: the session record's activity vocabulary
offers implementation, review and other. An agent-driven loop has three paid
roles — implementer, model reviewer, and the coordinator that writes contracts,
launches the implementer, reads verdicts and reports to the operator. The
coordinator is the most expensive per task (about 75 % of one fully measured
task's tokens, as reported) and fits only `other`. This project's own journal
shows the same proportion: every lead session is filed as `implementation`,
which is also wrong.

The disposition accepted the activity and deferred the money field, with a
reason: a price in an evidence record asserts something no reviewer of the
record can check. That half stays deferred.

## What Changes

`coordination` joins the activity vocabulary. The vocabulary is defined once —
today `records.py` and `backfill.py` each keep a copy. A coordination record
carries a newer schema number, so an older reader refuses it by schema rather
than by a field it does not understand, and journals that never use the value
stay readable by it.

## Capabilities

- new: `session-activity`

## Impact

`record-session --activity coordination` works. No other record changes shape.
The report's per-task total is unchanged; a per-activity breakdown belongs to
the accounting rework the disposition deferred.
