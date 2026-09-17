Проверил `9681bb5` статически (запуск pytest здесь заблокирован — выводы ниже получены чтением кода и тестов). Дальше — по-английски, как требует языковое правило проекта для записей.

**Review of CR-100 at `9681bb563e63894f7c37ad447766c500496e62da`**

What I verified as correct: the hit record never carries matched text or a marker value; `safe_path` also covers the marker-in-path case; the standalone command and the gate share `render_leak_hits`, and `tests/test_gate.py:1762` pins both lines against the same `detail` string; the self-match narrowing is bounded by path and by "sole occurrence", and the gate's `config_path=""` in a sidecar keeps the narrowing from firing on host content; the zero-exit reviewer stderr lands in the system temp directory (`TMPDIR`-isolated in the tests), outside any journal, with the path on stderr, and the silent case writes and says nothing; `tests/test_gate.py` byte-for-byte 0.3.0 transcript test is untouched and its candidate is clean, so no WARN line enters it. The two existing parser tests that now assert `LeakHit(...)` still hold under the new per-file attribution, including `+++ b/AKIAIOSFODNN7EXAMPLE` being consumed as a path rather than content.

Two things do not hold.

`spec-leak-scan-delta-not-applied`: `openspec/specs/leak-scan/spec.md` is missing material that the archived delta `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/leak-scan/spec.md:6` declares under `## ADDED Requirements` — the sentence "A path that itself contains a configured marker SHALL NOT be printed either, and SHALL be described in the same way the marker is." and the whole scenario "a path that carries a marker is described, not printed". The sibling capability in the same change, `openspec/specs/reviewer-adapter/spec.md:53`, is character-for-character identical to its delta, so this is a divergence, not a house style. The result is that `safe_path` (`src/agentmarshal/journal/capture.py:298`) implements a redaction the living spec does not require, and an operator reading `openspec/specs/leak-scan/` is told less than the scan actually guarantees.

`path-scenario-has-no-test-that-names-it`: acceptance 1 asks that every scenario in `openspec/changes/adopter-small-defects/specs/` be demonstrated by a test whose docstring names it. Seven of the eight do — `tests/test_capture.py:317`, `:392`, `:410`, `:425`, `tests/test_gate.py:1766`, `tests/test_review_launcher.py:659`, `:691` all open with `"""Scenario: <name>."""`. The eighth, `tests/test_capture.py:334` `test_a_path_that_carries_a_marker_is_not_printed_either`, carries a rationale docstring instead and never names "a path that carries a marker is described, not printed". The test itself is correct and does demonstrate the scenario; only the naming the contract asks for is absent.

Two advisory notes.

`leak-scan-command-config-path-diverges-from-gate`: `src/agentmarshal/journal/gate.py:1137` deliberately passes `config_path=_PROJECT_FILE if not sidecar else ""`, but `src/agentmarshal/cli.py:1287` calls `scan_diff_for_leaks(diff_text, markers)` and so always uses the `.agentmarshal/project.json` default, including in a sidecar where the markers came from `markers_from_config(sidecar_config)` and the diff is the host's. The comment at `src/agentmarshal/cli.py:1257` acknowledges that a sidecar host may have a `project.json` of its own; for such a host, a marker occurring only there is reported by the gate and silently dropped by the command. Narrow, but it is the one input on which the two surfaces can still diverge.

`diagnostics-preservation-failure-aborts-the-review`: `src/agentmarshal/journal/review.py:333` marks itself `# pragma: no cover - preservation is best effort` and then raises `ReviewLaunchError` on `OSError`. In `launch_review` that runs after the reviewer has already produced a parseable verdict, so a temp-file write failure discards a paid review rather than degrading. The established pattern next door, `_reject` at `src/agentmarshal/journal/review.py:352`, degrades instead: `(raw output could not be kept: {error})`. Matching it would keep the failure non-fatal.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9681bb563e63894f7c37ad447766c500496e62da",
  "verdict": "changes_required",
  "findings": [
    "spec-leak-scan-delta-not-applied",
    "path-scenario-has-no-test-that-names-it"
  ],
  "advisory_findings": [
    "leak-scan-command-config-path-diverges-from-gate",
    "diagnostics-preservation-failure-aborts-the-review"
  ]
}
AGENTMARSHAL_VERDICT_END
