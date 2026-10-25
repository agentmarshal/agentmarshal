# leak-scan Specification (delta)

## ADDED Requirements

### Requirement: the acknowledgement mark identifies a self-acknowledgement
Where an acknowledgement's acknowledging party is a declared author or
committer of the commit `leak-scan` scans — of any commit in the
candidate range for the gate — the mark SHALL say `self-acknowledged`,
the term `status` uses. Any other acknowledgement, and a check git
cannot answer, SHALL print exactly as today (ADR-0021 decision 5).

#### Scenario: the standalone command marks a self-acknowledgement
- **WHEN** an acknowledgement bound to the scanned commit records a
  party that is a declared author or committer of that commit
- **THEN** the hit's mark reads `self-acknowledged by <recorded_by>:
  <reason>`

#### Scenario: the gate marks a self-acknowledgement over the candidate range
- **WHEN** an acknowledgement bound to the candidate records a party
  that is a declared writer of a commit in the candidate range
- **THEN** the gate's advisory line marks the hit `self-acknowledged`

#### Scenario: the commit's committer marks a self-acknowledgement
- **WHEN** the acknowledging party matches the scanned commit's
  declared committer and not its author
- **THEN** the mark says `self-acknowledged`

#### Scenario: a declared actor's resolved identity marks a self-acknowledgement
- **WHEN** the acknowledging party is a declared actor whose git
  identities include a declared writer of the scanned commit
- **THEN** the mark says `self-acknowledged` — the actor's resolved
  identities are compared, not only the recorded name

#### Scenario: a writer of an earlier range commit marks at the gate alone
- **WHEN** the acknowledging party is a declared writer of an earlier
  commit of the candidate range but not of the candidate the record
  binds
- **THEN** the gate's line says `self-acknowledged` and the standalone
  command's mark on that commit does not — it compares against the
  scanned commit's writers alone

#### Scenario: an acknowledgement by another party prints unmarked
- **WHEN** the acknowledging party is no declared writer
- **THEN** both surfaces print the mark exactly as today —
  `acknowledged by`, never `self-acknowledged`

#### Scenario: a check git cannot answer marks nothing
- **WHEN** the writer lookup cannot answer for the commit or the range
- **THEN** the mark prints as for any other acknowledgement — only a
  confirmed self-acknowledgement is marked, and `status` alone says the
  check did not run

#### Scenario: the writer check folds case
- **WHEN** the acknowledging party matches a declared writer only
  under case folding
- **THEN** the mark says `self-acknowledged`

## MODIFIED Requirements

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
same mark text, produced by the one mark-builder the two surfaces
share (ADR-0021 decision 3). The `self-acknowledged` qualification
alone is judged over different writer sets on the two surfaces — the
merge boundary over the candidate range, the command over the commit
it scans — so where the acknowledging party wrote only an earlier
commit of the range the two marks read differently, a difference
stated here and not hidden (ADR-0021 decision 5).

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
decisions 2 and 3). The mark's `self-acknowledged` qualification is
the one judgement the two surfaces make over different writer sets —
the line over the candidate range's writers, the command over the
scanned commit's — so where the acknowledging party wrote only an
earlier commit of the range the line marks `self-acknowledged` and
the command does not: the difference is stated here, not hidden
(ADR-0021 decision 5). There is no other matching: an acknowledgement
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
- **THEN** the mark on the line and the mark on the command's output
  come from the one mark-builder — same wording, same masking, same
  escaping; only the `self-acknowledged` qualification can differ
  between them, judged over the candidate range on the line and the
  scanned commit on the command

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
