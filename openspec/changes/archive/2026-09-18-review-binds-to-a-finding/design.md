## Context

`launch_review` resolves a commit, diffs `merge-base..commit`, extracts a
metadata-free snapshot of the commit, reads the contract (from the snapshot in
an embedded placement, from the sidecar journal in a sidecar one), builds a
prompt from contract plus diff, runs the configured command, parses a
machine-verdict block that must name the reviewed commit, and records the
verdict through `submit_review` with the reviewer's raw bytes pinned as an
artifact.

`submit_review` already takes `reviewed_finding`; `records.py` already validates
a review that names exactly one of the two bindings; the gate's findings lane
already verifies artifact hashes and compares reviewer identity against the
recorder's. The only missing piece is the launcher path, and the CLI refusal
that stands in for it.

## Goals

- A review of a finding, recorded by the same writer, with the same prose
  pinning and the same diagnostics handling as a review of a commit.
- The reviewer judges the bytes the finding pinned.
- No change to the commit path, including its prompt bytes.

## Non-Goals

- Acceptance over a finding's blocking findings: `accept --accepted-finding`
  exists and is not touched here.
- A second reviewer channel, quorum, or any change to who decides.
- Reading artifacts from anywhere but the local project root. A reference that
  does not resolve is named, never fetched.
- Changing the gate: the findings lane already checks what it checks.

## Decisions

- **Verification happens in the launcher, before the reviewer runs.** The gate
  verifies hashes too, but after the fact. A reviewer given drifted content
  would produce a verdict about bytes nobody recorded, and the record would
  look identical to a sound one. Refusing before the run is the cheap side of
  that asymmetry.
- **One resolver, shared with the gate.** `_artifact_path` in `gate.py` decides
  what "resolves locally" means: a file, under the project root, symlinks
  resolved. The launcher needs exactly that decision, and two copies of it
  would be two answers to "is this artifact ours". It moves to
  `journal/artifacts.py` as a public helper and both callers read it. (The
  lesson is CR-100's: the two leak-scan callers were made to share a renderer
  and still kept two spellings of the suppression key.)
- **The reviewer gets file content, not a diff.** The prompt names each
  verified reference with its recorded hash and includes its text; references
  that did not resolve are listed as unverified. There is no base, so there is
  nothing to diff against, and a "diff" of a conclusion would be an invention.
- **Binary and oversized artifacts are named, not embedded.** An artifact that
  is not valid UTF-8 is named with its hash and size and its content is left
  out; the reviewer is told why. A conclusion pinned as a PDF is still
  reviewable by a human, and this path must not turn a byte sequence into
  mojibake inside a prompt.
- **The verdict protocol mirrors the commit one.** The block carries
  `reviewed_finding` instead of `reviewed_commit`; the parser accepts exactly
  one of the two and the launcher refuses a verdict whose subject is not what
  was asked. The commit prompt template is untouched; the finding prompt is its
  own template, because editing the shared one would change the pinned bytes.
- **The snapshot is the verified artifacts, not the tree.** A commit review
  gets a metadata-free snapshot so a relative path in the reviewer command
  resolves; a finding review gets a temporary directory holding the verified
  files at their reference paths, for the same reason.

## Risks

- [A reviewer reading pinned research prose reads private material] → the
  material is the project's own, the command runs where the operator put it,
  and the confinement of the reviewer is the operator's arrangement (ADR-0002);
  this change adds no new reader.
- [Two prompt templates drift] → the shared parts (verdict protocol, named
  material, amendment history) stay in shared helpers; only the subject block
  differs, and the commit template has a byte-for-byte test.
- [A finding with many large artifacts makes an unusable prompt] → content is
  included per reference with its hash; the operator sees the size in the
  refusal or the prompt. No limit is invented here: the existing prompt has
  none either, and inventing one in this task would be a second decision.
