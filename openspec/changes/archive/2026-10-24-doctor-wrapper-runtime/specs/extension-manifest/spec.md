## ADDED Requirements

### Requirement: `doctor` checks the runtime a wrapper declares

For each shared extension whose manifest parses and declares
`[wraps].runtime` — the `<name> >= <version>` form, a declared
minimum — `doctor` SHALL run one check of its own,
`extension runtime <name>`, which resolves the declared `<name>` on
`PATH` — the one `PATH` exception of ADR-0013 decision 13 as
amended — runs the resolved path with `--version` as an argv call,
never through a shell, under a short time limit, and reports the
path found, the version it reports and whether that meets the
declared minimum. Versions SHALL be compared by their leading
numeric dot-separated components — a leading `v` ignored, a missing
trailing component reading as zero — and output naming no readable
version SHALL be reported as unreadable rather than guessed. A
runtime not found on `PATH`, one whose invocation fails, one that
does not answer in time, one reporting an unreadable version and
one below the declared minimum SHALL each fail the check — the
failure counting in the verdict and the exit status by `doctor`'s
existing rules for a failed check. Every value a result names —
the path found, the version reported, the declared requirement —
SHALL be escaped on display; the check SHALL run nothing else an
extension declares and SHALL install nothing.

#### Scenario: a wrapper's runtime that meets the declared minimum passes
- **WHEN** a shared extension's manifest declares
  `runtime = "node >= 20"` and `node` resolves on `PATH` reporting
  `v20.11.0`
- **THEN** the `extension runtime` check passes, naming the path
  found, the version reported and the requirement it meets

#### Scenario: versions compare by leading numeric components, a leading v ignored
- **WHEN** the manifest declares `runtime = "node >= 20"` and the
  runtime reports `v9.11.0`
- **THEN** the check fails below the minimum — 9 is less than 20
  numerically though the texts compare otherwise — and the leading
  `v` played no part

#### Scenario: a runtime not found on PATH fails the check
- **WHEN** the declared `<name>` resolves nowhere on `PATH`
- **THEN** the check fails naming the runtime and the declared
  requirement

#### Scenario: a runtime whose --version fails fails the check
- **WHEN** the resolved path's `--version` exits non-zero
- **THEN** the check fails naming the path and the exit status

#### Scenario: a runtime that does not answer in time fails the check
- **WHEN** `--version` does not return within the time limit
- **THEN** the check fails naming the path and the limit

#### Scenario: a runtime reporting no readable version fails the check
- **WHEN** the `--version` output names no numeric version or
  cannot be decoded
- **THEN** the check fails reporting the version unreadable rather
  than guessed

#### Scenario: a runtime below the declared minimum fails the check
- **WHEN** the manifest declares `runtime = "node >= 20"` and the
  runtime reports `v18.19.0`
- **THEN** the check fails naming the reported version and the
  declared minimum

#### Scenario: each value a runtime result names is escaped on display
- **WHEN** a value a runtime result names — the resolved path,
  say — carries a character the forgeable-text rule refuses
- **THEN** the value prints escaped

#### Scenario: the check runs nothing else an extension declares and installs nothing
- **WHEN** a wrapper's `bin/` holds a runnable file and `doctor`
  runs the runtime check
- **THEN** only the declared runtime's `--version` is invoked — no
  `[[stage]]` `command` runs and nothing is installed

### Requirement: a wrapper adds a runtime check only while its manifest declares `[wraps]`

An extension whose manifest declares no `[wraps]` SHALL gain no
runtime check and no runtime line; an extension whose manifest
cannot be read SHALL gain none either — the manifest's own check
already reports the reason — and a project holding no wrapper SHALL
keep `doctor`'s output unchanged: the same checks, the same
verdict.

#### Scenario: each wrapper gets its own runtime check
- **WHEN** two shared extensions declare `[wraps]` with different
  runtimes
- **THEN** each gains one `extension runtime <name>` check

#### Scenario: an extension without wraps gets no runtime line
- **WHEN** a shared extension's manifest declares no `[wraps]`
- **THEN** no `extension runtime` line prints for it

#### Scenario: an unreadable manifest adds no runtime check
- **WHEN** a shared extension's manifest cannot be read
- **THEN** the `extension manifest <name>` check reports the
  reason and no `extension runtime` line prints

#### Scenario: a project without wrappers prints doctor's output unchanged
- **WHEN** `doctor` runs in a project whose extensions declare no
  `[wraps]`, or holding none
- **THEN** the check report and the verdict print as they would
  without the change
