## Context

`create_review_record`'s `reviewer_actor` parameter (CR-174) writes the
`actor` key inside the review record's `reviewer` object; the minimum-
schema derivation stamps 7 when the key is present, and the write-time
rule refuses an `actor` that is empty, all whitespace or carries a
character that could forge a line. What is missing is the path from a
command line to that parameter: `submit_review` — the one function both
`submit-review` and the `review` launcher record through — has no way to
receive it, and the parsers declare no flag.

ADR-0018 decision 3 frames what the value is: the *declared* reviewer
actor — a label for the `reviewers` membership and `distinct-actor`
checks a later task adds to the gate — never a derived identity.
`recorded_by` is the orthogonal stamp: it says who wrote the record and
`write_record` resolves it from the environment as before.

## Goals

- Both review-writing commands take `--actor <id>`; the value lands in
  `reviewer.actor` and the record stamps schema 7.
- A refused value costs nothing: the refusal precedes any write and any
  reviewer launch, and names the flag.
- An undeclared actor is accepted and noted — visibility, not a refusal
  (ADR-0006's declared-identity boundary).
- Without the flag, byte-for-byte silence: same record, same schema,
  same printed lines.

## Non-Goals

- The gate checks that read `reviewer.actor` (`reviewers` membership,
  `distinct-actor`) and `status` showing it — later tasks.
- Deriving the actor from `AGENTMARSHAL_ACTOR` or the git identity: the
  flag is explicit because the launcher is usually not the reviewer.
- `previous_review` and `classes` — a later task in the same module.

## Decisions

- **The flag flows through the one recording function.** `submit_review`
  gains `reviewer_actor` and passes it to `create_review_record`;
  `launch_review` gains it and threads it through `_launch_finding_review`
  and `_launch_review_tail` to the same call. The commit form and the
  finding-review form share the tail, so the flag reaches both — the
  record's binding rule (exactly one of `reviewed_commit`,
  `reviewed_finding`) is unaffected.
- **The flag is checked against the record rule before anything runs.**
  The rule's actor clause lives inside the schema-7 review-field rule —
  it cannot be isolated for a preflight — so `submit_review` restates
  its two conditions on the flag value: non-empty after stripping, and
  `forges_rendered_text` — the public predicate the record layer's
  `_reject_control_characters` raises on. The refusal names `--actor`
  rather than the field, so a mistyped flag is named as a flag. In
  `submit_review` it runs before `load_task_for_record`; in
  `launch_review` and `dry_run_review` before the reviewer command —
  where a refusal costs no paid run. `write_record`'s own check still
  stands behind it.
- **Declared-ness is tested on the id against the project file's
  `actors` keys.** An actor id is declared when it is a key of the
  section — the reading `_actor_git_identities` makes — not when it is a
  value of `_actors_table`, which maps identities to actors and would
  miss an actor declaring no identities. The project file consulted is
  the journal repository's, found through the same `_project_root_for`
  `write_record` resolves `recorded_by` from, so a sidecar's table is
  the sidecar's. An undeclared id is written and noted —
  `note: reviewer actor <id> is not a declared actor` on stderr —
  matching `agree`'s note for an undeclared recorder.
- **The note rides the result objects.** `SubmittedReview` and
  `LaunchedReview` gain `actor_note`; printing stays in the CLI, which
  owns every operator-facing line already.
- **`--actor` is the one record flag a dry run accepts.** The dry run
  exists to exercise the configured reviewer before money is spent; it
  validates the flag by the same preflight, then the CLI shows the actor
  a recorded review would carry and the same undeclared note. Every
  other record flag stays refused on a dry run.

## Risks

- [The preflight's restated actor rule drifts from the record layer's]
  → the record layer's check still runs on every write, so a drifted
  preflight is caught by the tests that pin both the refusal and the
  record — and the predicate it calls, `forges_rendered_text`, is the
  record layer's own.
- [An actor id is taken as authenticated] → the flag names a declared
  actor, which is a label until signing exists (ADR-0006); the command
  records what it is given and says when it is undeclared — the honest
  line, not a control the journal cannot keep.
