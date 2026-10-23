## Why

ADR-0013 decision 14 and section F give `doctor` the overview of
extensions: what is installed and whether this machine approved it.
CR-152 and CR-158 parse manifests in both forms, and CR-209 keeps local
grants and computes whether a directory changed after approval — but
nothing puts the two together for a developer: `extension list` reports
the grant and nothing else, and `doctor` does not mention extensions at
all.

## What Changes

`agentmarshal doctor` gains an extensions section on stderr — beside the
paths and the overdue-step lines — printing one line per shared
extension found under `.agentmarshal/extensions/` of the working tree:
its name, its form (file or directory), its manifest schema, its stages
with their modes and its declared `ext` kinds. A directory-form
extension's line adds this clone's grant state — `granted`, `not
granted` or `changed after approval` naming the file — computed the way
`extension list` computes it. An extension whose manifest cannot be read
or validated is reported the way doctor reports its other malformed
project settings: a failed check of its own naming the reason, which
counts in the verdict and the exit status, while its section line names
the reason and the rest of doctor runs on. A project with no
`.agentmarshal/extensions/` directory gets one line saying there are no
extensions and unchanged output otherwise. The listing runs nothing an
extension declares and writes nothing.

## Capabilities

- modified: `extension-manifest`

## Impact

`src/agentmarshal/doctor.py`: one discovery helper shared by the new
checks and the report, one check per extension manifest, and the section
in the stderr report. The grant state calls the CR-209 computation in
`src/agentmarshal/extension_trust.py`, which is unchanged — as is every
other command. Dependencies against locks, runtimes, switches and the
personal scopes remain later tasks.
