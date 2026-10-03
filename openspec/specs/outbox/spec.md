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
regular file except the `README.md` that `init` writes, which is not a
draft — and, for each draft that does not conform, SHALL name the file and
each field of the five that is missing or still unfilled: a field is
missing when the draft has no `## ` heading for it, and unfilled when its
body is empty or is the scaffold's placeholder unchanged. A draft that is
not UTF-8 text SHALL be named as such.

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
conforms, nothing in the outbox went unchecked and the scan finds
nothing, and non-zero otherwise, so a batch wrapper can refuse to send.

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

### Requirement: `outbox send` commits the checked batch

`agentmarshal outbox send` SHALL first run the check of the `outbox
check` requirements and SHALL refuse when it fails for any reason; it
SHALL refuse, saying there are no drafts to send, when the outbox holds
no finding draft — the README `init` writes is not a draft and a batch
of no drafts sends nothing. With the check passed, the command SHALL
refuse — naming each staged path — when anything outside
`.agentmarshal/upstream/` is already staged, so findings never ride
along in another commit and another commit's work never rides along in
the batch. Otherwise the command SHALL stage only
`.agentmarshal/upstream/` — the outbox README's exclude pathspec applied
the other way — SHALL refuse when nothing under the outbox is staged for
commit, and SHALL otherwise make exactly one commit of the batch with a
message naming the files, in the repository the outbox belongs to — in a
sidecar the journal repository, never the host — and SHALL print the
commit it made. If the commit fails after the batch was staged, the
command SHALL put back the index entries it staged under the outbox — a
refused send leaves the index as it found it. Every name the command
prints SHALL be masked and a name that is not UTF-8 SHALL be written in
escaped printable form, exactly as `outbox check` names files. The
command SHALL transmit nothing and SHALL open no network: delivery stays
with the operator.

#### Scenario: send refuses when the check fails
- **WHEN** a draft does not conform or the scan reports a hit
- **THEN** `outbox send` refuses and makes no commit

#### Scenario: send refuses when the outbox holds no drafts
- **WHEN** the outbox holds no finding draft — only the README `init`
  writes
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
prints SHALL be masked and a name that is not UTF-8 SHALL be written in
escaped printable form, exactly as `outbox check` names files. When
there is no outbox the command SHALL refuse with a message saying so.
The command SHALL open no network: the index is a file the operator
obtains and passes.

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
