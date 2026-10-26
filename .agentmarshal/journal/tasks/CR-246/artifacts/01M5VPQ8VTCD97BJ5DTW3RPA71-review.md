Разобрал контракт и diff статически (файлы читал, не менял). Запустить проверки в этой песочнице не удалось — `uv`/`pytest` недоступны, снапшот не git-репозиторий, так что про CI полагаюсь на твою заметку и на чтение кода.

## Acceptance criteria — где diff их выполняет

**AC1 (file-form manifest читается base-tree reader'ом).** `src/agentmarshal/stages.py:335-351` — `_base_manifests` получает `extension_names` целиком (а не только `directory_names`) и гонит каждое имя через `_manifest_from_tree`; вызовы на `:1106` и `:1118`. Демонстрируют `tests/test_stages.py::test_a_broken_file_form_manifest_at_the_base_fails_the_run` и `::test_a_command_declaring_file_form_manifest_at_the_base_fails_the_run`, через общий runner — `tests/test_complete_stages.py::test_a_file_form_manifest_the_base_refuses_fails_the_completion`. «File-form всё ещё не планирует stage» держится `tests/test_stages.py::test_a_file_form_extension_has_no_stage_to_run` (не изменён) и структурно: `journal/extensions.py:525-545` `_refuse_single_file_directory_paths` отказывает любому file-form манифесту, назвавшему `[[stage]].command`, так что well-formed file-form физически не может нести stage. Собственный `openspec.toml` этого репозитория (schema 1, без stage/lock) под новым чтением проходит.

**AC2 (маскирование пути в diagnostic'е leak-scan).** `src/agentmamarshal/cli.py:1789-1793` — `escape_for_display(safe_path(str(error), markers))`, порядок как требует контракт; `markers` в scope с `:1737`. Демонстрирует `tests/test_leak_scan_acknowledgements.py::test_a_marker_in_a_task_directory_name_is_masked_in_the_diagnostic` (`TaskStatusError(ValueError)` из `journal/status.py:212` ловится веткой `ValueError`).

**AC3 (`--skip-ext` с shared-именем на operational lane).** `stages.py:1054-1076` — `_extension_names_at_tree(...)[0]` и затем отказ, оба до `operational_candidate` на `:1078`; манифесты не читаются. Демонстрируют `tests/test_gate_operational.py::test_a_shared_name_in_skip_ext_is_refused_on_the_operational_lane` и `::test_complete_skip_ext_naming_a_shared_extension_is_refused_on_the_lane` (оба с намеренно битым манифестом и `assert "invalid TOML" not in captured.err`). Старый сценарий `test_a_broken_extension_cannot_block_the_operational_change` не ломается: enumeration читает только listing.

**AC4 (runtime lookup раскрыт).** `docs/threat-model.md:506-513` и `CHANGELOG.md:347-353`. Проверил по коду: `stages.py:180` `_MINIMAL_PATH = "/usr/bin:/bin"`, grep `runtime` по `stages.py` пуст, `doctor.py:575` действительно даёт check `extension runtime <name>`, ADR-0013 decision 13 amended (`docs/adr/ADR-0013…:229-242`) — цитата «the command runs as an argv process under the core's interpreter» существует в `openspec/specs/extension-stages/spec.md:174`. Документация, теста не требует.

**AC5 (git 2.31).** `README.md:117-122`, `docs/quickstart.md:19-23`, `docs/sidecar.md:83-87`. Сходится с кодом: `doctor.py:72` `MINIMUM_GIT_VERSION = (2, 31)` с той же мотивировкой, `project.py:400-412` действительно зовёт `--path-format=absolute`; утверждение «`status` всё равно работает, показывая пути как unavailable» подтверждается `cli.py:1469-1475` + `localstate.py:113-122` (`LocalStateError` → degraded-строки), а `resolve_placement` local state не трогает.

**AC6 (audit-файл).** `release/audit-0.6.0.toml:134-162` — ровно пять `[[finding]]` (`SOL-extensions-1`, `SOL-extensions-2`, `SOL-commands-2`, `SOL-docs-claims-1-1`, `SOL-docs-claims-1-3`), `disposition = "fixed"`, `task = "CR-246"`, с комментарием про gpt-6.1-sol после release audit; `CHANGELOG.md:227` называет CR-246 в заголовке audit-fixes. Сам `check_release_audit.py v0.6.0` я не запускал (нет git-репозитория и тега; к тому же `.agentmarshal/journal/tasks/CR-246/records/` пока содержит только `opened` + две `amendment`, а скрипт требует `completed` в tagged tree — это появится после завершения задачи). Статически проверил главное, что скрипт считает: каждый путь diff'а покрыт либо `ALWAYS_ALLOWED`, либо scope CR-246 по правилу `_covered`.

**AC7 (UPGRADING + README).** `UPGRADING.md:55-65` в секции «0.5.0 → 0.6.0»; сходится с `outbox.py:832-851` (`_pinned_blob`: `--path` против `--no-filters`), `:879-929` (`_transform_cause`: `filter`/`text`/`eol`/`core.autocrlf`), `:1023-1046` (`_batch_mismatch` перед batch-commit'ом), и строка-ремедия `` `.agentmarshal/upstream/** -text` `` совпадает с кодовой байт-в-байт (`_OUTBOX_DIR_SPEC` = `.agentmarshal/upstream`). `README.md:53-54` — новая формулировка верна по `journal/review.py:813-824` + `_preserve_output:599`: сохранение raw output висит на launcher-отказе и не зависит от capture level.

**AC8 (MODIFIED-блок и архив).** Дельта `openspec/changes/archive/2026-10-26-operational-skip-ext-refusal/specs/extension-stages/spec.md` несёт heading и текст requirement'а, совпадающие с `openspec/specs/extension-stages/spec.md:30-117`, все восемь прежних сценариев плюс новый; обе новые проверки в `test_gate_operational.py` имеют docstring `"""Scenario: a shared name in --skip-ext is refused before the operational-lane exception."""`; `openspec/changes/` содержит только `archive`, висячего change-каталога нет. Версию самого OpenSpec-инструмента проверить нечем.

**AC9.** Регрессий статически не нашёл: `_base_extensions` нигде больше не упоминается, ни один существующий тест не кладёт в base file-form манифест со stage или lock (`test_gate.py:149`, `test_pause_and_operational_acceptance.py:747` — оба без stage), порядок refusal'ов `stage run` (task-id → sidecar → skip-ext → lane) спецификацию не нарушает. Полную CI-последовательность не прогонял.

## Advisory

**SOL-docs-claims-1-1-gate-lanes** — после этого изменения активная спека `openspec/specs/gate-lanes/spec.md:344-352` («pre-gate stages do not run on an operational change») утверждает без оговорок, что `stage run --phase pre-gate` на operational-кандидате «SHALL print one line … and SHALL run no stage … returning success», а код (`src/agentmarshal/stages.py:1063-1076`) теперь при `--skip-ext <shared name>` печатает отказ и выходит с 1 — то есть ровно тот рассинхрон между спекой и реализацией, который SOL-docs-claims-1-1 нашёл в `extension-stages`, остался в её соседке; `openspec/specs/gate-lanes/` не входит в scope CR-246, так что это departure для финального отчёта, а не правка здесь.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "7bf939b4d46a5743506029f7537e4956b05d9b63",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["SOL-docs-claims-1-1-gate-lanes"],
  "classes": {
    "SOL-docs-claims-1-1-gate-lanes": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"_base_extensions|_base_manifests\" src/ tests/ docs/", "result": "only stages.py:335 definition and the two call sites at 1106 and 1118; no stale references"},
      {"what": "grep -rn \"_MINIMAL_PATH\" src/agentmarshal/stages.py", "result": "_MINIMAL_PATH = \"/usr/bin:/bin\" at :180, used at :707 and :1183"},
      {"what": "grep -n \"runtime\" src/agentmarshal/stages.py", "result": "no match — stage run performs no runtime lookup, as the threat model and CHANGELOG now state"},
      {"what": "grep -rn \"extension runtime\" src/ docs/", "result": "doctor.py:524,575 register the `extension runtime <name>` check; threat-model.md:510 cites it"},
      {"what": "grep -rn -- \"path-format\" src/ docs/ README.md", "result": "project.py:407 calls it; doctor.py:70-72,144,151 pins MINIMUM_GIT_VERSION=(2,31) with the same rationale; README.md:119, quickstart.md:21, sidecar.md:85 now name it"},
      {"what": "grep -rn \"unavailable\" src/agentmarshal/cli.py", "result": "cli.py:1467-1475 degrades the local-state lines rather than failing status, so the docs' `status still runs` claim holds"},
      {"what": "grep -n \"_OUTBOX_DIR_SPEC|_UPSTREAM_DIR|PROJECT_DIR_NAME\" src/agentmarshal/outbox.py src/agentmarshal/project.py", "result": "resolves to .agentmarshal/upstream, so UPGRADING's `.agentmarshal/upstream/** -text` matches outbox.py:921 byte for byte"},
      {"what": "grep -rn \"invalid TOML\" src/agentmarshal/", "result": "journal/extensions.py:383 produces `invalid TOML extension manifest: {source}`, the text the new complete test asserts under the `complete:` voice"},
      {"what": "grep -rn \"invalid task directory\" src/", "result": "journal/status.py:212 raises TaskStatusError(ValueError) carrying the path — reached by the leak-scan except clause and now masked"},
      {"what": "ls openspec/changes/ and openspec/changes/archive/", "result": "only `archive`; 2026-10-26-operational-skip-ext-refusal present, no leftover live change directory"},
      {"what": "ls .agentmarshal/journal/tasks/CR-246/records/", "result": "opened + two amendment records; no `completed` record yet, so check_release_audit.py would still refuse at this commit by design"}
    ],
    "read": [
      "src/agentmarshal/stages.py:260-420,960-1230,1558-1600",
      "src/agentmarshal/cli.py:28-45,1652-1856",
      "src/agentmarshal/journal/gate.py:610-731,945-1103,1570-1610",
      "src/agentmarshal/journal/extensions.py:495-575",
      "src/agentmarshal/journal/capture.py:312-371",
      "src/agentmarshal/journal/review.py:588-625,805-825,1255-1305",
      "src/agentmarshal/journal/status.py:196-219",
      "src/agentmarshal/localstate.py:100-123",
      "src/agentmarshal/project.py:380-425",
      "src/agentmarshal/doctor.py:60-158",
      "src/agentmarshal/outbox.py:820-930,1023-1046",
      ".github/scripts/check_release_audit.py",
      "release/audit-0.6.0.toml",
      "openspec/specs/extension-stages/spec.md:1-120",
      "openspec/specs/gate-lanes/spec.md:336-368",
      "openspec/specs/leak-scan/spec.md:1-60",
      "openspec/changes/archive/2026-10-26-operational-skip-ext-refusal/specs/extension-stages/spec.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:225-250",
      "UPGRADING.md:1-70",
      ".agentmarshal/extensions/openspec.toml",
      "tests/test_stages.py:27-160,320-421",
      "tests/test_complete_stages.py:1-60,225-298",
      "tests/test_gate_operational.py:32-57,700-815",
      "tests/test_leak_scan_acknowledgements.py:29-110,302-330",
      "tests/test_personal_extensions.py:1-60,855-925",
      "tests/test_gate.py:149-170",
      "tests/test_pause_and_operational_acceptance.py:747-766",
      "tests/test_extension_trust.py:290-335"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "uv and pytest are not installed in this review sandbox and command execution is restricted; relying on the coordinator's statement that the sequence passed at this commit"},
      {"what": "python3 .github/scripts/check_release_audit.py v0.6.0 in a throwaway clone with a local tag", "why": "the snapshot is not a git repository, has no v0.6.0 tag, and CR-246 has no `completed` record yet; verified statically instead that every changed path is covered by ALWAYS_ALLOWED or CR-246's contract scope under _covered"},
      {"what": "confirming the archive was produced by OpenSpec 1.15.0 specifically", "why": "the tool version is not recorded in the tree; only the resulting file layout and the pinned version in .agentmarshal/extensions/openspec.toml are observable"}
    ]
  },
  "evidence": {
    "SOL-docs-claims-1-1-gate-lanes": "openspec/specs/gate-lanes/spec.md:344-352 states that `stage run --phase pre-gate` on an operational candidate `SHALL print one line saying pre-gate stages do not run on an operational change and SHALL run no stage - no extension event, no pause - returning success`, with no exception for --skip-ext; src/agentmarshal/stages.py:1063-1076 now prints `<voice>: <name>: a shared extension is switched off only by an operational task (extension switch off)` and returns StageRunResult(1) before operational_candidate() at :1078 is consulted. tests/test_gate_operational.py:746-775 asserts exactly that exit 1 and that the operational line does not print. The parallel extension-stages requirement was amended (openspec/specs/extension-stages/spec.md:44-48); gate-lanes was not, and openspec/specs/gate-lanes/ is outside CR-246's scope."
  }
}
AGENTMARSHAL_VERDICT_END
