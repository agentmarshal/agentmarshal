# 025 — `validate` refused records an earlier release wrote

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.4.0 · **Source:** `sha256:4b86c6ddfac756a2270d29c2b8041c680d82606ecb0806e41023307029c84ce6` · **Disposition:** accepted *(in part; the allowlist is declined)*

## Finding

Before upgrading a pinned installation from 0.3.0 to 0.4.0, the reporter ran
the 0.4.0 wheel's `agentmarshal validate`, read-only, over their journal. The
same journal passes under 0.3.0; under 0.4.0 it printed one failure line for
each of two tasks — `review record finding id must not contain control
characters`, naming a review record an earlier release had written — and
ended in `validate: journal invalid`. The upgrade was halted: nothing of
schemas 4, 5 or 6 was written, and the pinned installation stayed on 0.3.0.

The mechanism, as the code has it. A record is validated when it is read —
`read_records` runs each record through the schema validator as it loads and
raises on the first invalid one — so the gate, which reads only the
candidate's task, never saw these records, while whole-journal `validate`
walks every task. `validate` reports every violation it finds; this refusal,
though, ends a task's read at its first bad record, so here it printed one
failure line per task and moved to the next. That is the shape of the run's
output: three records carry the character, across two tasks, and the run
refused the first such record in each task — the record in the second row
of the table below, the other one in the first task, sorted behind the
refused record in that task's records directory, was never read by it.

The check behind the refusal is `_reject_control_characters` in
`src/agentmarshal/journal/records.py`. It existed before 0.4.0, where it
guarded the acceptance record's fields and finding ids; 0.4.0 extended it to
review `findings` and `advisory_findings` — and to the finding record's
summary and artifact references, fields no earlier release could have
written. Its test was `str.isprintable()`, which is false for every space
separator except a plain space — U+00A0, U+2007, U+2009 and U+202F among them
— none of which can end a line, which is all the check exists to prevent. The
three records are `changes_required` verdicts by the model reviewer whose
finding ids are whole sentences, and in that prose U+202F separates thousands
(`71<U+202F>415`).

Measurements, as reported — counted over the journal as it stood before the
finding was filed, 282 task directories; the remaining 280 tasks were
reported `OK`:

| Measure | Value |
|---|---|
| Records | 1918 |
| Review records | 732 |
| Review records with a character for which Python's `str.isprintable()` is false (other than U+0020) | 3 |
| Occurrences | 11, all U+202F NARROW NO-BREAK SPACE |
| Field they occur in | `findings`, in all 11 cases |
| Characters of category Cc, Cf, Zl or Zp in any string value of any record | 0 |

The three records, across two tasks — the first two rows are one closed
task's, the third another's:

| Schema | `tool_version` | Written | U+202F |
|---|---|---|---|
| 2 | 0.1.0 | 2026-08-23 | 6 |
| 2 | 0.1.0 | 2026-08-23 | 3 |
| 2 | 0.1.0 | 2026-08-29 | 2 |

Because the journal is append-only and both tasks are closed, the gate
refuses changes to these records: the only local remedy would be rewriting
history, which is what the journal exists to prevent. Refusing them is
refusing history — every `validate` run and every merge whose wrapper
reproduces it would fail while they stand.

## Proposed

1. **Refuse what can break a line or reorder text, not everything
   non-printable.** Refuse categories `Cc`, `Zl` and `Zp`, plus the `Cf`
   bidirectional controls (U+202A–U+202E, U+2066–U+2069) if hiding text is in
   scope. Allow `Zs`.
2. **Do not tighten a rule over records an earlier release wrote.** A rule
   introduced with a new record schema applies to that schema and later ones;
   already-written records keep the rules they were valid under. Otherwise
   every stricter check is a breaking change to adopters' history.
3. **Validate a release against an adopter's journal before publishing.**
   Before publishing a version whose validation grew stricter, run its
   `validate` read-only over at least one real adopter journal.
4. **An allowlist of known-bad records** — a supported way to mark a
   historical record as accepted, by record id — or interim guidance to stay
   on the previous release until a fix ships.

## Disposition — accepted for the rule, the principle and the release check; the allowlist declined

**The narrowed rule** is accepted and already shipped. In 0.4.1 the check
refuses exactly what can forge a rendered line or reorder text: Unicode
categories `Cc`, `Cs`, `Zl` and `Zp`, and the bidirectional marks, embeddings,
overrides and isolates — and accepts the rest, space separators included. One
predicate, `forges_rendered_text`, decides it for records, contract headers
and the artifact references `validate` checks, so the three cannot drift
(CR-114). The shipped set adds two classes to the reporter's list: `Cs`, an
unpaired surrogate, which cannot encode as UTF-8 at all, so a record carrying
one could not be written back out; and three more bidirectional marks —
U+061C, U+200E and U+200F — which reorder displayed text as the overrides do.

**Not tightening a rule over records an earlier release wrote** is accepted
as a principle and not yet decided as a mechanism. The principle is what this
finding proves: a stricter check applied to records a closed task cannot
repair is a breaking change to an adopter's history, and the rules a record
was written under should be the rules it is read under. The open question is
how a reader knows which rules a record was written under — nothing in a
record says so today — and that decision is its own piece of work, not
bundled into this intake.

**The release check** is accepted and was done for the release at hand:
before 0.4.1 was published, its `validate` ran read-only over the journal
0.4.0 had refused, and passed — the run is reported in the message of
CR-115's completion commit (`git log --grep "complete CR-115"` finds it), not
in a journal record. The check answered for the journal that raised the
finding; a standing form of it — whose journals, at what point in a release —
is not yet settled.

**The allowlist** is declined, on the journal's own reasoning: an allowlist
declares a record acceptable around the gate. The exception would be a claim
no record attests, kept in configuration next to the evidence rather than in
it — the journal would hold a record it calls invalid and a note elsewhere
saying to read it anyway. The interim-guidance half of the proposal is
answered by timing: the fix shipped the same day, and the upgrade notes route
a pinned 0.3.0 installation straight to 0.4.1, past the release that refused
these records.

## Where

The narrowed rule and the release check shipped in 0.4.1 (CR-114, CR-115).
The retroactivity principle is accepted; the mechanism for it is undecided.
The allowlist is declined.
