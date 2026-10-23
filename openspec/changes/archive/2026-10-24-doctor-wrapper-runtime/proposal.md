## Why

ADR-0013 decision 13, as amended on 2026-10-03, names the one exception
to the `PATH` ban: the runtime a wrapped product needs — `node` for a
JavaScript product — which the manifest declares as `<name> >=
<version>` and the core finds on `PATH`, with `doctor` and the stage
output naming the path and version found. CR-152 parses
`[wraps].runtime`; CR-213 gave `doctor` its extensions section and a
check per manifest — but nothing yet answers the question a developer
needs before any stage runs: is the runtime a wrapper needs present,
and new enough?

## What Changes

For each shared extension whose manifest parses and declares
`[wraps].runtime`, `agentmarshal doctor` gains one check of its own,
`extension runtime <name>`, reported by doctor's existing rules — `OK` /
`FAIL` on stdout, counting in the verdict and the exit status. The check
resolves the declared `<name>` on `PATH` — the one `PATH` exception —
runs the resolved path with `--version` as an argv call, never through a
shell, under a short time limit, and reports the path found, the version
it reports and whether that meets the declared minimum. Versions compare
by their leading numeric dot-separated components, a leading `v`
ignored; output naming no readable version is reported unreadable rather
than guessed. A runtime not found on `PATH`, one that fails or does not
answer in time, one reporting an unreadable version and one below the
declared minimum each fail the check. An extension without `[wraps]`, or
whose manifest cannot be read, gains no runtime check, and a project
without wrappers keeps `doctor`'s output unchanged. The check runs
nothing else an extension declares and installs nothing.

## Capabilities

- modified: `extension-manifest`

## Impact

`src/agentmarshal/doctor.py`: `_extension_checks` reads each discovered
manifest once more to learn whether it declares `[wraps]`, and adds the
runtime check beside the manifest check; three small helpers parse a
`<name> >= <version>` requirement, read a version out of `--version`
output and compare components. The manifest parser, the grant state and
the stderr section are unchanged — as is every other command.
Dependencies against locks and the stage runner's own use of the runtime
remain later tasks.
