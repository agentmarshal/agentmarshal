# Spec Delta

## Purpose

The upstream outbox holds an adopter's findings about the tool — one file
per finding, sent as a batch. This capability is the tool's side of that
convention: a command that scaffolds a conforming draft, and a check that
names what a draft lacks and what the leak scan finds before anything is
sent.

## ADDED Requirements

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
configuration — over the drafts' content, and SHALL name each hit by file
and by what matched: a built-in signature by its identifier, a configured
marker by its position. The matched text, a marker's value, and a name that
itself carries a secret SHALL appear nowhere in the output; such a name is
described the way the scan describes it. The command's exit status SHALL be
0 only when every draft conforms and the scan finds nothing, and non-zero
otherwise, so a batch wrapper can refuse to send.

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
