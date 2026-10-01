# 026 — Unchecked reviewer facts, unconverging review rounds, and two further gaps

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.3.0 · **Source:** `sha256:e84a6250930b3145f82be59bcce626562bbd439c048eb13cded9d38f92246d44` · **Disposition:** accepted *(in part; `review --since` is deferred)*

One file, four findings, each with its own disposition below. All four were
observed on a single task — a research document evaluating third-party Python
libraries, with no code in it — whose review ran **eight rounds** while the
document's content did not change after the first.

The reporter's model reviewer runs inside their own wrapper, without network
access — the reporter's inference from three false claims of one kind, not a
configuration they inspected — and the reporter marks which side each finding
belongs to: the prompt and the reviewer's lack of network are their wrapper's;
the form of the review record, the gate that reads it, the link between review
records and the leak scan are the tool's. The reporter asks for none of the
things a quick reading might suggest: not network access for the reviewer
through the tool, not a cap on review rounds — the eight rounds were the
consequence of an acceptance criterion they wrote too broadly — and no change
to what `changes_required` means.

## Finding 1 — a finding asserts an external fact the reviewer could not check

Across the task the reviewer disputed **five** facts about third-party
libraries — a version, a release date, a license, an archived status. Checked
afterwards against machine-readable sources (the package index's JSON
metadata, the forge's API), **three of the five were false and two true**, and
the false ones were phrased as fact — "the index shows…", "the page states…" —
with no note that the source was never opened.

A fact dispute in which neither side attached a source does not converge:
every edit made under a wrong remark corrupts a correct fact, and declining to
edit without proof earns the same verdict on the next round. This task
converged only once the document quoted machine-pulled metadata as evidence.

The reporter proposes an `evidence` field on a review finding — a link or the
command that checked the claim — required of findings that dispute an external
fact, with the gate lowering one that lacks it to advisory so it cannot carry
`changes_required` alone; and a rule of the review protocol that a reviewer
who cannot reach a source writes "cannot confirm X; a source is needed",
never "X is wrong".

## Finding 2 — the rounds do not converge: new findings on unchanged lines

Findings per round: **6, 3, 4, 5, 2, 3, 3, 0**. Of the twenty findings in
rounds two through seven, **one** concerned the document's content; the rest
concerned form. Every one of those rounds produced findings on lines that had
existed, unchanged, since round one and that earlier rounds had not flagged —
a demand for verbatim verdict wording arrived in round six, at phrasing that
had been in the document since round one. The wrapper's prompt already
instructs the reviewer to report everything found in a pass; it does not help,
because the reviewer sees neither its own past findings nor what was already
accepted.

The reporter proposes that a review record link the previous review record of
the same task; that each finding carry a status against it — `new`,
`persisting`, `resolved`; that the gate or `report` print, for each round, how
many findings are new and how many sit on lines unchanged since the previous
round — a signal to stop the loop and revisit the acceptance, not a block; and
optionally that `review --since` hand the reviewer the diff since the last
reviewed commit together with the past findings and their status, which would
make "everything found in one pass" checkable.

## Finding 3 — recording cost after `complete` needs idempotency

0.3.0 allowed `record-session` on a closed task, and the reporter took it.
Their first implementation of "write after `complete`" would have doubled the
recorded cost of every task: their coordinating wrappers already wrote session
records before `complete`, and `report` sums all records. A second
implementation — skip the write if the task holds any session record — lost
the roles that were missing. What they shipped deduplicates by role.

The reporter proposes `record-session --if-missing`, or an idempotency key of
`task + role + actor + activity`, so that a repeat write under the same key is
a no-op with a message rather than a second record. That every adopter taking
"record after `complete`" the same way will arrive at the same place is the
reporter's expectation, not an observation — and the proposal exists so they
do not have to.

## Finding 4 — one binary file in a diff switches the leak scan off

A dry-run merge of a vendored-wheel update printed
`WARN: leak-scan skipped (git produced non-UTF-8 output: 'utf-8' codec can't
decode byte …)`. The warning says the scan was skipped; whether the whole diff
or only the binary file went unscanned, the message does not say. The
observation was single — a dry-run writes no journal record — and the reporter
asked us to reproduce it on our side rather than claim more.

We did, on 2026-10-01: a commit adding a text file holding a secret-shaped
string and a file of random bytes reported nothing from the scan, while the
same commit without the binary file reported the string. The gate decodes the
entire `git diff` output strictly as UTF-8, so one file's undecodable bytes
fail the decode and every file in the diff goes unscanned. The same root cause
— strict decoding of git's output — reached us from another adopter, whose
`agentmarshal review` run died on it (proposal 037); the two reports are one
defect.

The reporter proposes scanning per file: skip what `git diff --numstat` marks
with `-`, or what `Binary files differ` reports, with a note, scan the text
files, and keep the warning for the skipped files alone.

## Disposition — each part on its own

**The unverifiable-fact wording** (finding 1) is accepted, to be done: a
finding about a fact the reviewer could not check is stated as unconfirmed and
lands as advisory, rather than asserting the fact and carrying
`changes_required`. The `evidence` field was deferred at intake and moved to
accepted on 2026-10-01 — into the same question of review evidentiality it
waited on, where the same ask arrives from another adopter: what a review
record should say about how a claim was checked is to be answered once
rather than one field at a time. Not shipped yet.

**Converging rounds** (finding 2) is accepted, into the decision on the
finding lifecycle — the link between a task's review records, the
new/persisting/resolved status of a finding, and the per-round count the
reporter asks the gate to print are one machinery, and two further reports
from another adopter land in the same decision. `review --since` stays
deferred: handing the reviewer a bounded diff and its own history is the
right shape, and also the one most likely to change under whatever the
lifecycle decision settles — whether rounds link at all is that decision's
to settle, so the flag waits for it rather than arriving first.

**Idempotent cost recording** (finding 3) is accepted. A write that is safe to
repeat is the difference between a record and a trap, and a no-op with a
message under `task + role + actor + activity` is precisely the semantics the
reporter's three attempts converge on.

**The skipped leak scan** (finding 4) is accepted as a defect, reproduced
upstream on 2026-10-01 as described above, and sharing its root cause with the
other adopter's report from `review`, proposal 037: the fix is the per-file
scan the reporter proposes, so a binary file costs its own scan and not every
file's.

## Where

Nothing here is shipped yet. The protocol wording, `record-session
--if-missing`, and the per-file leak scan are accepted; the release that
carries them will say so in its changelog. The `evidence` field is accepted
into the review-evidentiality decision, the lifecycle machinery waits on the
finding-lifecycle decision, and `review --since` is deferred until it
settles whether rounds link at all.
