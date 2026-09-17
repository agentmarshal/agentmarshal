## Context

`review.py` builds the prompt from a module constant and a suffix of named
material (contract, named ADRs, named documents). `brief.py` renders the same
material for the implementer. `records.py` validates records against a closed
field set per schema, and selects the schema a writer stamps.

## Decisions

- **The block goes after the contract, in both renderings, with one wording.**
  A reader who has seen one recognises the other. The prompt's fixed text is a
  module constant and stays one constant, as CR-089 required.
- **A task with no amendment records gets no block and no heading.** Not an
  empty section: the pinned 0.3.0 prompt test must pass unmodified, and it is
  the cheapest proof that nothing moved for journals that never amend.
- **Order is the order the records were written.** Amendment records are
  append-only and their ids sort by time, so no separate sort key is needed.
- **The hash is over the exact bytes the prompt carried.** Not over the file on
  disk, which may differ from what the reviewer was handed in a sidecar, and not
  over a normalised form. Same discipline as the pinned review prose (CR-091).
- **Schema 5 follows the shape of schema 4.** `_SCHEMA_5_FIELDS` holds the new
  field, `_SUPPORTED_SCHEMAS` gains 5, and a writer stamps 5 only when the field
  is present, keeping the current floor for everything else. The refusal message
  names the field, as the schema 4 message does.
- **`submit_review` passes the field through when its caller has one.** The
  launcher has one; the human path does not and must not invent one.

## Risks

- [The prompt suffix is assembled in more than one place] → CR-089 made the
  fixed text one constant; the block is appended where the named material is
  appended, not in a second assembly path.
- [A sidecar reads the contract from its own working tree] → the hash is over
  what was read, so the sidecar case needs no separate branch.
- [An amendment reason containing the block's own delimiter] → the reason is
  quoted material and renders as text; no delimiter that a reason could forge.
