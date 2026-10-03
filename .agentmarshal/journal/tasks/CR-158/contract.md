+++
schema = 2
id = "CR-158"
title = "An extension may live in a directory — <name>/manifest.toml with bin/ and lock/ — read from the working tree beside the single-file form"
scope = [
  "src/agentmarshal/journal/extensions.py",
  "tests/",
  "openspec/changes/extension-directory-form/",
  "openspec/changes/archive/",
  "openspec/specs/extension-manifest/",
]
acceptance = [
  "the change extension-directory-form has a proposal, a design.md and a delta spec modifying the extension-manifest capability (MODIFIED requirements keep their exact headers, ADDED for new ones); every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`read_extension_manifest` finds an extension at `.agentmarshal/extensions/<name>/manifest.toml` as well as at `.agentmarshal/extensions/<name>.toml`; when both exist for one name it refuses, naming both paths; the directory form requires a manifest of schema 2 and refuses schema 1 with a message saying so",
  "in the directory form, a stage's `command` and the `lock` paths a manifest names must exist inside that directory as regular files, not symlinks and not reached through `..`, and are refused otherwise with a message naming the path; the single-file form keeps its rules unchanged (a schema-2 single file naming `bin/` or `lock/` paths is refused, since it has no directory — stated in design.md)",
  "every symlink refusal the reader has today applies to the directory and to the manifest inside it; the parsed manifest exposes the directory it was read from, for later tasks",
  "the callers (brief, review, the gate's working-tree read) keep working with both forms unchanged, the gate's fixtures are unchanged, and the full CI sequence passes",
]
documents = ["openspec/specs/extension-manifest/"]
+++

# CR-158: the extension directory form

## Context

ADR-0013 (decisions 12–15 and the 2026-10-03 amendments) gives an extension
a directory: `manifest.toml`, `bin/` for everything runnable, `lock/` for
the dependency locks. CR-152 parses manifest schema 2 in the single-file
form. This task reads the directory form from the working tree. The gate's
reading of manifests from the base tree is a separate task.

## Objective

An extension in the directory form is found, validated and exposed with its
directory.

## Acceptance Criteria

As in the header.

## Non-Goals

- The gate's base-tree reader and removal check (a later task).
- Running anything, trust, the personal scope, doctor.
