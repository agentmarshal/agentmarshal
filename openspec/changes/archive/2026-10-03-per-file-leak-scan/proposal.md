## Why

Proposal 026's fourth finding (one adopter) and proposal 037 (another) share a
root cause: git's diff output is decoded as UTF-8 strictly and as a whole. In
the gate, one undecodable byte raises and the scan degrades to
`WARN: leak-scan skipped` for the entire diff; the `leak-scan` command refuses
the same way. Upstream reproduced it on 2026-10-01: a commit adding a text
file holding a secret-shaped string and a file of random bytes reported
nothing; without the binary file it reported the string. The published
disposition: a file that does not decode should cost its own readability, not
every file's scan.

## What Changes

The candidate diff is captured as bytes and decoded one `diff --git` section
at a time. A section that fails strict decode is decoded with the escape
error handler instead — its added bytes are still searched, because a
signature written in ASCII survives the escaping, and the file is named in
the caller's output as one whose bytes were only partially readable. A path
whose own bytes do not decode is named in escaped printable form rather than
refusing the scan. One helper runs the pinned diff for both the gate and the
standalone command, so the two can no longer degrade differently.

The command's exit status keeps answering "was anything found": a file that
did not decode is reported but does not fail the run on its own — an ordinary
binary file in a diff must not fail every CI run of the command, which is
where adopters run it. The gate's scan stays advisory throughout.

## Capabilities

- modified: `leak-scan`

## Impact

A candidate mixing a text file and a binary file is scanned for the text
file's content again, and the binary file is named rather than silently
carrying the whole scan down with it. `review`'s diff handling shares the
root cause and is a separate task; the byte-capturing helper this change adds
is shaped so that task can reuse it.
