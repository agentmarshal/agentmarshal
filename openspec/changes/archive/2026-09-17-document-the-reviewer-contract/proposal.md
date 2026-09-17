## Why

An adopter running the published release lost three review launches to
properties of the reviewer command that appear in no documentation
([proposal 015](../../../docs/proposals/015-reviewer-command-contract-undocumented.md)):
the command runs in a metadata-free snapshot with no git directory, a relative
path in it resolves inside that snapshot, and the invalid-placeholder error
names no token. They read about 120 lines of the launcher to learn what the
documentation does not say.

The same undocumented fact has a second half this project found on itself: the
snapshot sets where the command *starts*, not what the process may *read*. A
reviewer launched as an ordinary process can read whatever its operating-system
user can, including the journal it is judging.

## What Changes

- The configuration section documents the reviewer command's contract: the
  snapshot as working directory, relative-path resolution inside it, and what
  the prompt-file placeholder contains.
- The same section states that bounding what the command may read is the
  adapter's responsibility, not the tool's.
- The invalid-placeholder error names the token it rejected.
- `agentmarshal review --dry-run` launches the configured command on a synthetic
  prompt, reports whether the output yields a parseable verdict, and records
  nothing.

## Impact

- `src/agentmarshal/journal/review.py`: the placeholder error, and a launch path
  that does not record.
- `src/agentmarshal/cli.py`: the flag.
- `docs/quickstart.md`: the contract and the adapter's responsibility.
- No record, no gate change: a dry run is not evidence.
