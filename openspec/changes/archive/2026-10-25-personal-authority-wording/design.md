# personal-authority-wording — Design

## Context

Release-audit finding AUD-extensions-1: the requirement's text promised
"a personal extension SHALL write no `ext` records — … — and nothing to
the journal" — a containment claim. The core enforces a narrower bound:
`record-ext` accepts only kinds a shared extension's manifest declares
(`record_ext._declared_kind` reads the shared manifest alone, so a
personal manifest's `[records]` entries never enter the accepted set),
a personal manifest is refused when it carries `footprint`, `documents`
or `artifacts` (`extension_trust.read_personal_manifest` checks the raw
table), no personal stage is planned in CI, and the gate reads nothing
an extension produces — so nothing a personal extension does reaches
the journal through the core or touches the server-side process. The
extension's own process, though, runs with the developer's rights:
docs/threat-model.md states that local state and the process log do not
resist a process running as the same OS user, and ADR-0013 decision 15
rests the local protection on the personal extension having no
authority, not on containing its process.

## Decision

The requirement keeps its heading byte for byte and every scenario, and
restates its text as the enforced bound plus the caveat: a SHALL for
each piece the core enforces — the accepted-kind set, the refused
manifest fields, no effect on the gate or the server-side process, the
`personal` scope on `extension-event`s — and a plain statement, citing
docs/threat-model.md, that the extension's process runs with the
developer's rights and is not contained beyond the stage isolation. No
SHALL promises that the process writes nothing to the journal: a
promise the enforcement cannot keep does not belong in the spec.

The kept scenarios still hold because they describe the run, not the
process: a run of personal stages appends no journal records and writes
only `extension-event`s to the process log.

The release notes get the same bound: "writes to no shared surface" and
"never reaches the shared journal or CI" become the no-write-path
statement plus the same-user caveat. Every other statement is
unchanged.

## Risks / Trade-offs

- "No effect on the gate" could still be over-read as containment; the
  same requirement's caveat bounds it — the gate takes nothing from an
  extension's run by construction (ADR-0013 decision 5), not by
  sandboxing the process.
