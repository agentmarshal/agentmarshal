# Harness setup for the AgentMarshal rails

AgentMarshal drives its rails through a coding harness (Claude Code,
Codex CLI, …). Agents are productive on the rails only when the harness
does not stop them for a permission prompt on every routine command.
This guide captures a friction-free starting configuration. It is a
starting point — adapt the paths and command families to your project.

## Why this matters

The rails are a sequence of ordinary commands: `git`, the framework
scripts, your project's test and lint commands. If the harness prompts
for each one, an unattended or fast interactive run stalls waiting for a
human. The fix is a small, explicit allowlist of the command families
the rails actually use — not blanket permission, which gives up the
harness's safety.

## Claude Code

Permissions live in `.claude/settings.local.json` (personal, per
project; keep it out of version control). Start from
`docs/templates/claude-code-settings.local.json` in this repository and
adapt it.

Three practical rules learned from running the rails:

1. **Allowlist by command family, not by full command.** A rule like
   `Bash(git *)` covers `git status`, `git commit`, `git push`, and so
   on. Cover every family the rails touch: git verbs, your package's
   check commands (test/lint/type-check runner), and the framework
   scripts.

2. **Command substitution `$(...)` cannot be allowlisted.** The harness
   treats any command containing `$(...)` as needing confirmation,
   regardless of the allowlist — this is a safety heuristic, not a gap
   to close. Avoid it: read files with the harness's file tools instead
   of `cat`/`sed` in a subshell, and resolve a dynamic value (a commit
   SHA, a path) in a separate allowed command, then pass it literally.
   A thin wrapper script that fixes the environment and runs from the
   repository root turns a substitution-heavy invocation into a single
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

## Verifying the setup

After configuring, run one full rails cycle on a throwaway task. If any
routine command still prompts, note the command family and add it to the
allowlist. A correctly configured harness completes the cycle —
contract, review, gate, completion — without a permission stop.
