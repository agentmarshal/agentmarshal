Проверил diff против контракта, ADR-0005/0008 и спеков. Тесты запустить не смог (нет разрешения на запуск pytest в этой сессии), поэтому анализ статический.

Коротко: ядро задачи сделано — `LeakHit`/`render_leak_hits` общий для standalone и gate, self-match по `config_path`, маркер по позиции, `safe_path` для путей, stderr ревьюера сохраняется вне журнала, README outbox'а. Все сценарии из `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/` закрыты тестами с именующими docstring'ами, byte-for-byte gate-транскрипт не затронут (чистый репозиторий, WARN не печатается). Но есть один реальный регресс на success-пути ревью и три замечания поменьше.

F-001: `_keep_diagnostics` at `src/agentmarshal/journal/review.py:327` raises `ReviewLaunchError` when `mkstemp` fails, and it is called at `src/agentmarshal/journal/review.py:606` before the verdict is parsed and before `submit_review` writes anything — so a reviewer run that exited zero with a valid verdict is thrown away entirely because a warning could not be written to a temp file; its own comment on line 334 says "preservation is best effort", and the sibling `_preserve_output`/`_reject` path at line 355-358 degrades instead of raising, as does the dry run's own `except OSError` at line 500.

A-001: `safe_path` at `src/agentmarshal/journal/capture.py:298` masks a path only when it contains a configured private marker, so a path that itself matches a built-in signature is printed verbatim by `render_leak_hits` — the shape already exists as a fixture at `tests/test_capture.py:259` (`+++ b/AKIAIOSFODNN7EXAMPLE`), and adding one leaky added line to that file would make the scan print the key it exists to keep out of CI logs.

A-002: the suppression key `.agentmarshal/project.json` now lives in three independent places — `capture._PROJECT_CONFIG_PATH` at `src/agentmarshal/journal/capture.py:277`, `gate._PROJECT_FILE` at `src/agentmarshal/journal/gate.py:52`, and an inline literal at `src/agentmarshal/cli.py:1294` — so the "cannot drift" property the task bought for rendering was not bought for the thing that decides whether a hit is dropped; the CLI's embedded branch could simply omit the keyword and inherit the constant.

A-003: `openspec/specs/leak-scan/spec.md` publishes the requirement unconditionally ("A leak-scan hit SHALL name the file it matched in and what matched"), but `scan_for_leaks` and `assert_no_leaks` at `src/agentmarshal/journal/capture.py:317` and `:336` still return and print a bare category with no file, and `design.md` names only the two diff callers without recording that the artefact-refusal path keeps the old shape — the capability spec now claims more than the code does.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "30176f407593324f0d2e8ef7e52f61a467bab005",
  "verdict": "changes_required",
  "findings": ["F-001"],
  "advisory_findings": ["A-001", "A-002", "A-003"]
}
AGENTMARSHAL_VERDICT_END
