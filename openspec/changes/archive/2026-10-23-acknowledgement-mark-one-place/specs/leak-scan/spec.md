## MODIFIED Requirements

### Requirement: `leak-scan` reads the journal's acknowledgements for the candidate

`agentmarshal leak-scan --base <ref> --commit <rev>` SHALL look up the
journal's `acknowledgement` records bound to the candidate: the records
whose `commit` equals the candidate's resolved commit — the full 40-hex
id `git rev-parse --verify <rev>^{commit}` gives in the repository the
scan reads. It SHALL read them from every task of the journal, or from
the one task an optional `--task <id>` names, where the gate reads
records: the calling checkout's working tree in the embedded placement,
the journal repository's working tree under a sidecar (ADR-0014). An
acknowledgement on a task that has since closed still counts — the
record binds the commit, not the task's state. A repository carrying no
journal has no records to find, and the command SHALL behave there
exactly as it does without acknowledgements. When the journal or a
task's records cannot be read — a task `--task` names that does not
exist, a record that fails validation, a journal that cannot be listed
— no hit SHALL count as acknowledged and the command SHALL say why on
stderr.

#### Scenario: the records are read from every task of the journal
- **WHEN** `leak-scan` runs without `--task` and `acknowledgement`
  records bound to the candidate sit on several tasks
- **THEN** each is read, and a hit any of them names counts as
  acknowledged

#### Scenario: --task reads the one task's records
- **WHEN** `leak-scan --task <id>` runs and an acknowledgement bound to
  the candidate sits on a different task
- **THEN** it is not read and the hit counts as unacknowledged; a
  record on the named task still counts

#### Scenario: a task that cannot be read acknowledges nothing
- **WHEN** `--task` names a task the journal does not carry, or one
  whose records fail reading
- **THEN** no hit counts as acknowledged and the command says why on
  stderr

#### Scenario: a journal that cannot be read acknowledges nothing
- **WHEN** reading the journal's tasks or a task's records fails
- **THEN** no hit counts as acknowledged and the command says why on
  stderr

#### Scenario: an acknowledgement on a closed task still counts
- **WHEN** the task carrying the acknowledgement has since completed or
  been abandoned
- **THEN** the record still acknowledges the hit it names — it binds
  the commit, not the task's state

#### Scenario: a repository with no journal behaves as without acknowledgements
- **WHEN** `leak-scan` runs in a git repository carrying no AgentMarshal
  journal
- **THEN** it prints and exits exactly as a run finding no
  acknowledgements does

#### Scenario: a sidecar's records are read in the journal repository
- **WHEN** `leak-scan` runs in a checkout whose placement is a sidecar
  and an `acknowledgement` record bound to the candidate sits on a task
  of the journal repository
- **THEN** the record is read from the journal repository's working
  tree while the candidate is resolved and scanned in the host, and
  the hit it names counts as acknowledged

### Requirement: an acknowledged hit stays printed and marked, and only an unacknowledged hit fails the command

Every hit the scan reports SHALL still be printed, in the order and
form it prints today, and an acknowledged hit's entry SHALL
additionally carry a mark naming who acknowledged it — the record's
`recorded_by` — and the `reason`, each masked by the scan — record
values are the operator's own text and can themselves carry the string
the scan matches — and each escaped on display as the other displayed
record values are. Nothing is removed, and the matched text is never
printed. The command SHALL exit 0 when the scan finds hits and every
one is acknowledged, SHALL exit 1 when any hit is unacknowledged, and
SHALL print and exit exactly as today when the scan finds nothing or
finds no acknowledgement. The mark the command prints is the mark the
merge boundary shows on the hits its bound lets its line show — the
same mark over the same naming, the one mark-builder the two surfaces
share (ADR-0021 decision 3).

#### Scenario: an acknowledged hit prints marked
- **WHEN** a hit is acknowledged
- **THEN** its printed entry additionally carries a mark naming who
  acknowledged it and the reason

#### Scenario: every hit still prints in today's order and form
- **WHEN** the scan reports hits of which some are acknowledged and
  some are not
- **THEN** every hit appears in the order and form it prints today, the
  acknowledged entries carrying the mark

#### Scenario: a recorder named the secret is masked in the mark
- **WHEN** the acknowledging record's `recorded_by` or `reason`
  carries a string the scan matches
- **THEN** the mark prints it masked, the way every printed name is

#### Scenario: the mark is escaped where it could forge a line
- **WHEN** the acknowledging record's `recorded_by` carries a character
  that could add a line to rendered output or reorder it
- **THEN** the mark prints each such character as its escape

#### Scenario: the matched text is never printed
- **WHEN** a hit is acknowledged
- **THEN** neither stdout nor stderr carries the matched text or a
  marker's value

#### Scenario: every hit acknowledged exits 0
- **WHEN** the scan reports hits and every one is acknowledged
- **THEN** the command exits 0

#### Scenario: any unacknowledged hit exits 1
- **WHEN** the scan reports a hit nobody has acknowledged
- **THEN** the command exits 1

#### Scenario: a clean scan is unchanged
- **WHEN** the scan reports no hits
- **THEN** the command prints and exits as it does without
  acknowledgements

#### Scenario: a run with no acknowledgement is byte for byte today's
- **WHEN** the scan reports hits and the journal holds no
  acknowledgement naming one
- **THEN** the hits print exactly as before, unmarked, and the command
  exits 1

#### Scenario: the merge boundary's line carries no mark yet
- **WHEN** the gate's added-content scan reports a hit no
  acknowledgement of the task names
- **THEN** its line prints the same file and identification the
  standalone command gives, and no mark

### Requirement: the gate marks an acknowledged hit on its leak-scan line

The gate's advisory leak-scan line SHALL mark each hit it shows that
an `acknowledgement` record of the task acknowledges — the record's
`commit` equal to the candidate's resolved commit, its `file` equal
to the hit's file exactly as the scan prints it, and its
identification equal to the hit's, where the record's `signature`
equals a signature hit's identification and `private-marker #<n>`
equals a marker hit's for the record's `marker` <n> — with the same
mark `leak-scan` prints on the hit — one mark-builder produces it for
the command and for the line, so the mark's wording, masking and
escaping cannot drift between the surfaces: acknowledged, who
acknowledged it (the record's `recorded_by`) and the `reason`, masked
with the scan's markers and escaped on display the same way (ADR-0021
decisions 2 and 3). There is no other matching: an acknowledgement
bound to another commit, carried on another task, spelled differently
in `file`, or naming another identification marks nothing, and where
several records of the task match one hit the earliest in journal
order marks it. A hit the line's bound does not show carries no mark:
the bound is unchanged — at most twenty hits, then "and N more not
shown" — and an acknowledgement neither removes a hit from the line
nor changes which hits are shown or their order. The line stays a
warning: a marked hit adds no violation. A candidate whose task holds
no acknowledgement bound to its commit produces the line byte for byte
as without the record.

#### Scenario: an acknowledged hit is marked on the gate's line
- **WHEN** the gate's added-content scan reports a hit an
  `acknowledgement` record of the task names on the candidate's
  commit
- **THEN** the hit's entry on the line carries a mark naming who
  acknowledged it and the reason

#### Scenario: the mark is the one the standalone command prints
- **WHEN** the gate's line and `agentmarshal leak-scan` report the
  same acknowledged hit
- **THEN** the mark on the line is the mark on the command's output —
  same wording, same masking, same escaping

#### Scenario: a marked hit adds no violation
- **WHEN** a hit on the gate's line is marked acknowledged
- **THEN** the line stays a warning and the hit blocks nothing

#### Scenario: the bound is unchanged and the unshown stay unmarked
- **WHEN** the scan reports more hits than the line shows and an
  acknowledgement names one of them
- **THEN** the line shows at most twenty hits and says how many it
  did not show — a named hit among the shown carries the mark, a
  named hit beyond them none

#### Scenario: an acknowledgement changes neither the hits shown nor their order
- **WHEN** the scan reports hits of which some are acknowledged and
  some are not
- **THEN** every hit appears in the order and form it does without
  the record, the acknowledged entries marked

#### Scenario: an acknowledgement bound to another commit marks nothing
- **WHEN** a record names the hit's file and identification but its
  `commit` is not the candidate's resolved commit
- **THEN** the hit prints unmarked

#### Scenario: an acknowledgement of another task marks nothing
- **WHEN** the acknowledgement bound to the candidate's commit sits
  on a different task than the one the gate runs on
- **THEN** the hit prints unmarked

#### Scenario: a file spelled differently marks nothing
- **WHEN** a record's `file` differs from the hit's file as the scan
  prints it
- **THEN** the hit prints unmarked

#### Scenario: an identification that is not the hit's marks nothing
- **WHEN** a record's `signature` or `marker` does not equal the
  hit's identification
- **THEN** the hit prints unmarked

#### Scenario: the earliest matching record marks the hit
- **WHEN** two `acknowledgement` records of the task both name the
  hit
- **THEN** the mark names the earlier record in journal order

#### Scenario: a recorder named the secret is masked in the mark
- **WHEN** the acknowledging record's `recorded_by` or `reason`
  carries a string the scan matches
- **THEN** the mark prints it masked, the way every printed name is

#### Scenario: the mark is escaped where it could forge a line
- **WHEN** the acknowledging record's `recorded_by` or `reason`
  carries a character that could add a line to rendered output or
  reorder it
- **THEN** the mark prints each such character as its escape

#### Scenario: a candidate with no acknowledgement is byte for byte today's
- **WHEN** the task holds no `acknowledgement` record bound to the
  candidate's commit
- **THEN** the line prints exactly as it does without one
