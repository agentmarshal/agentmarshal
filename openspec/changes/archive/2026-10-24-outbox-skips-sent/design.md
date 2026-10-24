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
  file and a non-UTF-8 name has no other writable form; matching never
  uses it, only the digest does.
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
  what the manifest would become — the manifest's current bytes, plus
  one `<sha256>  <name>` line per draft, appended in the outbox's
  sorted entry order — and pins the `SENT` path to the blob id of those
  bytes, the same `hash-object --stdin --path` pin every file gets.
  `send` writes exactly those bytes before the add, so the staged
  manifest blob is the pinned one and the same batch commit carries
  drafts and manifest together.
- **A manifest with nothing to add does not make a batch.** When the
  only thing the add stages is `SENT` — every draft already committed
  and unchanged — there is nothing to send and the send refuses as
  today, index and manifest file both put back. A refusal after the
  manifest write likewise puts the file's bytes back — or removes it
  when there was none — so a manifest never claims files a commit
  never landed; a made commit is never put back.
- **"No drafts to send" means no drafts.** The count is of drafts
  under the new rule: an outbox holding only the README, the manifest
  and already-sent files has nothing to send.
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
