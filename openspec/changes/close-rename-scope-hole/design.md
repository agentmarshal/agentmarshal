## Context

`run_gate` calls two listings of the same range: `_changed_paths`
(`git diff --name-only`) for the scope check, the lane choice and the emptiness
refusal, and `_changed_with_status` (`git diff --name-status`, a rename
decomposed into a deletion and an addition) for the append-only, validity and
collision checks. The first listing shows a rename by its destination only.

## Decisions

- **One listing.** `_changed_paths` is deleted; the set of touched paths is the
  paths of `_changed_with_status`, deduplicated in listing order. The three
  readers change nothing but their source: `outside` is still sorted, the lane
  choice is still `all(...)`, the emptiness refusal is still on an empty list.
- **Not `--no-renames`.** Passing the flag to both listings would make git
  itself show a rename as a deletion plus an addition, and it would remove the
  `R` branch from `_changed_with_status`. It is the smaller diff but leaves two
  listings of one range and a rename-decomposing helper that never sees one;
  one helper that states the rule once is preferred.
- **The source is reported as a path outside scope, nothing more.** No new
  transcript wording: a rename's source is a deleted path the scope does not
  cover, and the existing line says exactly that.

## Risks

- A candidate that renames a path within scope now lists two paths where it
  listed one; the scope line's PASS wording carries no paths, so it is
  unchanged. The FAIL wording lists paths — a candidate refused today for a
  rename destination outside scope will list its source too if that is also
  outside.
