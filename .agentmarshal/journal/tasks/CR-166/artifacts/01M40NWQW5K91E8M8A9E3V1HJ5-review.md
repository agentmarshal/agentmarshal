I reviewed the diff against the contract and the named spec material.

**What I checked**

- `record_session` (`src/agentmarshal/journal/session.py:30-77`): the six new parameters are keyword-only, default `None`, and pass straight through to `create_session_record`, which already accepted them (`src/agentmarshal/journal/records.py:1380-1437`). No positional signature change, and `record_session` has exactly one caller (`cli.py:948`), so nothing existing shifts.
- Schema stamping: `_minimum_schema` (`records.py:1232-1245`) raises the stamp to 7 on `record.keys() & _SCHEMA_7_SESSION_FIELDS`, and omits the key entirely when a value is `None` — so "with a flag → 7" and "without any flag → 3, or 6 for coordination" both follow from the existing derivation rather than from new CLI logic.
- Refusals: the command layer adds no validation of its own, so an empty/whitespace value surfaces `session-fields-7`'s message (`records.py:552-563`) and a forgeable character surfaces `forgeable-text`'s (`records.py:682-694`, `_reject_control_characters` at `records.py:1014-1032`). The asserted substrings in the new tests are real substrings of those messages, and `write_record` is never reached, so nothing is written.
- `--commit`: `_resolve_commit` (`gate.py:275-281`) is `git rev-parse --verify <rev>^{commit}` with a 40-char check, run against `placement.host_root` — the same root `review` (`cli.py:620`) and `complete` (`cli.py:789`) use. `require_host=args.commit is not None` (`cli.py:936`) matches the established conditional pattern (`cli.py:615`, `677`, `773`), and a sidecar without the flag reads no host fact. An unresolvable revision fails as `GateError` whose text embeds the revision, so the refusal names it, and the failure is before any write.
- Scenario-to-test mapping: all nine delta scenarios have a test whose docstring names them verbatim. The sidecar test is genuinely discriminating — `_host_and_sidecar` inits the sidecar with `-b master` and no commit (`tests/test_placement.py:15-17`, `397-435`), so `master` resolves only in the host. The cross-module test import (`from test_placement import _host_and_sidecar`) follows the existing pattern at `tests/test_gate.py:36`.
- Archive state: `openspec/changes/` holds only `archive/`, the change sits at `openspec/changes/archive/2026-10-03-record-session-schema-7-flags/`, and the two ADDED requirements landed verbatim in `openspec/specs/session-activity/spec.md:128-194` with no duplicated headers. `docs/sidecar.md:406` already described `record-session` as "reading host git facts where needed", so no doc contradicts the new behaviour.

I found no blocking defect.

**Advisory**

AD-1 — `src/agentmarshal/cli.py:35` imports `_resolve_commit`, a module-private helper, out of `agentmarshal.journal.gate` into the CLI layer. The design records this as a deliberate choice, and `gate_context.py:15` sets a precedent, but `gate_context` also already wraps that helper in public functions (`resolve_current_head`, `resolve_default_base`), and `review.py:250` keeps a second, independently-worded copy of the same resolution. A public `resolve_commit` would have given the CLI a supported entry point and one place for the refusal wording; as written, a change to `gate._resolve_commit`'s contract silently reaches a command. Non-blocking: the behaviour is correct today.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9fcc2ce115d2d8fa37d83e6110e912d349237ad1", "verdict": "approved", "findings": [], "advisory_findings": ["AD-1"]}
AGENTMARSHAL_VERDICT_END
