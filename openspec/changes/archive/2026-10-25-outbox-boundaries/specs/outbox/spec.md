# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
