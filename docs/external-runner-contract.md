# External runner contract

AgentMarshal core is a governance/process layer. It defines tasks, policy,
evidence and gates. It does not own a model runtime, queue, daemon, dashboard or
always-on dispatcher.

An external runner is anything that executes AgentMarshal work outside a live
model chat:

- a human coordinator;
- a CI job;
- a shell/Python script;
- a host-specific extension;
- a future standalone runner project.

For v0.1 cutoff the reference runner is manual: the coordinator runs commands,
waits for completion and records evidence.

## Boundary

AgentMarshal provides:

- task/review/event/stat schemas and conventions;
- role/profile/scope policy;
- deterministic scripts for validation, CI lookup, read-only review, triage,
  merge policy and task lifecycle;
- configured journal paths;
- provider adapters for host facts.

The runner provides:

- process scheduling;
- waiting for long-running commands;
- model invocation when a task explicitly requires it;
- artifact collection;
- notification to the operator;
- retry/cancel timing.

The runner must not bypass AgentMarshal policy. It supplies facts and artifacts;
AgentMarshal gates decide whether the workflow may advance.

## Request

Every runner request must be explicit enough to execute without chat context.

Required fields:

```text
Task: CR-NNN
Action: pipeline-wait|review-readonly|merge-check|followup-record|completion-check|custom
Target-SHA: <full sha or n/a>
Base-Ref: origin/master or n/a
MR: <id or n/a>
Provider: gitflic|github|gitlab|mock|host
Command: <exact AgentMarshal/host command or script entrypoint>
Expected-Artifacts:
  - <path>
Stop-Condition: <terminal status, exit code or artifact existence>
Resource-Tier: none|economy|standard|critical
Requested-By: <role/email/session>
```

The command may be a host script such as `infrastructure/scripts/mr.sh` when the
host owns that integration. The runner records it, but the command remains
outside AgentMarshal core.

## States

Runner state names are intentionally small:

```text
requested
running
succeeded
failed
cancelled
superseded
```

Only `succeeded` with matching artifacts can be used as positive evidence.
`failed`, `cancelled` and `superseded` require an event explaining the next
decision.

## Durable Event

For each completed runner action, write an event under the configured journal:

```text
.agents/events/YYYY/CR-NNN/<timestamp>-runner-<action>.md
```

Recommended event header:

```text
Task: CR-NNN
Runner-Mode: manual|ci|script|service
Runner-ID: <operator, job id or service id>
Action: <action>
State: succeeded|failed|cancelled|superseded
Target-SHA: <full sha or n/a>
Base-Ref: <ref or n/a>
MR: <id or n/a>
Started-At: <UTC timestamp>
Finished-At: <UTC timestamp>
Exit-Code: <integer or n/a>
Artifacts:
- <path>
```

The body should summarize what happened, what was verified and what remains
blocked. Do not include secrets or large logs; link artifact paths instead.

## Manual Coordinator Procedure

Use this process until an automated runner exists:

1. Ask the model/Lead for a runner request with exact fields.
2. End the model session or stop asking it to poll.
3. Run the requested command in a terminal or CI environment.
4. Save raw output in the configured `runs/` area when appropriate.
5. Write the runner event with exact SHA, command, result and artifacts.
6. Re-open a model session only to inspect recorded evidence and choose the next
   workflow step.

For example, the coordinator may run:

```bash
agentmarshal/scripts/gitflic-ci.sh wait <pipeline-id> 1800 15
```

Then record the pipeline result as an event and provide
`AGENTMARSHAL_PIPELINE_OK_SHA=<full-sha>` to merge-policy. The live model never
needs to wait for the loop.

## Future Runner Compatibility

A future automated runner should be able to replace the manual coordinator
without changing AgentMarshal core tasks:

- consume the same request fields;
- execute only allowlisted commands or provider actions;
- write the same event format;
- store raw artifacts in configured paths;
- report model/tool statistics through existing statistics scripts;
- leave merge/task state changes to AgentMarshal policy gates.

UI, desktop notifications and event-driven scheduling are separate products or
host extensions. They may build on this contract, but they are not part of the
v0.1 core cutoff.

## Learning Loop

The manual runner phase is also a discovery tool. Every non-trivial manual run
should record process observations in the durable event or a linked research
note:

- fields that were missing from the request;
- commands that were hard to express safely;
- artifacts that merge/review policy needed but the runner did not produce;
- where human judgement was required;
- whether the step should become a future automated runner feature, provider
  adapter capability or host-specific extension.

These observations inform a post-cutoff runner project. They do not expand
AgentMarshal v0.1 core scope.

Python may be used by a future runner or by a later rewrite of deterministic
core tools, but v0.1 does not require Python as a runtime dependency.
