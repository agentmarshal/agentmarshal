## Why

ADR-0021 decided that a verified leak-scan hit is recorded rather than
bypassed: an operator who has checked a hit and found it harmless writes
an **acknowledgement** of it — a record of its own type bound to the
candidate commit, naming the file as the scan prints it and the hit's
identification, with a reason. ADR-0022 section 3 gave the record its
fields and its schema. CR-154 laid down the registry a record type
declares through and the shared field validators; CR-160 and CR-167
showed a field family and a record type registering. The journal cannot
yet carry an acknowledged hit at all.

## What Changes

- An `acknowledgement` record type joins the record-type registry,
  declared once: its predicate type, no projected state, admission after
  no terminal record, writable, `recorded_by` with `recorded_by_source`
  required.
- Its fields register as a schema-7 field family: `commit` (required,
  exactly 40 lowercase hex), `file` (required, the path as the scan
  prints it — already masked, non-empty), exactly one of `signature` (a
  built-in signature id the scan knows) or `marker` (an integer of at
  least 1, the marker's position), and `reason` (required, at most 1000
  characters). `reason` registers its character bound; `file` and
  `reason` register under the forgeable-text rule for this record type
  and field.
- An `acknowledgement` record stamped below 7 is refused at write and on
  read; a writer stamps 7 through the minimum-schema derivation, and
  `create_acknowledgement_record` builds the record.

## Capabilities

- modified: `leak-scan`

## Impact

No other record type changes, and the gate's fixtures are unchanged.
`signature` is validated against the scan's own signature table
(`capture.py`'s `_LEAK_PATTERNS`), so a new signature joins the
vocabulary the record admits with no second list. Nothing reads
acknowledgements yet: the `acknowledge` command, and the leak scan, gate
and `status` marking acknowledged hits, are later tasks.
