+++
schema = 2
id = "CR-150"
title = "outbox new scaffolds a finding for upstream, and outbox check names what a draft is missing and what the leak scan finds"
scope = [
  "src/agentmarshal/outbox.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/outbox-new-and-check/",
  "openspec/changes/archive/",
  "openspec/specs/outbox/",
]
acceptance = [
  "the change outbox-new-and-check has a proposal, a design.md and a delta spec adding the outbox capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/outbox/",
  "`agentmarshal outbox new \"<gist>\"` writes one new draft into the project's outbox (`.agentmarshal/upstream/`), named with the next free number and a slug of the gist (the scheme is stated in design.md), carrying the five fields of CONTRIBUTING's finding form — Symptom, Measurements, Version, Environment, Expected — as headings, with Version filled from the running tool and Environment from the machine (OS, Python version), and prints the path; it never overwrites a file, and refuses with a message when there is no outbox",
  "`agentmarshal outbox check` reads every draft in the outbox (the README that init writes is not a draft: its fields are not checked, but its name and content are leak-scanned like everything that leaves with the batch) and, for each draft that does not conform, names the file and each missing or still-unfilled field; a freshly scaffolded draft is reported as unfilled in Symptom, Measurements and Expected",
  "`outbox check` also runs the leak scan the merge boundary uses, with the private markers from the project's configuration, over the drafts' content, and names each hit by file and identification without printing the matched text; a draft whose file name carries a configured marker or matches a signature is a hit by itself, since the name leaves with the batch; anything in the outbox that is not a regular file is named as not checked; no path and no error text carrying a path is printed unmasked; its exit status is 0 only when every draft conforms, nothing in the outbox went unchecked and the scan finds nothing, and non-zero otherwise, so a wrapper can refuse to send",
  "the command registers itself from its own module (cli.py gains only the hook), and the full CI sequence passes",
]
documents = ["openspec/specs/outbox/"]
+++

# CR-150: outbox new and outbox check

## Context

ADR-0020 decisions 1–3: one command group named `outbox`; `outbox new`
scaffolds a draft with the five fields of CONTRIBUTING's finding form,
Version and Environment filled from the machine; `outbox check` names, per
draft, the file and the missing field, runs the leak scan over what would
be sent, and refuses by exit status. `send` and `status` are a later task.

## Objective

An adopter scaffolds a finding in one command and learns, before sending,
what it lacks and whether it leaks.

## Acceptance Criteria

As in the header.

## Non-Goals

- `outbox send` and `outbox status` (a later task).
- Any change to init's outbox README or to the research `finding` command.
- Sending anything anywhere.
