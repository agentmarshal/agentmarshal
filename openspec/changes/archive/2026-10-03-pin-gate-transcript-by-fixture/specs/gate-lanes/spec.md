## MODIFIED Requirements

### Requirement: A default run is unchanged
A gate run that does not request the mode SHALL produce the transcript it
produces today, byte for byte, in every placement and on every lane — the
transcript pinned by fixtures committed in the repository, one for each
case the pin covers. A run's stdout, stderr and exit status
SHALL each equal the fixture for its lane and placement, compared after one
substitution replaces the values that differ from run to run — commit
hashes, temporary paths, record ids, times — with named placeholders, so
the comparison is exact everywhere else. Any change to a fixture SHALL be
made, and named, by the task that changes the output: the fixture is
regenerated only when the test is explicitly asked to, and the fixture's
diff is part of that task's reviewed change.

#### Scenario: the pinned transcript still matches
- **WHEN** the gate runs without the mode on a candidate the pinned
  transcript fixtures cover — the implementation lane and the journal-only
  lane in the embedded placement; in the sidecar placement the
  implementation lane and the host candidate whose diff touches only the
  journal, whose fixture pins the refusal because the deterministic lane
  does not exist there (ADR-0008 decision 2)
- **THEN** its stdout, its stderr and its exit status equal the committed
  fixture once run-dependent values are replaced by named placeholders

#### Scenario: a transcript difference is shown, not hidden
- **WHEN** a gate run's transcript differs from the committed fixture for
  its lane and placement
- **THEN** the pinned test fails and shows the difference as a readable
  diff between fixture and run

#### Scenario: a fixture changes only when the output changes on purpose
- **WHEN** a task changes the gate's default output on purpose
- **THEN** that task regenerates the fixtures — which the test rewrites
  only when explicitly asked — and the change to each fixture is part of
  the task's reviewed change, naming the output change it makes
