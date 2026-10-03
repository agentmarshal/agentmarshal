I reviewed the reader, the delta spec, the archived change, the live spec, the tests, and the three callers.

**What I verified**

- `_manifest_candidate` applies the file-form rule to both candidates: the lexical `is_symlink()` walk runs from the manifest path up to (excluding) `.agentmarshal/extensions`, so for the directory form it covers both `<name>/manifest.toml` and `<name>` itself — dangling or not, before existence is decided — while a symlinked `extensions/` or `.agentmarshal/` is still caught by `resolved != path` (`extensions.py:485`–`511`). The walk always terminates, since `extensions_dir` is constructed as an ancestor of `lexical` from the same `project_root`.
- `not_a_directory_is_absent` is the only asymmetry, and it is the right one: the file form keeps its `NotADirectoryError` → "cannot resolve" refusal (test at `tests/test_extensions.py:769` parametrized over both ancestors), while a `<name>` that is a regular file is simply absent.
- `_manifest_directory_paths` covers exactly the three fields that `_require_directory_file` validates in the parser — `stage.command`, `[dependencies].lock`, `[wraps].lock` — so nothing a schema-2 manifest can name under `bin/`/`lock/` escapes the existence check, and nothing else is checked.
- `..` is genuinely forbidden lexically before the filesystem check: `validate_scope_entry` rejects any `.`/`..` component (`contracts.py:126`), so design.md's claim holds, and `_require_existing_directory_file`'s component walk plus a fully-resolved `directory` (guaranteed by `resolved == path` on the dir candidate) make escape out of the extension directory unreachable.
- Callers are untouched in substance: `brief.py:232`, `review.py:1071`/`1247` and `gate.py:820` use only `.documents`/`.footprint` and the exception types; nothing compares `ExtensionManifest` instances, so the new `directory` field (last, defaulted) breaks no equality or positional construction. The gate's base-tree reader and `_extension_name` are untouched, which matches the stated non-goal.
- Every one of the 17 scenarios in the delta has a test whose docstring names it verbatim (I diffed the delta's scenario headings against all test docstrings — no misses), each new requirement appears exactly once in `openspec/specs/extension-manifest/spec.md`, the MODIFIED requirement keeps its exact header and its body matches the live spec byte for byte, and the change lives only under `openspec/changes/archive/2026-10-03-extension-directory-form/` with the `.openspec.yaml` the other archived changes carry.

**One advisory finding**

`advisory-schema-1-directory-message-order` — in `src/agentmarshal/journal/extensions.py:623`–`629` the "directory form requires schema 2" check runs *after* `parse_extension_manifest_text`, so it is only reached by a directory-form manifest that is otherwise a valid schema-1 manifest. A directory-form `manifest.toml` that declares `schema = 1` and also, say, omits `install` is refused with `extension manifest field 'install' must be a non-empty string` instead of the message the requirement "The directory form requires a manifest of schema 2" asks for. The input is still refused, and the field message is arguably more useful, so this is a message-ordering nit rather than a correctness defect; checking the parsed `schema` before the schema-1 field requirements would close it.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "059ba350bcf40d8d912d30850535816f2a87d076", "verdict": "approved", "findings": [], "advisory_findings": ["advisory-schema-1-directory-message-order"]}
AGENTMARSHAL_VERDICT_END
