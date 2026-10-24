# extension-stages Specification (delta)

## Purpose

The declared stages of shared extensions, invoked at the two lifecycle
points an extension may act — ADR-0013 section A, decisions 1, 2, 4, 5
and 7 — with the switches that take one out of the plan (decisions 16
and 17). `agentmarshal stage run --phase <pre-gate|post-gate> --task
<id> --commit <rev> --base <ref>` is a separate step beside the gate:
it reads each shared extension's manifest from the base commit — never
the candidate's tree and never the working tree — materializes the
extension's directory from that tree, and runs every `[[stage]]` whose
phase the invocation selects under the core's interpreter as an argv
process, in a snapshot of the candidate commit, bounded by the declared
`timeout_seconds` capped at the core's 600-second limit. On a
workstation a stage runs only under a local grant matching the
base-materialized contents (decision 14); in CI none is needed.
`.agentmarshal/switches.toml`, likewise read from the base, switches a
shared extension off with a mandatory reason: its stages report
`switched off` and do not run, the operational CR that set the switch
needed no review and ran no `pre-gate` stage of its own, and `status`
and `doctor` show the switch. Every stage gets exactly one result line
— `checked`, `failed (exit <n>)`, `did not finish (timeout)`, `switched
off (<task>, <reason>)` or `not run (<reason>)` — and its output a
frame that cannot read as one; each result appends an
`extension-event` to the process log (ADR-0022 section 7). The
isolation a manifest asks for is enforced where the platform allows —
a new user and network namespace unless `network = true`, the
`pre-gate` candidate bound read-only over itself, provider secrets
withheld at `pre-gate`, capabilities dropped before exec — and a
guarantee the core cannot enforce is named on a note line for the
stage, never silently weakened. A `pre-gate-stop` stage that failed,
did not finish or did not run pauses the process before the gate — the
command exits 3 — while a `pre-gate-warn` stage's failure is only a
loud warning and a `post-gate` stage's only a notification; an
`accepted_pause` acceptance naming the extension at the resolved commit
stands the pause down (decision 5, ADR-0022 section 2). `complete`
invokes the same run before its gate check — a pause refuses the
completion while the candidate is not yet merged into `--target` and
warns once it is — and again after the `completed` record as the
post-gate notification. Extensions cannot alter the gate's decisions:
the gate reads none of this and the command writes no journal.
