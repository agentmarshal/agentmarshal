# Design

## Context

The outbox already takes its boundary seriously inside the repository:
`send` stages only `.agentmarshal/upstream/`, pins each staged blob to
the bytes the check read, and puts the index back when a commit fails.
The audit's three findings are all boundary leaks the pinning does not
cover — one below the outbox's root (a symlink in its own path), one
inside git (attributes that rewrite bytes on staging), one on the way
out (`status` printing raw names).

## Goals / Non-Goals

**Goals:**

- A linked `.agentmarshal` or `.agentmarshal/upstream` is refused before
  the outbox creates, writes or stages anything.
- `send` commits exactly the bytes the check vetted — a git attribute
  that would transform them refuses the run.
- `status` prints names the way `check` and `send` do.

**Non-Goals:**

- Following, validating or reporting where a link points — a link is a
  link, whatever its target.
- Any other outbox behaviour.

## Decisions

- **The component check is `lstat`, one refusal per command.** The
  project root `find_project_root` returns is already resolved, so the
  only components that can be links are `.agentmarshal` and `upstream`;
  each is checked with `is_symlink()` — lstat, no following — the same
  refusal `extension_trust._managed_directory` applies to the managed
  extensions directory and `write_project_file` applies to the project
  file's parent. It lives in `_locate`, so all four subcommands refuse
  identically, before any outbox I/O. `init`'s scaffold is best-effort:
  it returns the refusal as its error text and `init` reports it on its
  one warning line, still succeeding as a project.
- **The pin is compared, not re-derived.** `hash-object --stdin --path`
  yields the blob id staging writes; `hash-object --stdin --no-filters`
  yields the blob of the bytes read. Asking git twice keeps the check
  object-format-agnostic (sha256 repositories included) and covers
  every transformation git knows — clean filter, `ident`, eol — rather
  than enumerating them. A mismatch is a check problem on the file,
  named like every other, so a refused `send` stages nothing.
- **`status` reuses `_printable`.** The masked-then-escaped order the
  helper already implements is the audited property — escaping first
  would insert word characters a signature's anchors do not see past —
  so the fix is swapping `safe_path(_shown_name(...))` for `_printable`,
  not a second renderer.
