+++
schema = 1
id = "CR-135"
title = "docs/known-defects.md: the kinds of defect this repository's reviews keep finding, and how to avoid them"
scope = [
  "docs/known-defects.md",
  "docs/README.md",
]
acceptance = [
  "docs/known-defects.md carries the thirteen classes of the coordinator's source, grouped as there (statements about the tool, consistency, privacy, code, scope, form), each with how it showed up and what avoids it, in plain English and in the source's order",
  "every example in the file is general: no task id, record id, finding id, proposal number used as an example of a defect, adopter pseudonym, commit, or private path; where the source names a published document (an ADR, the leak scan, the gate), the name is exact and linked only if the file exists",
  "every statement about the tool's present behaviour in the file is true of the code and published documents (for example, how many record types the journal has, that the gate writes nothing to the journal, how the leak scan masks paths)",
  "the documentation map has a line for docs/known-defects.md saying who reads it and when — an implementer, before starting and before finishing",
  "the full CI sequence passes",
]
+++

# CR-135: known defects

## Context

The project's own reviews keep finding the same kinds of defect: claims
about the tool made from memory, a reporter's observation stated as the
tool's fact, one fact said differently in different places, a new text that
revises a published decision without saying so, identifiers from an
adopter's repository, text processing that splits on more than it should,
changes outside the scope. A document of these classes, given to the
implementer in the brief, may make tasks converge faster; whether it does is
measured on the tasks that follow (the coordinator's experiment). This task
only publishes the document.

## Objective

The classes are published where a brief can name them.

## Acceptance Criteria

As in the header.

## Non-Goals

- Naming the document in any contract (the experiment decides per task).
- Adding classes the source does not have.
