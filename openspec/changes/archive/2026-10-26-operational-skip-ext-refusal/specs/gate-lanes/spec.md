# gate-lanes Specification (delta)

## Purpose

The operational-lane requirement said the pre-gate stage run prints one
line and returns success — which placed the lane's exception ahead of
the `--skip-ext` refusal a shared name draws on every other lane: on a
candidate the operational lane admits, `stage run --phase pre-gate
--skip-ext <shared>` printed the operational line and exited 0. The
exception now follows the refusal, decided on the names the base's
`extensions/` enumerates with no manifest read, exactly as the code
does.

## MODIFIED Requirements

### Requirement: pre-gate stages do not run on an operational change

The `--skip-ext` refusal of a shared name precedes this lane's
exception — decided on the names the merge base's
`.agentmarshal/extensions/` enumerates with no manifest read, as "a
shared extension is never named in a personal switch" states — and
only then does the exception apply: `stage run --phase pre-gate` on a
candidate the gate's own predicate qualifies for the operational lane
SHALL print one line saying pre-gate stages do not run on an
operational change and SHALL run no stage — no extension event, no
pause — returning success. The decision SHALL come from the same
function the gate uses, imported rather than copied. Every other phase
and every other candidate SHALL behave as today.

#### Scenario: pre-gate stages do not run on an operational change

- **WHEN** `stage run --phase pre-gate` is asked on a candidate taking
  the operational lane — one whose switched-off extension's
  `pre-gate-stop` stage would otherwise pause
- **THEN** the command prints one line saying pre-gate stages do not
  run on an operational change, runs no stage and exits 0

#### Scenario: other phases and other candidates behave as today

- **WHEN** `stage run` is asked for `post-gate` on an operational
  candidate, or for `pre-gate` on a candidate that is not operational
- **THEN** it behaves exactly as it does today — the post-gate stage
  runs, and the other candidate's pre-gate stages run

#### Scenario: a shared name in --skip-ext is refused before the operational-lane exception

- **WHEN** `stage run --phase pre-gate --skip-ext <name>` names a
  shared extension on a candidate the gate's operational lane admits
- **THEN** the run refuses with the shared-name refusal line — the
  operational line does not print, no manifest is read and no stage is
  planned
