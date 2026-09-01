+++
schema = 1
id = "CR-076"
title = "The install instructions describe a published release"
scope = ["docs/quickstart.md", "README.md"]
acceptance = [
  "the quickstart installs with `pip install agentmarshal==0.2.0` and no longer says the version is unpublished",
  "the README does the same, and no longer describes the repository version as unavailable from the index",
  "uv is no longer stated as a requirement for installing, since it was needed only to build from source",
  "the guide still says which artifact its commands were verified against",
  "the pinning advice stays, and still points at the upgrade guide for the reason",
]
+++

# CR-076: The install instructions describe a published release

## Context

0.2.0 was published to PyPI at 2026-09-01T00:07Z. The quickstart and the README
were written while it was not, and both tell the reader that the version is
unavailable from the index and must be built from source with uv.

That was true when written and is false now. Leaving it is the exact failure
this release spent a pass removing: a document describing a state that has
passed, which a reader cannot distinguish from a current one.

## Objective

Say how to install the release that exists.

## Acceptance Criteria

- The quickstart installs with `pip install agentmarshal==0.2.0`, and no
  statement remains that the version is unpublished.
- The README does the same, and no longer describes the repository version as
  unavailable from the index.
- **uv is no longer a stated requirement.** It was needed only to build from
  source; requirements return to Python and git.
- The guide still says what its commands were verified against — now the
  published release rather than a locally built wheel.
- The advice to pin stays, and still points at `UPGRADING.md` for why.

## Threat model and boundaries

Documents. Nothing executes.

The hazard is the one the whole release taught: **an instruction that was true
once**. The install path must be run as written, against the published package,
before the document claims it works — the guide's verification claim is the
thing this task is protecting, not decorating.

## Non-Goals

- Changing anything about the loop the quickstart walks through, or any other
  section.
- Re-verifying the whole guide. The loop was verified for CR-074 and has not
  changed; what changed is where the package comes from.
- Announcing the release, or editing the changelog.
