# Design

## Context

CR-150 shipped `outbox new` and `outbox check`: the outbox is
`project_root/.agentmarshal/upstream/` — the directory `init` scaffolds
beside `project.json`, so in an embedded project it is the host
repository's `.agentmarshal/` and in a sidecar the journal repository's.
`project_root` is therefore always a git worktree root — `init` wrote
`project.json` at the git root it found — and the repository a batch
commit belongs in is the project root's own, host lookup never involved.
ADR-0020 decisions 4–5 are this task: `send` makes one batch commit after
the check passes, and `status --index` compares outbox file hashes with
the `Source:` lines of an index file the operator passes.

The index format is what published digests carry since the batch of
2026-09-16 (`docs/proposals/README.md`, "Tracking what happened to
yours"): a `Source:` line holding the sha256 of the file sent, in full and
in lowercase hex, written in the digest headers as
`**Source:** \`sha256:<64 hex>\``. The operator obtains a file holding
such lines — a digest, a concatenation, `docs/proposals/README.md` itself
— and passes its path.

## Goals / Non-Goals

**Goals:**

- One command from checked drafts to one batch commit, with the check's
  refusal point kept in front of it.
- A status report that needs nothing but a file the operator already
  holds.

**Non-Goals:**

- Fetching the index or delivering the commit — both stay the operator's;
  the group opens no network.
- Changes to `new`, to the check's rules, or to init's README.
- Push, publish, or any second commit.

## Decisions

- **`send` runs `check` literally.** The first thing `send` does is run
  the same check the `outbox check` command runs — its report is the
  operator's reason when it refuses, and when it runs under `send` it
  also brings back the per-file digests the next decision verifies. Any
  non-zero result refuses the send: a non-conforming draft, a scan hit,
  an unchecked entry, a missing outbox, an unreadable config.
- **`send` refuses when anything outside the outbox is already staged.**
  The staged set is `git diff --cached --name-status -z` — which reads an
  unborn-HEAD repository against the empty tree, so a first send needs no
  special case. Every path a record names is judged, both halves of a
  rename or copy: a rename staged out of or into the outbox touches a
  path outside it and refuses. The refusal names the outside paths —
  masked, and escaped when not UTF-8, the way the check names files — and
  commits nothing. The rule protects both directions the ADR measured:
  findings riding along in another commit, and another commit's work
  riding along in the batch.
- **`send` refuses an outbox that holds no draft.** The README `init`
  writes is not a draft, so an outbox holding only it — or nothing —
  has no batch to make: the command says there are no drafts to send
  rather than committing the README alone.
- **`send` stages the outbox pathspec and commits once.** `git add
  --force -- .agentmarshal/upstream` — the README's
  `:(exclude).agentmarshal/upstream/**` applied the other way. `-f`
  because an ignore rule must not silently drop a draft the check just
  passed: the whole outbox is what leaves, so a file the adopter
  gitignored inside the outbox is checked like every file and then sent
  — never excluded. The staged set is read again after the add; when
  nothing under the outbox is staged for commit — the files are all
  committed and unchanged already — there is no batch and the command
  refuses. Otherwise `git commit -m` makes exactly one commit whose
  message is `outbox: findings batch` followed by one line per staged
  outbox path, and `git rev-parse HEAD` is printed — the commit, for
  whatever delivery the operator chooses. Delivery itself, and any
  push, is not the command's.
- **What is committed is what was checked.** A draft can change between
  the check's read and the commit, so the check itself pins every
  regular outbox file it reads: the blob id `git hash-object --stdin
  --path` computes from the very bytes the check vetted — the same clean
  filters the add applies, so the id is the one staging writes, and no
  second read gives an edit a window. After the add, `git ls-files
  --stage` under the outbox must show exactly those paths at stage 0
  with those ids: a changed, removed or newly arrived file is a refusal
  naming the mismatched names, and the index goes back.
- **A refused send — and only a refused send — puts the index back.**
  Before the add, the command records `git ls-files --stage -z` under
  the outbox. On a refusal after the add — a mismatch, a hook refusing
  the commit — those records are replayed through `git update-index
  --index-info` and every path now staged under the outbox that no
  record names is dropped with `git update-index --force-remove`. No
  step writes an object id, so the repository's object format cannot
  break it the way a hard-coded null id does — a mode-0 index-info line
  has to name the format's null id — and the plumbing form works where
  `restore --staged` cannot, an unborn HEAD. Index entries outside the
  outbox are never in either list, so nothing else is touched. Once
  `git commit` returns success the commit stands: a later step that
  fails — `rev-parse` reading the commit's id — is reported as a
  failure but puts nothing back.
- **Git runs with `subprocess`, captured bytes in, domain error out.** A
  helper mirrors `gate`'s `_run_git_bytes`: `subprocess.run` with
  `capture_output`, `check=False`; a missing git is described by its
  errno text (never `str(OSError)`, which carries a path), a non-zero
  exit by git's own stderr decoded with `backslashreplace`. The error
  names only the git subcommand — the arguments stay out because one of
  them can be the whole commit message, and the report would echo it
  back at the operator. The caller prints that text masked — a path git
  quotes back can itself carry a marker.
- **A name that is not UTF-8 is written in the escaped printable form.**
  `os.fsencode` reverses the surrogateescape decode the filesystem layer
  applied, giving the name's real bytes; decoding them with
  `backslashreplace` writes one `\xNN` escape per undecodable byte — the
  same form the leak scan uses for undecodable diff header lines
  (CR-127). `check` names every entry this way, `send` names staged paths
  this way in its refusal and in the commit message, `status` names every
  file this way, and the escaped text is what the marker masking and the
  name scan then see — a marker in a non-UTF-8 name is still masked, a
  signature beside it still matches. The surrogate-carrying `str` that
  crashed `check` at print time never reaches output again.
- **`status` hashes regular files and names what it cannot hash.** Every
  regular file in the outbox — `README.md` included, it leaves with the
  batch — is hashed with `sha256` over its bytes, lowercase hex. An entry
  that is not a regular file is named as not hashed, as is one that
  cannot be read (errno text only); either makes the report incomplete,
  so the exit is non-zero — the check's "nothing in the outbox passes in
  silence" rule, applied to the other direction of the channel. A symlink
  is never followed: the file as sent is the link, not its target.
- **What the index contributes is every `Source:` occurrence, identified
  by its digest.** Parsed: per line, each occurrence of `Source:` —
  optionally wrapped as `**Source:**` — followed by whitespace, an
  optional backtick, `sha256:` and 64 hexadecimal digits (either case,
  normalized to lowercase), then an optional closing backtick. Each
  occurrence is one index entry, but the entry's identity is the digest:
  two digests on one line are two entries, and the same digest on two
  lines is one. The line numbers stay for the report. For each outbox
  file the report says either `claimed by index line N` (or lines N, M)
  or `no index entry`; afterwards each entry that claimed no file is
  printed once per distinct digest — `index line N:` or `index lines N,
  M: sha256:<digest> claims no outbox file`. A missing or unreadable
  index is refused with a message before the outbox is touched; an index
  that holds no `Source:` line simply claims nothing.
- **The group keeps registering itself.** `outbox.py` gains the two
  subcommand parsers and two dispatch arms; `cli.py` is untouched — its
  hook already calls `outbox.register` and `outbox.run`.

## Risks / Trade-offs

- [A hook configured on the repository alters or blocks `git commit`] →
  the operator's hooks are theirs, like their identity configuration; a
  hook failure surfaces as a masked git error, no commit is claimed, and
  what the send staged is put back.
- [The check runs twice on a `send` — once as the send's gate, once if
  the operator ran it before] → the check is read-only and cheap; running
  it inside `send` is what makes the refusal point unconditional rather
  than a convention.
- [`-f` stages an intentionally ignored outbox file] → the outbox is the
  operator's own convention and the file passed a check that exists to
  vet exactly what leaves; an ignore hit there is an accident to
  override, and the alternative is a checked draft silently absent from
  the batch.
- [The index parse matches a `Source:` line anywhere in a file] → an
  index the operator made by hand or by `grep` is accepted on the same
  footing as a published digest header; a line that only mentions a
  digest without the `Source:` marker is not an entry, which is what
  keeps batch prose in `docs/proposals/README.md` from claiming files.
