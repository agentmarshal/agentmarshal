## 1. The vocabulary

- [ ] 1.1 `coordination` is a valid session activity, defined in one place and read by `records.py`, `backfill.py` and the CLI help — verify: grep finds one definition.
- [ ] 1.2 A coordination session records, validates and reads back — verify: test.
- [ ] 1.3 An activity outside the vocabulary is still refused — verify: existing or new test.

## 2. The schema

- [ ] 2.1 A coordination record carries the newer schema number; the supported schema set grows by it — verify: test on the written record.
- [ ] 2.2 Records with the other three activities keep their schema — verify: test.
