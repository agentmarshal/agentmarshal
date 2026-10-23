## Why

ADR-0021 decision 3 named the gate one of the three surfaces an
acknowledgement prints on: the gate prints the mark on the hits its
line shows, within the bound that line already has — at most twenty,
then "and N more not shown" — and an acknowledgement neither widens
nor narrows that bound. CR-187 landed the `acknowledge` command and
CR-190 the mark in `leak-scan`'s own output; the gate's advisory line
still prints every hit bare, so a reader of the merge transcript
cannot see which reported hits someone already verified — the one
surface where the merge decision is actually read.

## What Changes

- The gate's advisory leak-scan line marks each hit it shows that an
  `acknowledgement` record of the task acknowledges — the record's
  `commit` equal to the candidate's resolved commit, its `file` equal
  to the hit's file exactly as the scan prints it, and its
  identification equal to the hit's — with the same mark `leak-scan`
  prints: acknowledged, by whom, and the reason, masked with the
  scan's markers and escaped on display the same way. The records are
  the task's own, which the gate already loads.
- The mark-building moves into `capture.py` beside the renderer so
  the gate shares the command's code rather than forking its wording;
  `leak-scan`'s output is byte for byte unchanged.
- The line's bound is unchanged: at most twenty hits shown, then "and
  N more not shown" — an acknowledgement removes no hit, changes no
  order, and marks nothing the bound does not show. The line stays a
  warning and blocks nothing.
- A candidate whose task holds no acknowledgement bound to its commit
  produces today's line byte for byte; an acknowledgement of another
  commit or another task marks nothing.
- The specification's interim sentences are revised the way ADR-0021
  named them: the mark is part of the detail the merge boundary
  shares with the standalone command, not a thing the boundary lacks.

## Capabilities

- modified: `leak-scan`

## Impact

Only the gate's advisory line changes, and only on a candidate whose
task acknowledges a hit its scan reports: every other run is byte for
byte what it is today, so the pinned merge transcript and the gate
fixtures stand untouched. No other gate check changes, no command
changes, and the scan itself is untouched — the acknowledgement stays
what the threat model published it as: declared and durable, not
proven.
