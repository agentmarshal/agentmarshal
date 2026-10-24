# Spec Delta

## MODIFIED Requirements

### Requirement: `outbox check` names what each draft lacks

`agentmarshal outbox check` SHALL read every draft in the outbox — every
regular file except the `README.md` that `init` writes, except the sent
manifest `SENT`, and except a file already sent — a file whose sha256 a
line of `SENT` lists or, when `--index <file>` is given, a `Source:`
line of that index claims — and, for each draft that does not conform,
SHALL name the file and each field of the five that is missing or still
unfilled: a field is missing when the draft has no `## ` heading for it,
and unfilled when its body is empty or is the scaffold's placeholder
unchanged. A draft that is not UTF-8 text SHALL be named as such.

#### Scenario: a freshly scaffolded draft is unfilled in Symptom, Measurements and Expected
- **WHEN** `outbox check` runs over a draft straight from `outbox new`
- **THEN** it names the file as unfilled in Symptom, Measurements and
  Expected — and not in Version or Environment

#### Scenario: a draft that dropped a field is named with the missing field
- **WHEN** a draft has no `## ` heading for a field — its `## Expected` was
  removed
- **THEN** the check names the file and the missing field

#### Scenario: a field emptied by hand is unfilled
- **WHEN** a field's body in a draft is emptied — Version cleared of the
  value `new` wrote
- **THEN** the check names the file and the field as unfilled

#### Scenario: the README init writes is not a draft
- **WHEN** the outbox holds only the README `init` wrote
- **THEN** no file is named and the check passes

#### Scenario: check refuses when there is no outbox
- **WHEN** the project has no `.agentmarshal/upstream/` directory
- **THEN** the command fails with a message saying there is no outbox

## ADDED Requirements

### Requirement: `outbox check` and `outbox send` skip files already sent

`agentmarshal outbox check` and `agentmarshal outbox send` SHALL take an
optional `--index <file>` — the same index file `outbox status` parses —
and SHALL treat as already sent, and not check, a regular file whose
sha256 is listed in the outbox's sent manifest — the file `SENT` in the
outbox, one `<sha256>  <name>` line each, lowercase hex — or claimed by a
`Source:` line of the index when `--index` is given. A skipped file is
still read and still goes through the leak scan — it leaves with the
batch like every file — it is only not judged as a draft; and it is
never the manifest or the README, which are not drafts either. Each
command SHALL print one line `skipped as sent: <n>` when it skipped any,
so skipping is never silent. A file whose name a manifest line carries
beside a different sha256 is not skipped — its bytes changed since it
was sent — so it is checked like a draft and the check SHALL name it as
changed after sending: an annotation, not a refusal.

#### Scenario: a file the sent manifest lists is not checked as a draft
- **WHEN** the outbox holds a file whose sha256 a `SENT` line lists —
  whatever its fields hold
- **THEN** the check does not name it as a draft, prints
  `skipped as sent: <n>` counting it and every other skipped file, and
  passes when everything else conforms

#### Scenario: `check --index` skips a file a Source: line claims
- **WHEN** `outbox check --index <file>` runs and a `Source:` line of
  the index claims an outbox file's sha256
- **THEN** the file is not checked as a draft and the command prints
  `skipped as sent: <n>`

#### Scenario: `send --index` skips a file a Source: line claims
- **WHEN** `outbox send --index <file>` runs and a `Source:` line of
  the index claims an outbox file's sha256
- **THEN** the file is skipped like a manifest-listed one and the batch
  commits what remains

#### Scenario: a manifest-listed file whose bytes changed is checked and named as changed after sending
- **WHEN** a `SENT` line names a file beside a sha256 the file no longer
  has, and no entry claims the sha256 it has
- **THEN** the file is checked like a draft and the check names it as
  changed after sending

#### Scenario: the sent manifest is not a draft
- **WHEN** the outbox holds `SENT`
- **THEN** the manifest is not checked as a draft and is not counted in
  the skipped line

#### Scenario: an unreadable sent manifest refuses the check
- **WHEN** `SENT` exists as a regular file and cannot be read
- **THEN** the command refuses with a message

#### Scenario: send refuses when every file is already sent
- **WHEN** every regular file in the outbox is already sent — none is a
  draft
- **THEN** `outbox send` refuses saying there are no drafts to send, and
  commits nothing

### Requirement: `outbox send` records the batch in the sent manifest

`agentmarshal outbox send` SHALL add to the outbox's sent manifest, in
the same batch commit as the drafts it sends, the sha256 of each draft
the batch carries — one `<sha256>  <name>` line each, appended to the
lines the manifest already holds — so a later `check` skips them
without an index. The manifest update SHALL be pinned by the same
checked bytes as every file the batch carries: the content committed is
the content the passing check computed, staged under
`.agentmarshal/upstream/SENT` and verified against the staged blobs
like every pinned path. A batch that would stage only the manifest is
nothing to send and SHALL be refused as an empty batch is. A refused
send SHALL leave the manifest's bytes as it found them — or absent
when there was none — as it leaves the index, so a failed commit never
leaves a manifest claiming files it did not land.

#### Scenario: send records the batch in the sent manifest
- **WHEN** `outbox send` commits a batch
- **THEN** the commit carries `SENT` with one `<sha256>  <name>` line
  per draft the batch carries, and a later `check` skips them without
  an index

#### Scenario: a manifest gained across batches appends
- **WHEN** a second `outbox send` commits over an existing `SENT`
- **THEN** the manifest keeps the earlier lines and adds one line per
  draft of the new batch

#### Scenario: a refused send leaves the manifest as it was
- **WHEN** `git commit` fails after the manifest was written
- **THEN** `SENT` holds the bytes it held before — or is absent when
  there was none — and no draft is skipped by it afterward
