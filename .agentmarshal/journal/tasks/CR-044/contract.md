+++
schema = 1
id = "CR-044"
title = "docs/proposals: intake of the first downstream batch (English digests + dispositions)"
scope = ["docs/proposals/"]
acceptance = [
  "docs/proposals/README.md documents the intake pipeline: adopters collect findings downstream, upstream publishes English digests with source attribution, tool version and a disposition; originals stay with the reporter",
  "the first batch is landed as English digests, one file per theme, each carrying a stable adopter pseudonym plus a neutral profile instead of any client, product or repository name",
  "every digest keeps its measurements verbatim (counts, run ratios, timings) because those are the evidence",
  "each digest states a disposition (accepted / deferred / declined) with reasoning; a declined proposal keeps its file and its reason",
  "no client name, product name, third-party domain or business data appears anywhere under docs/proposals/",
  "no code, schema or gate change; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-044: docs/proposals: intake of the first downstream batch

## Context

Three adopters have been running AgentMarshal 0.1.0 in production and sent
twenty-two files of operational findings upstream. They currently have no home
here: `docs/proposals/` does not exist, so the findings sit in the adopters'
private repositories and reach no one. CR-043 established the policy
(`CONTRIBUTING.md`); this task builds the receiving end and lands the backlog.

Two constraints shape the work. The originals are mostly Russian while this
repository is English, so the public artifact is a digest, not a translation.
And every adopter repository is private: the originals name clients and
products, and a public repository cannot un-publish, so names are replaced by
stable pseudonyms and the originals stay with the reporter.

## Objective

Create `docs/proposals/` with the intake pipeline documented, and land the first
batch as English digests — sanitized, attributed to pseudonymous adopters,
measurements verbatim, each with a disposition and its reasoning.

## Acceptance Criteria

- [ ] `docs/proposals/README.md` documents the pipeline and the disposition
      states.
- [ ] First batch landed as English digests, one file per theme, with adopter
      pseudonyms and neutral profiles.
- [ ] Measurements verbatim in every digest.
- [ ] Every digest carries a disposition with reasoning; declined ones keep
      their file.
- [ ] No client/product name, third-party domain or business data anywhere.
- [ ] No code/schema/gate change; the suite stays green.

## Non-Goals

- Not implementing any proposal — this is intake and disposition only.
- Not publishing the originals; they stay with the reporter (private).
