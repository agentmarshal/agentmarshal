+++
schema = 1
id = "CR-090"
title = "Install OpenSpec 1.12.0 under a declared manifest: the first extension"
scope = [
  ".agentmarshal/extensions/openspec.toml",
  "openspec/",
  ".agents/skills/openspec-apply-change/",
  ".agents/skills/openspec-archive-change/",
  ".agents/skills/openspec-explore/",
  ".agents/skills/openspec-propose/",
  ".agents/skills/openspec-sync-specs/",
  ".agents/skills/openspec-update-change/",
  ".agents/skills/.openspec-target",
]
acceptance = [
  "a manifest exists at .agentmarshal/extensions/openspec.toml, schema 1, name openspec, version 1.12.0, whose footprint lists exactly the git-visible paths openspec init wrote — openspec/, the six .agents/skills/openspec-* directories and .agents/skills/.openspec-target — with documents openspec/specs/, artifacts openspec/changes/archive/, and the install and remove strings as they were run; the manifest reader accepts it",
  "the candidate adds what openspec init 1.12.0 writes into git-visible paths and the manifest, and nothing else: every changed path lies in the declared scope, and the gate's scope line carries no extensions clause, because an install task lists its paths rather than naming the extension (ADR-0010 D2)",
  "the Claude Code assets openspec init writes under .claude/ are gitignored in this repository and absent from the candidate; a comment in the manifest says so, and names them as machine-local",
  "openspec/config.yaml gains a context block of at most ten lines saying what this project is for the tool's prompts: Python 3.12 managed with uv, contracts under .agentmarshal/journal/tasks/, decisions under docs/adr/, and that every change lands through the AgentMarshal gate",
  "the recorded install string opts out of the tool's telemetry (OPENSPEC_TELEMETRY=0) and pins the version; no telemetry setting is committed",
  "no documentation file changes: what adopters are told about OpenSpec is the research task's outcome, not this task's",
]
+++

# CR-090: install OpenSpec under a declared manifest

## Context

ADR-0010 makes a third-party process tool's footprint scope and its manifest
the thing the gate reads. CR-088 and CR-089 built both sides. This is the
first extension installed under them, and the first data point of the
research task that pre-registered how the experiment is judged: the tool is
installed as it ships, its footprint is declared by hand, and the gate
checks the install as it checks any change.

`openspec init` was run on a scratch clone first to learn what it writes:
`openspec/` (config, empty specs and archive), six skills under
`.agents/skills/` with a marker file, and six commands plus six skills under
`.claude/` — which this repository ignores wholesale, so those assets are
local to the machine and never reach a diff.

## Objective

Land the manifest and the tool's git-visible scaffold as one reviewed
change, with the footprint declared exactly and the parts the gate cannot
see named as such.

## Acceptance Criteria

As in the header. The install string is what was run, with the version
pinned and telemetry opted out:

    OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.12.0 init --tools claude,codex --no-animation .

## Threat model and boundaries

Installing runs third-party code on the operator's machine; the manifest
records the invocation and AgentMarshal verifies nothing about it (ADR-0010
D6). The scaffold's files are prompts for agents; they are inlined into
nobody's context by this task, because no contract names the extension yet.

## Non-Goals

- Naming the extension in this contract: an install task lists its paths
  (ADR-0010 D2), and the extensions clause first appears on the next task.
- Any use of OpenSpec for a product change; that starts with the next task
  and is measured by the research protocol.
- Documentation for adopters, templates, or an `extension add` command.
- Committing anything under .claude/.
