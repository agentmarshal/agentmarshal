## Context

ADR-0021 decision 5: where the acknowledging actor is a declared writer
of the candidate, the mark says the hit was acknowledged by the
commit's author. `status` derives this — ` self-acknowledged` appended
to the record's line — by comparing the record's actor git identities
against the commit's declared author and committer names and emails.
The shared mark `leak-scan` and the gate's advisory line print —
`acknowledged by <recorded_by>: <reason>` from `capture`'s
`_acknowledgement_mark` — carries no identity comparison
(AUD-commands-3).

## Goals

- Every surface that prints an acknowledgement mark says
  `self-acknowledged` where the acknowledging party is a declared
  writer — the gate over the candidate range, `leak-scan` over the
  commit it scans — through the writer lookup and comparison CR-237
  made shared.
- An acknowledgement by any other party, and a writer check git cannot
  answer, prints byte-for-byte what it prints today; `status`'s output
  is unchanged.

## Non-Goals

- Who may acknowledge; the acknowledgement records themselves.
- The merge boundary's line — it carries no acknowledgement marks.

## Decisions

- **One shared derivation for the acknowledging party.** `report`
  holds `acknowledging_party_is_declared_writer`: the record's
  `recorded_by` resolved to git identities by the same
  `_actor_git_identities` `status` uses — the actors table of the
  journal's own project — plus the recorded name itself (an override
  can name a git identity outright), each held against the writer set
  by `accepting_party_is_declared_writer`, the comparison every surface
  shares. `status`'s `_is_self_acknowledged` is this derivation applied
  to the record's commit — the same code, not a copy.
- **Each surface supplies its own writer set.** `leak-scan` scans one
  commit, so it compares over that commit's declared writers read
  through `declared_commit_writers` in the scanned repository. The
  gate's advisory compares over the candidate range — the writer
  identities `_range_writer_identities` already yields where the
  verdict block ran, looked up lazily beside the advisory where it did
  not: whichever lane asks first leaves the answer for the other, so
  the range is read once. A writer of an earlier commit of the range
  therefore marks at the gate alone.
- **The mark builder takes the check, it does not make it.** `capture`
  stands under `report` in the import order — `records` imports it —
  so `_acknowledgement_mark` receives the derivation as a predicate and
  prints `self-acknowledged` in place of `acknowledged` only where it
  answers `True`. The masked-and-escaped form is otherwise untouched,
  and a caller that supplies no predicate prints today's mark.
- **Only a confirmed self-acknowledgement is marked.** A writer lookup
  git cannot answer yields `None` — the unchecked leg of `status`'s
  tri-state — and the mark prints as for any other acknowledgement:
  `status` alone says the check did not run, because a
  `not checked` note on the mark would break the byte-for-byte promise
  a non-self-acknowledgement makes.
