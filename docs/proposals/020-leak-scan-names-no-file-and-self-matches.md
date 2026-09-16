# 020 — `leak-scan` reports a category but not the file, and a marker list matches its own declaration

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:dc5f932d5e4712c56b87ee33e48bd9408b98d9c1c2f1d7d1719ced102b7491cb` · **Disposition:** accepted *(in part; the acknowledged-and-proceed path is deferred)*

## Finding

Two problems in one incident, in a setup where review prompts are captured as
journal artifacts.

**The scan says what category matched, never where.** A journal transaction was
refused with a line naming a marker category and nothing else: no file, no line,
no matched marker. There was nothing to act on but a manual search.

**A marker list declared in the versioned project config matches its own
declaration.** The markers are read from the base tree; the task under review
changed that config, so the candidate's diff contained the marker declarations;
that diff was captured as an evidence artifact, so the artifact contained every
marker verbatim, and the scan fired on all of them. Nothing secret was present —
only variable names and the marker strings themselves. This is structural, not a
mistake in the marker values: any adopter who both captures diffs as evidence
and declares markers in the versioned config meets it on the task that edits
that config.

Measurements, as reported:

- Journal transactions blocked by this: **1 of 8**; false positives among them:
  **1 of 1**. Genuine built-in signature hits across all eight: **0**.
- Files and marker combinations checked by hand to locate the cause: **20**.
  Information the tool provided to narrow that down: **none beyond the category
  name**.
- Artifacts that contained the markers: **4**, all of them captured review
  prompts quoting the same config diff.
- Recovery cost: the transaction had to be completed outside the reporter's
  tooling, with the reasoning written into the pull request by hand, because
  the command offers no way to record "reviewed, not a leak".

## Proposed

Name the file path and the matched marker or signature for each hit, in the
standalone command and in the merge-time warning. Do not match a marker against
its own declaration, or at minimum document the interaction. Offer an
acknowledged-and-proceed path that is recorded rather than bypassed.

## Disposition — accepted for the first two, deferred for the third

An advisory scan that cannot say what it found is not advisory, it is an
obstacle: the operator's only move is a manual search, and the next operator's
move is to stop reading the warning. Hits will name the file and the matched
marker.

The self-match is the better half of this finding, because it is a property of
the design rather than of a configuration. It lands half-way home: this project
now pins reviewer prose as journal evidence, which is one of the two conditions
the reporter names, and declares no markers of its own, which is why it has not
met the second. A repository that adds a marker to its project file acquires the
defect the same day. The scan will not report a hit whose only
occurrence is the declaration it was loaded from.

The acknowledged-and-proceed path is deferred, and not for long. It is the right
idea — an operator who has verified a false positive should stay inside the
tooling, and the verification should become evidence rather than a bypass — but
it is a new kind of record, and this project decides record types in an
architecture decision before it builds them. It will be decided that way rather
than added as a flag.
