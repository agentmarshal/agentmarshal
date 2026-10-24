# extension-stages Specification (delta)

## ADDED Requirements

### Requirement: the stage run is one function both commands call

The run `stage run` performs SHALL be one function —
`stages.run_stages` — taking the resolved placement, the clone's local
state, the task id, the commit, the base, the phase and stderr
explicitly, never a parsed-arguments namespace, and returning a small
result: `status`, the exit status the invocation ends with (0, 1 when
the run's own machinery refused it, 3 when a `pre-gate-stop` stage
paused); `pauses`, the `pre-gate-stop` stages that paused as
`<name>: <result>` entries in run order, unprinted; and `plan_empty`,
whether the run reached the plan and the phase matched no stage. Every
line the other requirements pin SHALL be printed by the runner except
the per-entry pause lines and the no-stage line, which the caller
renders: `stage run`'s wrapper SHALL print
`stage run: the process is paused before the gate — <entry>` per pause
and `stage run: no shared extension declares a <phase> stage` on an
empty plan, so the command's output and exit statuses are unchanged
byte for byte.

#### Scenario: stage run's transcript is unchanged by the shared runner
- **WHEN** `stage run` runs stages to a pause — or matches no stage
- **THEN** the pause lines read `stage run: the process is paused
  before the gate — <entry>` and the exit is 3, and the empty run
  prints `stage run: no shared extension declares a <phase> stage` —
  as before the runner was shared

#### Scenario: both commands go through the one runner
- **WHEN** `stage run` runs and `complete --task --commit --base`
  completes a candidate
- **THEN** each invocation is a call to `stages.run_stages` — complete
  calls it once for `pre-gate` and, after the `completed` record, once
  for `post-gate`

### Requirement: `complete` runs the `pre-gate` stages before its gate check

`agentmarshal complete --task <id> --commit <rev> --base <ref>` in the
embedded placement SHALL invoke `run_stages` for `pre-gate` with the
same task, commit and base — after the task's open state is
established, so a closed task's refusal still precedes any extension
work, and before the gate is evaluated and before anything is written
(ADR-0013 decision 2). The run's own lines keep the `stage run`
voice — the stage output frames, result lines, notes and warnings
print exactly as `stage run` prints them; the pause lines are the
pause requirement's to render. A run whose own machinery refused —
the exit-1 outcome — SHALL refuse the completion on one `complete:`
line with the same status, writing nothing. A plan matching no stage
SHALL print nothing — a project whose shared extensions declare no
`pre-gate` stage reads exactly as `complete` reads today. The findings
lane (`complete --findings`, which takes no candidate) and the sidecar
placement SHALL invoke no stage at all.

#### Scenario: the pre-gate stages run before the gate's transcript and before any write
- **WHEN** `complete` runs in a project whose base declares a
  `pre-gate` stage
- **THEN** the stage's lines precede the gate's transcript on stdout,
  and a run that ends in a refusal writes nothing

#### Scenario: a run whose machinery refused refuses the completion
- **WHEN** the `pre-gate` run's own machinery refuses — a manifest the
  base cannot parse, a trust file that cannot be read
- **THEN** `complete` prints one `complete:` refusal line, exits with
  the run's status and writes nothing

#### Scenario: a plan matching no stage prints nothing
- **WHEN** `complete` runs in a project whose shared extensions declare
  no `pre-gate` stage — or none at all
- **THEN** stdout and stderr read exactly as `complete` reads today —
  no stage line, no no-stage line

#### Scenario: an operational change's completion skips the pre-gate stages
- **WHEN** `complete` runs on a candidate the gate's operational lane
  admits — a switches-only diff under a contract scoping exactly
  `.agentmarshal/switches.toml`
- **THEN** the invocation prints the operational line, runs no stage
  and the completion proceeds — a broken extension cannot block its
  own switching off

#### Scenario: the findings lane invokes no stage
- **WHEN** `complete --findings` runs in a project whose base declares
  stages
- **THEN** no stage runs, no stage line prints and no extension event
  is written

#### Scenario: a sidecar invokes no stage
- **WHEN** `complete` runs where the journal placement is a sidecar
- **THEN** no stage runs at either point — the advisory completion
  reads as it reads today

#### Scenario: the stage's environment is the resolved candidate's
- **WHEN** `complete` runs a `pre-gate` stage for
  `--commit <ref> --base <ref>`
- **THEN** the stage's environment carries `AGENTMARSHAL_PHASE`
  `pre-gate`, `AGENTMARSHAL_TASK` the task, `AGENTMARSHAL_COMMIT` the
  resolved candidate commit and `AGENTMARSHAL_BASE` the resolved merge
  base — the runner resolves them inside exactly as `stage run` does —
  and its working directory is a snapshot of the resolved candidate

### Requirement: a `pre-gate-stop` pause refuses `complete` only while the candidate is not merged

When the `pre-gate` run pauses — the exit-3 outcome — `complete`
SHALL decide whether the candidate is already merged:
`git merge-base --is-ancestor` of the resolved candidate into the
resolved base, in the journal's repository, the references resolved to
commits exactly as the gate resolves them; a check that cannot answer
SHALL read as not merged — the pause stands rather than being silently
lifted. While the candidate is not an ancestor of the resolved base,
the completion SHALL be refused: the stage lines stand as printed, one
stderr line — `complete: the completion is paused before the gate —
<entry>; …` — names every paused stage's result in run order, nothing
is written and the exit status is the pause's own, 3. Once the
candidate is an ancestor of the resolved base, each pause SHALL instead
be reported on one stderr line — `complete: WARNING: extension at
pre-gate-stop — <entry> — the candidate is already merged into the
base` — and the completion SHALL proceed to the gate. An accepted
pause stands down in `complete` exactly as `stage run` reads it — the
runner's own reading of the task's acceptances, not a second one.

#### Scenario: a pause while the candidate is not an ancestor refuses the completion
- **WHEN** a `pre-gate-stop` stage pauses and the candidate is not an
  ancestor of the resolved base
- **THEN** the stage lines print, one stderr line says the completion
  is paused before the gate naming the paused stage's result, nothing
  is written and `complete` exits 3 — the pause status `stage run`
  uses

#### Scenario: the pause line names every paused stage
- **WHEN** two `pre-gate-stop` stages pause on an unmerged candidate
- **THEN** the one refusal line names both `<name>: <result>` entries
  in run order

#### Scenario: a pause on an already-merged candidate is a warning
- **WHEN** a `pre-gate-stop` stage pauses and the candidate is an
  ancestor of the resolved base
- **THEN** one `complete: WARNING:` line per paused stage names it and
  says the pause does not apply, no pause line is printed and the
  completion proceeds to the gate

#### Scenario: an accepted pause stands down in complete as in stage run
- **WHEN** a `pre-gate-stop` stage pauses and the task holds an
  acceptance carrying `accepted_pause` naming the extension and
  `accepted_commit` equal to the resolved candidate
- **THEN** the result line carries the `pause accepted by` suffix, no
  pause line and no warning is printed, and the completion proceeds

### Requirement: `complete` runs the `post-gate` stages after `completed` is written

Once `complete` has written the `completed` record — and after
`complete`'s own output — it SHALL invoke the same `run_stages` for
`post-gate` with the same task, commit and base. The run is a
notification (ADR-0013 decision 4): its outcome SHALL change neither
the record nor the exit status. A completion that wrote nothing — a
refused gate, a standing pause — SHALL not invoke it.

#### Scenario: the post-gate stages run after the completed record is written
- **WHEN** `complete` succeeds in a project whose base declares a
  `post-gate` stage
- **THEN** the stage's lines follow `complete`'s own output, and its
  `extension-event` lands in the process log

#### Scenario: a post-gate result changes neither the record nor the exit status
- **WHEN** a `post-gate` stage fails or does not run
- **THEN** `complete` still exits 0, the `completed` record stands and
  the stage's result line prints as the notification it is
