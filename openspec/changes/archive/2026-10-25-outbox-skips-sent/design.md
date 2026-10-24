# Design

## Context

CR-150 shipped `outbox new` and `outbox check`; the next task shipped
`outbox send` and `outbox status`. The check judges every regular file
in the outbox but `README.md` a draft; `send` runs that check, stages
only `.agentmarshal/upstream/`, pins the staged blobs to the bytes the
check read, and makes one batch commit. `status --index` parses an
index file's `Source:` lines into digests and hashes each outbox file
with sha256 to compare.

Digest 045 reports what that costs an outbox that predates the group:
files already sent cannot be rewritten into the draft form — their
sha256 is the link to the published digest — so the check refuses the
batch and `send` can never run. The fix is the matching `status`
already does, turned around: a file whose sha256 is listed as sent is
not a draft and is not checked.

## Goals / Non-Goals

**Goals:**

- An outbox holding files already sent can check and send new drafts
  without rewriting or moving them.
- `send` records what it sends, so the next run needs no index.

**Non-Goals:**

- Changing the draft form, the leak scan's coverage, or `status`.
- Rewriting or moving files already sent; the manifest maps, it does
  not move.
- Fetching the index or delivering the commit — both stay the
  operator's; the group opens no network.

## Decisions

- **The sent manifest is a file named `SENT` in the outbox.** One
  `<sha256>  <name>` line per file sent — the `sha256sum` output form:
  digest, two spaces, name. The name cannot be mistaken for a draft:
  no `.md` suffix, no `NNNN-` number, uppercase like the README — and
  like the README it is not a draft but still leaves with the batch,
  so it is still read, pinned and scanned. The name on a line is the
  escaped printable form every command prints — the manifest is a text
  file and a non-UTF-8 name has no other writable form. The sent-skip
  itself matches only the digest; the name serves one purpose, the
  `changed after sending` annotation below — a line names a file and
  the digest beside it is what it was sent as.
- **A name that could add a line is refused, never written.** A file
  name carrying a newline or another character a line of text cannot
  hold — the set `forges_rendered_text` refuses — can take no manifest
  line and can forge one: the check names the file in escaped
  printable form and refuses, for a draft and for an already-sent
  file alike. The read side is strict to match — and loud: only a
  line of exactly `<64 lowercase hex>  <name>` with a name free of
  those characters is a manifest entry, and a line in any other
  shape — or a line that is not UTF-8 at all — does not parse. The
  command prints the manifest's name and the
  line's number and refuses — the manifest invites a hand edit (the
  `sha256sum` form is meant to be writable), so a typo restores the
  very refusal digest 045 reported unless it is diagnosed.
- **Masking runs on the raw name, escaping second.** A name is masked
  by `safe_path` on the raw shown form and escaped by
  `escape_for_display` after — escaping first inserts word characters
  (`\t`, `\uXXXX`) that defeat the signatures' `\b` and `\s` anchors,
  so a secret beside a control character would print unmasked. The
  escaped, masked form is what prints.
- **A file is already sent when its sha256 is listed.** The check
  hashes each regular outbox file — it reads every one for the scan
  anyway — and a draft is a regular file that is not the README, not
  `SENT`, and whose sha256 no manifest line lists and no `Source:` line
  of a passed `--index` claims. `--index` is optional on `check` and
  `send` and takes the same file `status` takes; the parse is the one
  `status` runs, factored into a helper so the commands cannot drift.
  A skipped file is still read, pinned and leak-scanned — it leaves
  with the batch like every file — it is only not judged on the five
  fields. Each command prints `skipped as sent: <n>` when it skipped
  any, so skipping is never silent.
- **A manifest name beside a different sha256 is "changed after
  sending".** When the manifest names a file the outbox still holds but
  the file's sha256 is not what the manifest lists — and no other entry
  claims it — the file is not skipped: it is checked like a draft, and
  the check's line for it says `changed after sending`, an annotation,
  not a refusal: the draft's own conformance decides, exactly as for
  any draft.
- **`send` writes the manifest inside the same batch commit, pinned
  like every file.** While the check reads the outbox it also computes
  what the manifest would become — its parsed lines, each following
  the name its digest still names, plus one `<sha256>  <name>` line
  per draft, appended in the outbox's sorted entry order — and pins
  the `SENT` path once, to the blob id of those bytes, the same
  `hash-object --stdin --path` pin every file gets (the file itself
  is not pinned a second time on its old bytes). `send` writes
  exactly those bytes before the add — only when they differ — so
  the staged manifest blob is the pinned one and the same batch
  commit carries drafts and manifest together. The leak scan covers
  those bytes too — the manifest's next content is scanned like
  every file the batch carries, because a name that trips nothing
  alone can match once it sits on a manifest line (a signature whose
  match spans the line break) — a hit refuses the run before `send`
  stages a byte.
- **The manifest's kept lines follow a renamed file.** A manifest
  line records `<sha256>  <name>`; when the outbox no longer holds
  the name and the sha256 names exactly one file in it — a rename, a
  move inside the outbox — the rewritten line takes the name the
  file now carries, so the renamed file stays skipped and the record
  still says where it is. A line whose name still exists, or whose
  digest matches no file or several, is kept as written.
- **A manifest with nothing to add does not make a batch — but an
  outbox change to a sent file does.** When the only thing the add
  stages is `SENT` — every draft already committed and unchanged —
  there is nothing to send and the send refuses as today, index and
  manifest file both put back. A refusal after the manifest write
  likewise puts the file's bytes back — or removes it when there
  was none — so a manifest never claims files a commit never
  landed; a made commit is never put back.
- **"No drafts to send" means no drafts and no committable change.**
  When the check finds no draft, `send` still stages the outbox, and
  the only batch it commits is the outbox's own record: every change
  the staged diff holds must be a rename or a move of a file already
  sent — status `R` — or the manifest update that follows one, with
  at least one rename among them (ADR-0020 decision 6: the exclude
  pathspec keeps findings out of journal commits, so the commit a
  renamed sent file earns is exactly the outbox-only transaction the
  group exists to provide), the message naming both paths of a
  rename. A passed check with no draft leaves a regular file no
  other change to make — the README and the manifest are never
  drafts and every other file is already sent — so any other staged
  change, a modified README, an untracked non-draft, a deletion, a
  pure addition of a skipped file, or the manifest alone, refuses
  saying there are no drafts to send and puts back what it staged.
- **Entries that are not regular files are unchanged.** A directory, a
  symlink, a FIFO is still reported on one line as not a draft and not
  checked, and still refuses the batch: `send` stages the whole outbox,
  so a skipped entry's contents would leave unchecked and the leak
  scan's every-staged-file coverage would break.

## Risks / Trade-offs

- [A skipped file carrying a marker or signature still trips the scan]
  → intended: the file leaves with the batch, so its name and content
  are scanned like every file's; only the five-field judgement is
  skipped. An adopter whose sent file trips the scan already published
  it; the refusal tells them.
- [A hash collision between a draft and a manifest line silently
  skips a draft] → a sha256 collision means the file is byte-identical
  to what was sent, so skipping it is correct.
- [A refused send leaves the written `SENT` on disk] → it does not:
  the restore puts the old bytes back or removes the file, so a later
  check never skips drafts a failed commit claimed as sent.
- [An index naming a file that is not in the manifest skips it for
  that run only] → intended: the index is per-run evidence; the
  manifest is the record `send` maintains.
