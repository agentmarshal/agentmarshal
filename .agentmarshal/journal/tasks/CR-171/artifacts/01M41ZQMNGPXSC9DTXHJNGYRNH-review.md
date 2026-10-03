CR171-003 is fixed: one-line triple-quoted IDs ending in quote characters are now parsed and rewritten correctly.

CR171-004: `src/agentmarshal/journal/open_task.py:188-196` uses ASCII-escaping `json.dumps(probe_id)`, producing TOML-invalid surrogate escapes for non-BMP characters; consequently a valid supported declaration such as `id = "😀"` is incorrectly refused by `open --contract-file`.

`agentmarshal validate` passed. The remaining prescribed checks could not run because `uv`, pytest, Ruff, and mypy are unavailable in the review environment.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"219729bca6fd20faaa0185f9c1379a5c45f83e83","verdict":"changes_required","findings":["CR171-004"]}
AGENTMARSHAL_VERDICT_END
