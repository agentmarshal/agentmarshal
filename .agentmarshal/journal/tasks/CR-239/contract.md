+++
schema = 2
id = "CR-239"
title = "The base-tree manifest reader refuses a file-form manifest that declares a command or a lock, and switch rewrites compare unchanged TOML values, NaN included, as unchanged"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/extensions.py",
  "src/agentmarshal/switch_off.py",
  "src/agentmarshal/extension_trust.py",
  "src/agentmarshal/switches.py",
  "tests/",
]
acceptance = [
  "the reader of manifests from the base tree (gate.py `_manifest_from_tree` or whatever it calls) applies the same file-form rule as the working-tree reader: a single-file manifest that declares a stage `command` or a dependency lock is refused with the working-tree reader's reason, through one shared validation rather than a second copy (release-audit finding AUD-extensions-2; extension-manifest spec, file form has no extension directory, and the tree reader applies the filesystem rules); a test reads such a manifest from a real temporary git repository's tree",
  "`extension switch off` and `extension enable/disable` verify a rewrite with a comparison under which an unchanged value compares equal to itself — NaN included — and types stay distinct (e.g. compare the parsed values with NaN treated as equal to NaN, or compare normalised TOML text of the untouched part); a switches file holding `future = nan` and an existing switch can be switched off, enabled and disabled (AUD-extensions-3); tests for each path",
  "no requirement changes; every valid manifest and switches file reads and rewrites byte for byte as today; existing tests and transcripts unchanged; the suite and the full CI sequence pass",
]
documents = []
decisions = ["ADR-0013"]
+++

# Base-tree manifest form rule, NaN in switch rewrites

## Context

Release audit 0.6.0, area extensions, findings AUD-extensions-2 and -3
(reproduced by the auditor at function level): the base-tree manifest
reader accepts a schema-2 file-form manifest with a stage command that
the working-tree reader refuses, which the extension-manifest
specification forbids; and a switches file holding an unchanged TOML
`nan` makes every switch rewrite fail its own verification, because NaN
is unequal to itself.

## Objective

Both manifest readers apply one rule; switch rewrites accept any valid
file.

## Acceptance Criteria

As in the header.

## Non-Goals

- Stage output limits (AUD-extensions-4) and spec Purpose text
  (AUD-extensions-5): advisory, later.
