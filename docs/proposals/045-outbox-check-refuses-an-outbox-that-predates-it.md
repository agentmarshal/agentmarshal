# 045 — `outbox check` refuses an outbox that predates it

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.5.0 · **Source:** `sha256:a819341cbe9022523a08b200c6ee92e687335c6b83fd4b12a88b22b35a411008` · **Disposition:** accepted

## Finding

0.5.0 shipped the `outbox` group of
[ADR-0020](../adr/ADR-0020-the-outbox-command-group.md) — `new`, `check`,
`send`, `status` — and the upgrade material the reporter received
suggested sending a pending finding with `outbox new` / `outbox send`.
The reporter's outbox predates the group: `.agentmarshal/upstream/` was
created by hand before `init` scaffolded one, and holds ten finding
files written before the group existed, nine of them already sent. On
that directory `outbox check` refuses the whole batch — one line per
file naming the fields it lacks — and `outbox send`, which runs the same
check first, refuses with it. The pending finding was delivered by
copying the file, the way the earlier batches went.

Measurements, as reported:

- 10 of the 10 finding files are refused, 0 conform; `README.md` is
  skipped, as designed;
- 8 files carry none of the five form fields as a second-level heading —
  they predate the form, and the reporter's English-at-source rule
  besides;
- 2 files carry `## Symptom` only — the section scheme the reporter
  settled on before the form existed;
- 9 of the 10 were sent before 0.5.0, and each one's sha256 is the
  `Source:` line that links it to its public digest — editing them into
  the form would break that link for every one of them; the tenth was
  sent by copy for the same reason;
- there is no flag or configuration key that changes which files are
  checked.

The mechanism, as the code has it. `_check` in
`src/agentmarshal/outbox.py` iterates every entry of the outbox and
treats each regular file other than `README.md` as a draft, requiring
the five fields as exact `## <Field>` headings; an entry that is not a
regular file — a subdirectory, for instance — is reported `not a draft,
not checked` and refuses the batch just the same. `_run_send` runs that
check literally and, when it passes, stages the whole directory (`git
add --force -- .agentmarshal/upstream`). The group has no notion of a
file that was already sent — although `outbox status` already computes
exactly that: it sha256-hashes the outbox files and matches them against
the `Source:` lines of an index file the operator passes with `--index`.

## Proposed

1. `check` and `send` skip files that are already sent, decided by
   sha256 — the matching `outbox status` already does. The input can be
   the same index file `status` takes, or a small manifest of sent
   hashes kept in the outbox and written by `send` itself.
2. Report the skipped files on one line (`skipped as sent: 9`), so the
   skipping is visible rather than silent.
3. Until then, say in the upgrade note that an outbox predating 0.5.0
   will not pass `check`, so adopters do not discover it at the moment
   they try to send.

The reporter weighed and rejected: rewriting the sent files into the
form — it breaks the sha256 `Source:` link to their public digests, the
only link the reporter holds; moving the sent files into a subdirectory
— `check` refuses any entry that is not a regular file, so the batch is
refused still; moving them out of the outbox — the same link breaks,
and `outbox status` could no longer hash them in place; and continuing
to deliver by copy — which works today, but gives up what `send` exists
for: the leak scan over exactly what leaves, and a batch commit pinned
to the checked bytes.

## Disposition — accepted for 0.6.0

**Skipping the already-sent** is accepted for 0.6.0, keyed on the hash
the reporter names — the sha256 `outbox status` already matches against
an index. The knowledge arrives by the routes the proposal offers — a
manifest of sent hashes that `send` writes, and the same index file
`status` takes — because each covers what the other cannot: the manifest
marks what this tool sent, while the index reaches back to findings
that left before it existed, or by copy. Deciding by hash rather than
by name also keeps the property the `Source:` line exists for: a file
edited after it was sent is a new draft, not a sent one.

**Reporting the skipped files** is accepted with it — one line, `skipped
as sent: N` — on the rule `_check` already prints by: nothing in the
outbox passes in silence.

**Saying so in the upgrade note** is overtaken by the fix itself: a note
warning that a pre-0.5.0 outbox will not pass `check` is true of the one
release that already shipped, and the notes for 0.6.0 describe the skip
instead of the refusal.

## Where

`outbox check` and `outbox send` skip files already sent — known by a
manifest of sent hashes that `send` writes, or by the index `outbox
status` takes — with the skipped files reported rather than silent, in
0.6.0. Not shipped yet.
