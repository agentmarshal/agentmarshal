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
- **A binary artifact is named, not embedded.** An artifact that is not valid
  UTF-8 is named with its hash and size and its content is left out; the
  reviewer is told why. Size is deliberately not a criterion: no threshold
  exists anywhere in this path, the Non-Goals below say why one is not
  invented here, and an earlier draft of this decision said "binary and
  oversized", which claimed a limit the code does not have. A conclusion pinned as a PDF is still
  reviewable by a human, and this path must not turn a byte sequence into
  mojibake inside a prompt.
- **The verdict protocol mirrors the commit one.** The block carries
  `reviewed_finding` instead of `reviewed_commit`; the parser accepts exactly
  one of the two and the launcher refuses a verdict whose subject is not what
  was asked. The commit prompt keeps its own template and, more to the point,
  its rendered bytes: the two templates share the verdict protocol, the prose
  instruction and the named-material block through helpers, and the pinned test
  proves the commit prompt still renders byte for byte as it did. The template
  text itself was edited to call those helpers — what is untouched is the
  output, not the source.
- **The snapshot is the verified artifacts, not the tree.** A commit review
  gets a metadata-free snapshot so a relative path in the reviewer command
  resolves; a finding review gets a temporary directory holding the verified
  files at their reference paths, for the same reason.
- **Named material is named, not supplied, for a finding review.** The finding
  snapshot contains only the verified artifact bytes, so named Decisions and
  Documents are not readable from the reviewer's working directory as they are
  in a commit snapshot. The prompt says that those items are names rather than
  supplied material, and that only the pinned artifacts were verified.
- **A launched finding review is for the latest finding and an independent
  reviewer.** The findings lane evaluates only its latest finding and compares
  declared git identities. The launcher makes both checks before invoking the
  reviewer, reusing the gate's identity resolution and refusal wording, so an
  append-only review record cannot be created for evidence the lane must deny.

- **Embedded artifact content is prefixed, because the diff path is immune by
  accident and this one would not be.** Every line of a diff carries `+`, `-`
  or a space, so a verdict sentinel copied from a source file never reaches
  column zero. A finding's artifact is embedded as itself, and a pinned file
  containing a complete verdict block naming the finding under review would
  hand the reviewer one valid block to echo — an approval nobody gave. Each
  embedded line therefore carries a fixed prefix, the prompt says so, and the
  sentinels appear in the prompt only where the launcher writes them.
  Withholding such content instead was the alternative; it would make exactly
  our own review prose and measurement logs unreviewable, which is the
  material this path exists for.
- **The two pre-run refusals are requirements, not implementation details.**
  The published capability said the launcher accepts a finding of the task,
  while the code refuses two classes of them. A spec that claims more than the
  code does is the defect this project keeps finding in its own documents, so
  the refusals are specified and each carries a scenario.

- **A scoped task is refused too, and the reason is the lane's own.** The
  findings lane refuses a task whose contract declares a scope, so a finding
  review launched on one spends a run and writes a permanent record no lane
  will read. The launcher's pre-run refusals exist to prevent exactly that, so
  the admission rule is asked before the reviewer runs, not after.
- **The finding's summary travels with its artifacts.** ADR-0009 Decision 1
  makes the summary the one-line claim the finding makes about the bytes it
  pins. A reviewer given the bytes and not the claim is asked whether evidence
  is good without being told what it is evidence for.
- **A finding review's contract is the working tree's, and the record says
  which one it was.** There is no commit to read it from, so the launcher reads
  the contract as it stands and records its sha256 in `reviewed_contract`
  (ADR-0011), the way the commit path does. ADR-0011 left what the findings
  lane does with amendment history and the contract hash unsettled; this
  settles it the same way for both paths — the amendment history is rendered
  into the prompt, and the hash pins which text was judged. Drift is therefore
  detectable after the fact rather than prevented, which is the same guarantee
  a commit review gives for a contract amended after the review.

- **Departure: the launcher's refusal wording is its own.** The decision above
  says the launcher reuses the gate's identity resolution and its refusal
  wording. It reuses the resolution, and deliberately not the wording: the
  gate's line is a transcript entry phrased as the check it performs, byte-
  stable because published transcripts pin it, while a pre-run refusal has to
  tell an operator what is wrong before anything is spent. One function holds
  both phrasings so the rule still has a single home.

## Risks

- [A reviewer reading pinned research prose reads private material] → the
  material is the project's own, the command runs where the operator put it,
  and the confinement of the reviewer is the operator's arrangement (ADR-0002);
  this change adds no new reader.
- [Two prompt templates drift] → the shared verdict protocol, named material,
  prose instruction, and amendment history stay in shared helpers; only the
  subject and snapshot statements differ. Both prompt renderings have
  byte-for-byte tests.
- [A finding with many large artifacts makes an unusable prompt] → content is
  included per reference with its hash; the operator sees the size in the
  refusal or the prompt. No limit is invented here: the existing prompt has
  none either, and inventing one in this task would be a second decision.
