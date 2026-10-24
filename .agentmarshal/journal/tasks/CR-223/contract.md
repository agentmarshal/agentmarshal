+++
schema = 2
id = "CR-223"
title = "The read-only candidate floor holds: the remount keeps the mount's locked flags, and the stage re-enters the candidate after the bind so no inherited working directory reaches the writable mount"
scope = [
  "src/agentmarshal/isolation.py",
  "tests/",
  "openspec/changes/readonly-floor-holds/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change readonly-floor-holds has a proposal, a design.md and a delta spec on the capability extension-stages (ADDED requirements, or MODIFIED for the requirement that states the read-only candidate, carrying its full text with the heading byte for byte); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "the read-only remount carries the flags the candidate's mount already has that a user namespace may not clear — at least `nosuid`, `nodev`, `noexec`, `noatime`/`nodiratime`/`relatime` as `os.statvfs(directory).f_flag` reports them (ST_NOSUID → MS_NOSUID and so on) — so that on a candidate under a `nosuid,nodev` mount such as `/tmp` the bind becomes read-only instead of failing with `EPERM`; the mapping is one function, unit-tested over every flag it maps",
  "after the read-only remount the child changes its working directory to the candidate directory again (`os.chdir`), before the capability drop and exec, so a relative write from the stage's inherited working directory meets the read-only mount; a failure of that step is reported on the read-only guarantee as not enforced, never silently",
  "the probe performs the same remount and re-entry, so its answer matches what a stage gets; the end-to-end test (run only where the real probe succeeds) writes through a relative path and through an absolute path into the candidate and both are refused, and it is skipped with the probe's reason elsewhere",
  "no other behaviour changes; `stage run`'s lines on a platform that enforces everything are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0013"]
+++

# The read-only floor holds

## Context

CR-221 landed stage isolation. The reviewer-model test of 2026-10-24
(research `observations/2026-10-24-reviewer-model-test-results.md`) found,
and an experiment outside any sandbox confirmed, two defects in the
read-only candidate floor (ADR-0013 decision 8):

1. In a user namespace the kernel refuses a remount that would clear a
   locked flag of the original mount; the remount passes only
   `MS_BIND | MS_REMOUNT | MS_RDONLY`, so on a candidate under a
   `nosuid,nodev` mount (any `/tmp`) it fails with `EPERM` and the floor is
   never enforced (the stage reports it as not enforced).
2. `Popen(cwd=…)` changes directory before `preexec_fn`; after the bind the
   inherited working directory still refers to the underlying writable
   mount, so a relative write bypasses the read-only bind (experiment: the
   relative write succeeded, the absolute one got "Read-only file
   system"; a `chdir` after the bind closed it).

## Objective

Where the platform allows the floor, a stage cannot write the candidate by
any path.

## Acceptance Criteria

As in the header.

## Non-Goals

- Making anything outside the candidate read-only.
- Network isolation and the provider-secret floor (unchanged).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
