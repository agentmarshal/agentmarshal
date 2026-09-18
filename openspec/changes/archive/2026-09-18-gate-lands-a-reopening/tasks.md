## 1. The gate reads the projection's rule

- [x] 1.1 The base-state check admits a strictly additive candidate whose added records are all admitted after the task's terminal record, reading the admitted set and the reopening predicate from `status.py` — verify: no suffix list of admitted records remains in `gate.py` (grep).
- [x] 1.2 A reopening of a task completed at base passes the base-state check, with a transcript line that names it as a reopening — verify: gate test whose candidate diff is only the reopening record.
- [x] 1.3 A reopening of a task abandoned at base is refused — verify: gate test.
- [x] 1.4 Measurements-only appends still pass, and a review record on a closed task is still refused — verify: existing tests unchanged, plus one test for the review case if none exists.
