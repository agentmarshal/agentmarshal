# outbox Specification

## Purpose
The upstream outbox holds an adopter's findings about the tool — one file
per finding, sent as a batch. This capability is the tool's side of that
convention: a command that scaffolds a conforming draft, and a check that
names what a draft lacks and what the leak scan finds before anything is
sent.

## Requirements

### Requirement: `outbox new` scaffolds a finding draft

`agentmarshal outbox new "<gist>"` SHALL write one new draft into the
project's outbox — `.agentmarshal/upstream/` under the project root, the
directory `init` scaffolds beside `project.json` in either placement, so in
a sidecar the outbox is the journal repository's. The draft's name SHALL
carry the next free number and a slug of the gist; its body SHALL be
Markdown carrying the five fields of CONTRIBUTING's finding form —
Symptom, Measurements, Version, Environment, Expected — as `## ` headings,
with Version filled from the running tool and Environment filled from the
machine the command runs on (the OS and the Python version). The command
SHALL print the path it wrote, SHALL NOT overwrite an existing file, and
SHALL refuse with a message when there is no outbox.

#### Scenario: a draft is named with the next free number and a slug of the gist
- **WHEN** `outbox new "gate hangs on amend"` runs in an initialized project
- **THEN** a file `0001-gate-hangs-on-amend.md` exists under
  `.agentmarshal/upstream/`, and a second draft takes the next number

#### Scenario: a scaffolded draft carries the five fields with Version and Environment filled
- **WHEN** a draft is scaffolded
- **THEN** it carries `## ` headings Symptom, Measurements, Version,
  Environment and Expected; Version holds the running tool's
  `agentmarshal --version` output; Environment holds the machine's OS and
  Python version; and the other three hold the scaffold's placeholders

#### Scenario: new prints the path it wrote
- **WHEN** a draft is scaffolded
- **THEN** the command's output names the new file's path

#### Scenario: a second draft never overwrites the first
- **WHEN** `outbox new` runs again with the same gist
- **THEN** a second, differently numbered file exists and the first draft is
  unchanged

#### Scenario: new refuses when there is no outbox
- **WHEN** the project has no `.agentmarshal/upstream/` directory
- **THEN** the command fails with a message saying there is no outbox

#### Scenario: in a sidecar the draft lands in the journal repository's outbox
- **WHEN** `outbox new` runs in a project whose journal is a sidecar
- **THEN** the draft is written under the journal repository's
  `.agentmarshal/upstream/`, and nothing is written in the host

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

### Requirement: `outbox check` scans what would be sent and refuses by exit status

`outbox check` SHALL also run the leak scan the merge boundary uses —
the same signatures, and the private markers from the project's
configuration — over what would be sent: each draft's whole content, and
each entry's file name, which leaves with the batch, so a name carrying a
configured marker or matching a signature SHALL be a hit by itself.
Anything in the outbox that is not a regular file — a directory, a
symlink, a FIFO — is not a draft and cannot be checked: the command SHALL
name it as such, and nothing in the outbox passes in silence. Each hit
SHALL be named by file and by what matched: a built-in signature by its
identifier, a configured marker by its position. The matched text, a
marker's value, and a name that itself carries a secret SHALL appear
nowhere in the output; such a name is described the way the scan describes
it, every path the command prints goes through that masking, and an error
is described without the exception's path-carrying text. A file name that
is not UTF-8 SHALL be named in the escaped printable form the leak scan
uses for undecodable diff header lines — one `\xNN` escape per
undecodable byte — under that same masking, so no name can crash the
command. The command's exit status SHALL be 0 only when every draft
conforms, nothing in the outbox went unchecked, the scan finds
nothing and git could verify each checked file's staged bytes, and
non-zero otherwise, so a batch wrapper can refuse to send.

#### Scenario: a hit names the file and what matched, never the matched text
- **WHEN** a draft's content matches a built-in signature
- **THEN** the hit names the file and the signature's identifier, and the
  matched text appears nowhere in the output

#### Scenario: a configured private marker is named by position, not value
- **WHEN** a draft's content contains a configured private marker
- **THEN** the hit names the file and the marker's position, and the
  marker's value appears nowhere in the output

#### Scenario: a name that carries a secret is described, not printed
- **WHEN** the file a hit names — or a draft the check names — has a name
  containing a configured marker or matching a signature
- **THEN** the output names it by that marker's position or that
  signature's identifier, and the characters that matched appear nowhere
  in the output

#### Scenario: a draft that is not UTF-8 text is named and still searched
- **WHEN** a draft's bytes are not UTF-8 but a span of them matches a
  signature
- **THEN** the file is named as one that is not UTF-8 text, and the hit is
  reported

#### Scenario: conforming drafts with a clean scan exit 0
- **WHEN** every draft conforms and the scan finds nothing
- **THEN** the command exits 0

#### Scenario: a non-conforming draft fails the check even when nothing leaks
- **WHEN** a draft does not conform and the scan finds nothing
- **THEN** the command exits non-zero

#### Scenario: a leak fails the check even when every draft conforms
- **WHEN** every draft conforms and the scan reports a hit
- **THEN** the command exits non-zero

#### Scenario: a file name that carries a secret is a hit even with clean content
- **WHEN** a draft's file name contains a configured marker or matches a
  signature — the name leaves with the batch — and its content is clean
- **THEN** the check reports a hit naming the file by that marker's
  position or that signature's identifier, and exits non-zero

#### Scenario: an entry that is not a regular file is named as not checked
- **WHEN** the outbox holds a directory, a symlink or a FIFO — not a
  regular file, so not a draft — beside conforming drafts
- **THEN** the check names it as not a draft and not checked, and exits
  non-zero

#### Scenario: an unreadable draft is named without the error's path text
- **WHEN** a draft cannot be read and its name contains a configured
  marker
- **THEN** the check names it through the scan's masking and describes the
  error without the exception's path-carrying text

#### Scenario: a file name that is not UTF-8 is named escaped and still masked
- **WHEN** an outbox entry's name is not UTF-8 and carries a configured
  marker
- **THEN** the check names it with one `\xNN` escape per undecodable
  byte, the marker is masked in that escaped name, and the command does
  not crash

#### Scenario: check refuses when git cannot verify a file's staged bytes
- **WHEN** git cannot pin a checked file — `git hash-object` fails or
  cannot run
- **THEN** the check names the file and the reason — masked and
  display-escaped — and exits non-zero

### Requirement: `outbox send` commits the checked batch

`agentmarshal outbox send` SHALL first run the check of the `outbox
check` requirements and SHALL refuse when it fails for any reason; it
SHALL refuse, saying there are no drafts to send, when the outbox holds
no finding draft — the README `init` writes is not a draft and a batch
of no drafts sends nothing. With no draft the one committable batch is
the outbox's own record: `send` SHALL still commit when every change
the outbox holds is a rename or a move of a file already sent — a
staged `R` entry — or the sent manifest's update that follows one, at
least one rename among them; any other change with no draft — a
modified README, an untracked non-draft, a deletion, or the manifest
alone — SHALL refuse saying there are no drafts to send exactly as no
change at all does. With the check passed, the command SHALL
refuse — naming each staged path — when anything outside
`.agentmarshal/upstream/` is already staged, so findings never ride
along in another commit and another commit's work never rides along in
the batch. Otherwise the command SHALL stage only
`.agentmarshal/upstream/` — the outbox README's exclude pathspec applied
the other way, every file under it, a file an ignore rule names
included, since the check already vetted it — SHALL refuse when nothing
under the outbox is staged for commit, and SHALL otherwise make exactly
one commit of the batch with a message naming the files, in the
repository the outbox belongs to — in a sidecar the journal repository,
never the host — and SHALL print the commit it made. What is committed
SHALL be what was checked: before committing, the command SHALL verify
the staged blobs are the files the check vetted and SHALL refuse —
putting back what it staged — when they are not. If the commit fails
after the batch was staged, the command SHALL put back the index
entries it staged under the outbox — a refused send leaves the index as
it found it, and a made commit is never put back. Every name the
command prints SHALL be masked and a name that is not UTF-8 SHALL be
written in escaped printable form, exactly as `outbox check` names
files. The command SHALL transmit nothing and SHALL open no network:
delivery stays with the operator.

#### Scenario: send refuses when the check fails
- **WHEN** a draft does not conform or the scan reports a hit
- **THEN** `outbox send` refuses and makes no commit

#### Scenario: send refuses when the outbox holds no drafts
- **WHEN** the outbox holds no finding draft — only the README `init`
  writes
- **THEN** the command refuses saying there are no drafts to send, and
  commits nothing

#### Scenario: send refuses a non-rename change when the outbox holds no draft
- **WHEN** the outbox holds no finding draft and an outbox change is
  not a rename or a move of a file already sent — a modified README,
  an untracked non-draft, a deletion, the manifest alone
- **THEN** the command refuses saying there are no drafts to send, and
  commits nothing

#### Scenario: send refuses when something outside the outbox is staged
- **WHEN** a path outside `.agentmarshal/upstream/` is already staged
- **THEN** the command refuses, names the staged path, and commits nothing

#### Scenario: send makes exactly one commit of the batch and prints it
- **WHEN** conforming drafts sit in the outbox and nothing outside the
  outbox is staged
- **THEN** the command stages only `.agentmarshal/upstream/`, makes
  exactly one commit whose message names the batch's files, prints the
  commit, and leaves unstaged changes outside the outbox unstaged

#### Scenario: send refuses an empty batch
- **WHEN** the outbox's files are all committed and unchanged — nothing
  under the outbox would be staged for commit
- **THEN** the command refuses and makes no commit

#### Scenario: a failed commit leaves the index as send found it
- **WHEN** `git commit` fails — a hook refuses it — after the batch was
  staged
- **THEN** the command refuses, and the index holds nothing `send`
  staged: the outbox paths it added are unstaged and what was staged
  before stays staged

#### Scenario: in a sidecar the commit lands in the journal repository
- **WHEN** `outbox send` runs in a project whose journal is a sidecar
- **THEN** the commit lands in the journal repository's git history and
  the host repository gains no commit

#### Scenario: a gitignored draft is checked and sent like every file
- **WHEN** an ignore rule names a draft in the outbox and the check
  passes
- **THEN** the command stages it and it leaves with the batch

#### Scenario: send refuses when a draft changed since the check
- **WHEN** a draft's content changed after the check but before the
  commit
- **THEN** the command refuses, puts back what it staged, and commits
  nothing

#### Scenario: a made commit is never put back
- **WHEN** `git commit` succeeded and only naming the commit fails
- **THEN** the command reports the failure and leaves the commit and the
  index as the commit left them

#### Scenario: a file whose name is not UTF-8 is sent under its escaped name
- **WHEN** the outbox holds a conforming draft whose name is not UTF-8
- **THEN** the check and the send name it in escaped printable form and
  the send commits it without crashing

### Requirement: `outbox status` reports which findings an index file claims

`agentmarshal outbox status --index <file>` SHALL read the index file
the operator names and SHALL refuse with a message when it is missing or
unreadable. From the index the command SHALL take every `Source:` line —
the bare form `Source: sha256:<64 hex>` as much as the markdown-decorated
form `**Source:** \`sha256:<64 hex>\`` a published digest carries — each
occurrence an index entry identified by its digest, the line or lines it
sits on kept for the report. The command SHALL hash each file in the
outbox — the sha256 of the file's bytes, lowercase hex — SHALL print for
each outbox file whether an index entry claims it and which, and SHALL
print each index entry that claims no outbox file — once per distinct
digest, naming the line or lines it sits on. An entry that is not a
regular file, and a file that cannot be read, SHALL be named as not
hashed and SHALL make the command exit non-zero. Every name the command
prints SHALL be masked and written in display-escaped printable form,
exactly as `outbox check` names files, so no printed name can add a
line to the report. When there is no outbox the command SHALL refuse
with a message saying so. The command SHALL open no network: the index
is a file the operator obtains and passes.

#### Scenario: a file the index claims is named with the entry claiming it
- **WHEN** an outbox file's hash appears on a `Source:` line of the index
- **THEN** the report names the file and the index line claiming it

#### Scenario: a file no entry claims is reported unclaimed
- **WHEN** no `Source:` line matches an outbox file's hash
- **THEN** the report says no index entry claims it

#### Scenario: index entries matching no file are listed
- **WHEN** the index holds a `Source:` line matching no outbox file
- **THEN** the report names that index entry

#### Scenario: two digests on one index line are two entries
- **WHEN** one index line carries two `Source:` digests and one matches
  an outbox file
- **THEN** the file is claimed by the matching entry, and the other
  digest is still listed as claiming no outbox file

#### Scenario: a digest on several index lines is listed once
- **WHEN** the same digest appears on several `Source:` lines and
  matches no outbox file
- **THEN** the report names it once, with the lines it sits on

#### Scenario: the markdown-decorated Source line is parsed like the bare one
- **WHEN** the index carries `**Source:** \`sha256:<64 hex>\``
- **THEN** the entry claims the matching outbox file exactly as the bare
  form does

#### Scenario: status refuses a missing or unreadable index
- **WHEN** the `--index` path names no readable file
- **THEN** the command refuses with a message

#### Scenario: an entry that is not a regular file is named as not hashed
- **WHEN** the outbox holds a directory, a symlink or a FIFO — not a
  regular file — beside regular files
- **THEN** the report names it as not hashed and the command exits
  non-zero

#### Scenario: a name that is not UTF-8 is printed escaped under the masking
- **WHEN** the outbox holds a file whose name is not UTF-8 and carries a
  configured marker
- **THEN** the report names it in escaped printable form, the marker is
  masked in that escaped name, and the command does not crash

#### Scenario: status refuses when there is no outbox
- **WHEN** the project has no `.agentmarshal/upstream/` directory
- **THEN** the command fails with a message saying there is no outbox

#### Scenario: a control character in a file name is escaped in the report
- **WHEN** the outbox holds a file whose name carries a control
  character
- **THEN** `status` prints the name with the character as an escape,
  never the raw character

### Requirement: `outbox check` and `outbox send` skip files already sent

`agentmarshal outbox check` and `agentmarshal outbox send` SHALL take an
optional `--index <file>` — the same index file `outbox status` parses —
and SHALL treat as already sent, and not check, a regular file whose
sha256 is listed in the outbox's sent manifest — the file `SENT` in the
outbox — or claimed by a `Source:` line of the index when `--index` is
given. The manifest is the tool's record of what was sent — bookkeeping
the outbox keeps beside the findings, not a finding itself — and it is
parsed strictly: one `<sha256>  <name>` line each, 64 lowercase hex
digits, exactly two spaces, a name free of the characters that could
add a line. A line in any other shape does not parse — a wrong form,
a name the record-text rules refuse, a carriage return, a line that
does not decode as UTF-8 — and no such line is dropped in silence:
each command SHALL refuse and SHALL print one line naming the
manifest and the line's number. A skipped file is
still read and still goes through the leak scan — it leaves with the
batch like every file — it is only not judged as a draft; and it is
never the manifest or the README, which are not drafts either. Each
command SHALL print one line `skipped as sent: <n>` when it skipped
any, so skipping is never silent. A file whose name a manifest line
carries beside a different sha256 is not skipped — its bytes changed
since it was sent — so it is checked like a draft and the check SHALL
name it as changed after sending: an annotation, not a refusal. A
regular file whose name could add a line to the manifest — a newline
or another character a line of text cannot hold — SHALL be named in
escaped printable form and refused: such a name is never written to
`SENT`. When `send` finds no new draft it SHALL still commit a change
the outbox holds to a file already sent — a rename, a move inside the
outbox, a staged `R` entry — as the outbox-only commit it is
(ADR-0020 decision 6: the exclude pathspec keeps findings out of
journal commits), the message naming both paths of a rename, and the
manifest SHALL follow the new name — the line that claims the file's
sha256 takes the name the file now carries — so the renamed file
stays skipped. It is also the only such batch: with no draft, every
change the outbox holds must be one — a modified README, an untracked
non-draft, a deletion, a pure addition of a skipped file the
repository never held, and the manifest alone are not — or `send`
SHALL refuse saying there are no drafts to send.

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
  draft — and the outbox holds no change to one of them
- **THEN** `outbox send` refuses saying there are no drafts to send, and
  commits nothing

#### Scenario: send commits a rename of a file already sent
- **WHEN** the outbox holds no new draft but a file a `SENT` line
  claims was renamed inside the outbox
- **THEN** `outbox send` stages only the outbox and commits the change
  in one commit whose message names both paths of the rename, and the
  manifest line follows the new name so a later `check` still skips
  the file

#### Scenario: a manifest line that does not parse refuses the check
- **WHEN** a `SENT` line is not exactly `<64 lowercase hex>  <name>`
  with a name free of line-forging characters — one space, an
  uppercase digest, a control character in the name, a carriage
  return, a line that does not decode as UTF-8
- **THEN** the check refuses and prints one line naming the manifest
  and the line's number

#### Scenario: a file whose name could add a line to the manifest is refused
- **WHEN** a regular file in the outbox has a name carrying a newline or
  another control character
- **THEN** the check names it in escaped printable form and refuses, and
  `send` writes no manifest line for it

### Requirement: `outbox send` records the batch in the sent manifest

`agentmarshal outbox send` SHALL add to the outbox's sent manifest, in
the same batch commit as the drafts it sends, the sha256 of each draft
the batch carries — one `<sha256>  <name>` line each, appended to the
lines the manifest already holds — so a later `check` skips them
without an index. The manifest update SHALL be pinned by the same
checked bytes as every file the batch carries: the content committed is
the content the passing check computed, staged under
`.agentmarshal/upstream/SENT` and verified against the staged blobs
like every pinned path — and the leak scan SHALL cover those same
bytes: the manifest's next content is scanned like every file the batch
carries, and a hit refuses the run before `send` stages a byte. A batch
that would stage only the manifest is
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

#### Scenario: the manifest's next content goes through the leak scan
- **WHEN** a draft's name makes the manifest's next content match a
  signature — the name trips nothing alone but does beside the line
  break
- **THEN** the check reports the hit on `SENT` and refuses, and `send`
  stages nothing

### Requirement: the outbox refuses a symbolic link in its path

Every `outbox` subcommand SHALL refuse — one line naming the path,
printed with the masking every outbox path gets, before creating or
writing anything — when `.agentmarshal/upstream` or a component between
it and the project root is a symbolic link, so a sidecar's outbox
linked into its host never writes the host; `init`'s outbox scaffold
SHALL refuse the same.

#### Scenario: a linked outbox refuses a command before it writes
- **WHEN** `.agentmarshal/upstream` is a symbolic link
- **THEN** `outbox new`, `outbox check`, `outbox send` and `outbox
  status` each refuse with one line naming the link, and nothing is
  written or committed

#### Scenario: a linked .agentmarshal component refuses the command
- **WHEN** `.agentmarshal` itself is a symbolic link
- **THEN** the command refuses with one line naming that component

#### Scenario: the refusal line names the linked component masked
- **WHEN** a directory on the outbox's path carries a configured marker
  and a component in the path is a symbolic link
- **THEN** the refusal names the component with the marker masked,
  never the raw characters

#### Scenario: init never scaffolds through a linked outbox
- **WHEN** `init` finds `.agentmarshal/upstream` a symbolic link
- **THEN** it writes nothing through the link and reports the refusal
  on one line naming the path

### Requirement: `outbox check` and `outbox send` refuse a file git would transform

`outbox check` SHALL refuse, naming the file and the remedy, when the
blob id a file stages as — its path's attributes applied — differs
from the blob id of the bytes it read: for end-of-line conversion the
remedy is `.agentmarshal/upstream/** -text` in .gitattributes, or
committing the file with the bytes git stages; for a clean filter, the
filter must not apply to the outbox. `send` runs the same check; the
sent manifest's update is held to it.

#### Scenario: check refuses a draft a clean filter would transform
- **WHEN** a `.gitattributes` clean filter would rewrite a draft's
  bytes on staging
- **THEN** `outbox check` refuses, names the file, and says the filter
  must not apply to the outbox

#### Scenario: an end-of-line refusal names the attribute that turns it off
- **WHEN** `core.autocrlf` or a `text`/`eol` attribute would rewrite a
  draft's bytes on staging
- **THEN** the refusal names the file and says
  `.agentmarshal/upstream/** -text` in .gitattributes — or committing
  the file with the bytes git stages — makes the bytes match

#### Scenario: send refuses a draft a clean filter would transform
- **WHEN** a `.gitattributes` clean filter would rewrite a draft's
  bytes on staging
- **THEN** `outbox send` refuses naming the file and commits nothing

#### Scenario: send refuses when a filter would transform the sent manifest
- **WHEN** an attribute would rewrite the manifest content `send`
  stages under `SENT`
- **THEN** the send refuses naming `SENT` and stages nothing
