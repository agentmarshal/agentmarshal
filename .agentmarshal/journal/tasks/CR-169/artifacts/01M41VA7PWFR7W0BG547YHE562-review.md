CR169-F001: `src/agentmarshal/process_log.py:263-295` checks `log/files/` without following symlinks but then traverses and unlinks through its pathname; replacing that directory with a symlink after the check can make the sweep delete files outside local state, violating the requirement that it never follow symlinks.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"45fd711b6bdea9b3b03ca0b250371a1ed5566958","verdict":"changes_required","findings":["CR169-F001"]}
AGENTMARSHAL_VERDICT_END
