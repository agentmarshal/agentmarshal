+++
schema = 1
id = "CR-074"
title = "Version 0.2.0, and every claim about what 0.1.0 contained re-checked"
scope = ["pyproject.toml", "src/agentmarshal/__init__.py", "README.md", "docs/quickstart.md", "docs/overview.md", "docs/adr/ADR-0004-journal-data-model.md", "docs/adr/ADR-0005-evidence-capture-and-format.md", "tests/test_smoke.py"]
acceptance = [
  "the project version is 0.2.0 in pyproject.toml and in `agentmarshal --version`",
  "every statement about what a release does or does not contain is re-checked against the code and corrected where it is now false",
  "living documents — README, quickstart, overview — describe 0.2.0; the ADRs keep their historical notes and say where a status has since changed",
  "the quickstart's claim to be verified against a release is honoured: the commands in it are run against a built 0.2.0 artifact",
  "the quickstart names the new commands where the loop reaches them, without becoming a reference manual",
]
+++

# CR-074: Version 0.2.0, and every claim about what 0.1.0 contained re-checked

## Context

Twenty-two statements across five documents describe what the 0.1.0 release
does or does not contain. Some are still true, some became false while the work
was being done, and a reader cannot tell which without checking the code — which
is the opposite of the reason they were written.

The quickstart makes the strongest claim of all: that every command in it was
verified against the published release. That claim is only worth anything if it
is re-earned rather than re-typed.

The two kinds of statement need different treatment. **README, quickstart and
overview are living documents** — they describe the tool a reader is about to
use, and should speak about the release they ship with. **The ADRs are
historical records**; their boundary notes were true when written and should stay,
with the change in status noted rather than the history rewritten.

## Objective

Bump the version, and make every claim about a release's contents true again.

## Acceptance Criteria

- The version is `0.2.0` in `pyproject.toml` and reported by
  `agentmarshal --version`, and the smoke test that pins the reported version
  is updated with it.
- Every statement about what a release contains is re-checked against the code
  and corrected where it is now false. A statement that is still true stays.
- The living documents describe 0.2.0. The ADRs keep their historical notes and
  say where a status has since changed, in the manner ADR-0005 already uses for
  the leak-scan.
- The quickstart's verification claim is **honoured**: its commands are run
  against a built 0.2.0 artifact, not merely re-labelled. Where the guide's
  install instruction refers to a version not yet on the index, it says so.
- The quickstart mentions the new commands at the point in the loop where a
  reader would reach for them, without turning into a reference manual.

## Threat model and boundaries

Documents and a version number. Nothing here changes behaviour.

The failure to guard against is the one this task is entirely about:
**re-labelling instead of re-checking**. Changing `0.1.0` to `0.2.0` throughout
would satisfy a careless reading of every criterion above and leave the
documents exactly as wrong as they are now, with the wrongness harder to spot
because the version looks current.

Not in this task's reach: publishing, tagging, or the release workflow. The
version in the repository and the version on the index are different facts, and
this task establishes only the first.

## Non-Goals

- **Tagging or publishing.** A version bump is not a release; the operator
  decides when to publish.
- Rewriting the ADRs' reasoning. A historical record stays historical.
- Documenting the new commands exhaustively. The changelog lists them and each
  has its own help; the quickstart points, it does not enumerate.
- Any code change beyond the version constant.
