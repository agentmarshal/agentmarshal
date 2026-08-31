# Harness setup for the AgentMarshal rails

AgentMarshal drives its rails through a coding harness (Claude Code,
Codex CLI, …). Harness permissions do not change how AgentMarshal runs;
they only control whether the harness stops to ask before a routine command.
This guide captures a low-friction starting configuration. No permission
setting described here is required by AgentMarshal.

## Why this matters

The rails are a sequence of ordinary commands: `git`, the framework
scripts, your project's test and lint commands. If the harness prompts
for each one, an unattended or fast interactive run stalls waiting for a
human. The fix is a small, explicit allowlist of the command families
the rails actually use — not blanket permission, which gives up the
harness's safety.

## What does not depend on the harness

Three parts of operating the rails are AgentMarshal rules rather than harness
configuration:

1. **Declare the agent.** Set `AGENTMARSHAL_ACTOR` in the agent's session
   environment. Otherwise records made by an agent that uses the human's git
   identity conflate the agent with that human.

2. **Deliver the contract with `agentmarshal brief`.** Give the implementer the
   output of `agentmarshal brief --task <task-id>`; this is the only contract
   delivery AgentMarshal provides.

3. **Never let the agent write the journal.** The agent must not hand-edit
   `.agentmarshal/`. Journal records come from AgentMarshal commands.

These hold whichever harness runs the agent and however that harness handles
permissions.

## What ages with the harness

Permission models, command names, and settings formats belong to each harness
and change on its schedule. This project does not track harness releases. Any
allowlist you copy is yours to verify and maintain for the harness version you
run.

## Claude Code

Permissions live in `.claude/settings.local.json` (personal, per
project; keep it out of version control). Start from
`docs/templates/claude-code-settings.local.json` in this repository and
adapt it. The template identifies the Claude Code settings format and date it
was checked against; it is a perishable starting point, not a current-version
promise.

Three practical rules learned from running the rails:

1. **Allowlist by command family, not by full command.** A rule like
   `Bash(git *)` covers `git status`, `git commit`, `git push`, and so
   on. Cover every family the rails touch: git verbs, your package's
   check commands (test/lint/type-check runner), and the framework
   scripts.

2. **Avoid command substitution `$(...)` in allowlisted commands.** In the
   Claude Code settings format against which the template was verified, the
   harness treats a command containing `$(...)` as needing confirmation. Read
   files with the harness's file tools instead of in a subshell, or resolve a
   dynamic value (a commit SHA, a path) separately and pass it literally. A
   thin wrapper script can turn a substitution-heavy invocation into one
   allowlistable command.

3. **Allow the working temp directory.** Commands that `cd` outside the
   repository prompt even when the command itself is allowlisted. List
   the temp/scratch directories your workflow uses under
   `permissions.additionalDirectories`.

## Codex CLI

Codex is configured through `~/.codex/config.toml` and per-project
trust. Mark the project trusted so routine commands run without a
prompt, and pin the model and reasoning effort you intend to use for
implementation and review. Model identifiers change over time; check
your local Codex model list rather than hard-coding an identifier that
may have been retired.

## Repositories with more than one remote

Keep a working remote distinct from backup mirrors. Pruning and any cleanup
automation must target the working remote, never a mirror. `agentmarshal prune`
itself examines and changes only local branches and worktrees; it never contacts
any remote, so remote selection remains the operator's responsibility in the
surrounding tooling.

Do not leave this cleanup indefinitely. At least one provider fails closed once
a repository grows past roughly a hundred branches, turning branch untidiness
into an outage rather than a cosmetic problem.

## Verifying the setup

After configuring, run one full rails cycle on a throwaway task. If any
routine command still prompts, note the command family and add it to the
allowlist. A correctly configured harness completes the cycle —
contract, review, gate, completion — without a permission stop.
