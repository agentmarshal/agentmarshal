# 044 — Unmeasured usage is written as zeros

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.4.1, rechecked on 0.5.0 · **Source:** `sha256:816c7ff8e0ad09bd1bc55f0030897758eba0a539c0da556744de745a76e57b0d` · **Disposition:** accepted *(reading side in 0.6.0; write side with the next record schema)*

## Finding

The reporter records the cost of every work session with `agentmarshal
record-session`. Some executor runs end without a usage figure: the run
was stopped before the agent CLI printed its final metrics, the CLI's
export format changed, or the sandbox failed before the model started.
For such a run there is no honest number to record — and the command
offers no way to say so. `--input-tokens`, `--output-tokens` and
`--cache-tokens` each default to `0` (`cli.py`), so omitting them still
writes `"tokens": {"input": 0, "output": 0, "cache": 0}` — which in the
journal is exactly what a run that cost nothing looks like.

The record models usage as always measured. `create_session_record`
(`journal/records.py`) writes the three-integer `tokens` object on every
session record; the optional `usage` object (`provider`, `method`)
carries the counts' provenance, and its absence is already a documented
reading — the quickstart says to omit the usage flags exactly when the
provenance is unavailable, and `report` reads that absence as
`usage=unrecorded`. But provenance is all that reading marks: the three
counts are still zeros that sum into the totals like a run that cost
nothing, and the record itself cannot say "not measured". Nor can the
distinction be written by hand: the `session-tokens` rule requires
`tokens` to be a mapping of exactly the three counts, each a
non-negative integer, so a session record without the object is
invalid — the schema admits no shape for "not measured".

How the reporter works around it, as reported: an executor wrapper
writes a per-run usage line, and a run whose counter was not found is
marked there with a total of `0` — a convention the wrapper documents,
because the zero cannot be told apart from a measured zero later. The
session records resolve the same ambiguity the other way: **a role
whose every run lacks a counter gets no session record at all.** The
cost of that workaround is that the run disappears from the journal —
its outcome and its actor are lost together with the missing number.

Measurements and impact, as reported:

- a journal-based cost report cannot separate cheap runs from
  unmeasured ones — `report` sums the `tokens` object of every session
  record — so averages are biased downward by an unknown amount;
- adopters either record misleading zeros or drop the session; this
  adopter drops it;
- numbers that look measured are not questioned from the other side
  either: in the reporter's journal, usage collection ran for nine
  consecutive tasks while not a single session record was written.

## Proposed

Make the token counts optional and explicit:

1. `--input-tokens`, `--output-tokens` and `--cache-tokens` default to
   "absent", not `0`.
2. When none is supplied, the record is written without a `tokens`
   object (or with `"tokens": null`), and the omission is guarded by an
   explicit marker — the reporter names `--usage-method unmeasured` —
   so that it is a statement, not an accident.
3. `validate` accepts such records; reports treat them as "unknown",
   never as zero.

The reporter weighed and rejected: recording zeros and relying on the
absent `usage` object — it marks the provenance unrecorded but leaves
the zeros in place, so any consumer summing `tokens` still gets the
wrong answer silently; a sentinel such as `-1` — the sums still
break, and negative counts would need special-casing everywhere; and
encoding the fact in `outcome` (`completed:unmeasured`) — which mixes
how the run ended with whether its cost is known, two independent facts
in one field.

## Disposition — accepted; the reading side in 0.6.0, the write side with the next record schema

**The reading side** is accepted for 0.6.0: `status` and `report` show a
session whose usage was not measured as unmeasured rather than folding
its zeros into the totals. For records written before the marker
exists, the signal they read is the one the finding names — the three
counts at zero and no `usage` object — and that signal is not
unambiguous. The quickstart tells the operator to omit the usage flags
whenever the provenance is unavailable, so a genuinely measured zero
recorded without them reads as unmeasured too. The acceptance takes
that trade knowingly: an agent session that ran consumes tokens, so a
real zero is the rare case, and only the write-side marker removes the
ambiguity. `report` already reads the absent `usage` object as
`usage=unrecorded`, and already shows the shape the rest of the
reading takes: sessions carrying no `cost` are counted apart, as
`sessions_without_cost`, never averaged as zero.

**The write side** — token counts that default to absent, and the
explicit unmeasured marker — is accepted with the next record schema.
Today it cannot be written at all: `create_session_record` always
writes the three counts, the `session-tokens` rule refuses a session
record without them, and `--usage-method` takes `reported` or `measured`,
paired with `--usage-provider`. Making `tokens` optional and extending
the marker vocabulary are changes to what a record may say, so they
travel with the schema rather than ahead of it — which is also why the
reporter's third item needs no entry of its own: `validate` accepts the
shape the schema defines, and "unknown, never zero" is the reading
side. Once the marker exists, the workaround of dropping the session
stops being necessary: an unmeasured run keeps its outcome and its
actor in the journal.

## Where

The reading side shipped in 0.6.0: a session record carrying zero token
counts and no `usage` block renders as unmeasured — `status` prints
`tokens=unmeasured` and `report` carries `unmeasured=<n>` on the task,
Summary and Cost lines — while an unmeasured session that carries a
cost still sums. The write side — optional token counts with an explicit
unmeasured marker — stays accepted with the next record schema.
