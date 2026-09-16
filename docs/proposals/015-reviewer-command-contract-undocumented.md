# 015 — The reviewer command contract is only discoverable from source

- **Reporter:** Adopter D (greenfield project on Linux, GitHub, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:5023b87a15185c08` · **Disposition:** accepted

## Finding

Three properties of the reviewer command are absent from the quickstart, and
each cost one failed launch:

1. The command runs with its working directory set to a metadata-free snapshot
   of the reviewed commit, with no git directory in it. A wrapper that begins by
   asking git for the repository root to find its own scripts dies there, and at
   least one vendor CLI refuses to start in such a directory without an explicit
   flag. The documentation says the reviewer is read-only; it does not say the
   reviewer is outside the repository.
2. A relative path in the command resolves inside that snapshot, which means it
   resolves to the reviewed commit's copy of the wrapper rather than the
   operator's current one. Bootstrapping a change to the wrapper itself
   therefore needs an absolute path.
3. The invalid-placeholder error does not name the token it rejected. The
   reporter's value had lost a closing brace to a shell quoting accident, and
   the message gave nothing to search for.

Measurements, as reported:

- Failed review launches before the first success: **3**, one per property.
- Lines of the review launcher read to learn the contract: about **120**.
  Documentation lines that state it: **0** for the first two properties.

## Proposed

Document that the reviewer runs in a metadata-free snapshot, that relative paths
resolve inside it, and what the prompt-file placeholder contains. Name the
offending token in the placeholder error. Offer a dry run that launches the
configured command on a synthetic prompt and validates the verdict block, so the
contract is exercised before the first real review.

## Disposition — accepted

All three, and one addition the reporter could not have known to ask for.

The snapshot is the mechanism behind the independence this project claims, and
it is described nowhere the operator reads. That is the finding. The addition is
what the same undocumented fact means in the other direction: the snapshot sets
where the reviewer command *starts*, not what the process may *read*. A reviewer
launched as an ordinary process can read whatever its operating-system user can
read, including the journal it is being asked to render a verdict for. Confining
that is the adapter's job, not the tool's, and until now we had not said so
anywhere either.

So the documentation this proposal asks for gains a second half: where the
command starts, and what the adapter is responsible for bounding. Accepted for
the next release together with the named token and the dry run.
