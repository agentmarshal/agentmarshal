## 1. The rule

- [x] 1.1 The character predicate lives once and names its set by Unicode category plus the bidirectional codepoints; `str.isprintable()` is gone from both call sites — verify: grep.
- [x] 1.2 `contracts.py` calls the same predicate rather than keeping its own — verify: grep.

## 2. The behaviours

- [x] 2.1 `\n`, `\r`, U+2028, U+2029 refused wherever they were refused before — verify: test per class, records and contract.
- [x] 2.2 U+202A–U+202E and U+2066–U+2069 refused — verify: test.
- [x] 2.3 U+00A0, U+2007, U+2009, U+202F accepted — verify: test.
- [x] 2.4 A journal holding a schema-2 review record whose finding id carries U+202F validates — verify: test built from a record written as an earlier release wrote it.
- [x] 2.5 Refusal messages unchanged — verify: existing tests pass unmodified.

## 3. The upgrade note

- [x] 3.1 UPGRADING says what an adopter whose 0.4.0 `validate` refused a historical review record does, and names no mechanism that does not exist.
