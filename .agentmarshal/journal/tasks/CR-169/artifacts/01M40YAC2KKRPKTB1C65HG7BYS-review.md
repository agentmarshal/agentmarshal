CR169-SIDECAR-DRY-RUN: `src/agentmarshal/cli.py:592` omits `placement.journal_root` when calling `dry_run_review`, so sidecar dry-run diagnostics fall back to a temporary file or enter the host’s local state; `tests/test_review_launcher.py:604` bypasses the CLI and therefore misses this acceptance-criteria violation.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"6f3e3511387e81325436009267cedf9bc377108c","verdict":"changes_required","findings":["CR169-SIDECAR-DRY-RUN"]}
AGENTMARSHAL_VERDICT_END
