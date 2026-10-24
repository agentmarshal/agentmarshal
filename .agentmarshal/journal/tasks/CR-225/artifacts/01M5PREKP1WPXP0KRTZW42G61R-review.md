Прочитал контракт, дифф и реальные файлы снапшота. Запускать интерпретатор/тесты в этой среде нельзя (bash-вызовы `python3`/`uv` отклоняются), поэтому проверка — чтением кода; результат CI беру из примечания координатора и ни одного падения инструментов не утверждаю.

## Как закрыты acceptance criteria

**Критерий 1 (change + delta + архив + тест на каждый сценарий) — выполнен.** `openspec/changes/complete-runs-stages/` архивирован как `openspec/changes/archive/2026-10-24-complete-runs-stages/` с `proposal.md`, `design.md`, `tasks.md` и дельтой `specs/extension-stages/spec.md`; те же ADDED-требования дописаны в `openspec/specs/extension-stages/spec.md:1227-1390` (так выглядит результат `openspec archive`, как и у соседних `2026-10-24-*`). Сценариев в дельте 15, тестов в `tests/test_complete_stages.py` 15, docstring каждого дословно называет свой сценарий и порядок совпадает.

**Критерий 2 (один runner, транскрипт `stage run` не меняется, pre-gate до gate и до записи) — выполнен.** `stages.run_stages` (`src/agentmarshal/stages.py:758`) принимает placement/state/task/commit/base/phase/stderr и возвращает `StageRunResult`; `_run_stages` (`stages.py:1148`) остался тонкой обёрткой, которая печатает no-stage-строку и per-entry pause-строки — `tests/test_stages.py` диффом не тронут, а `test_stage_runs_transcript_is_unchanged_by_the_shared_runner` пинит обе ветки транскрипта. Вызов `pre-gate` стоит в `cli.py:1085`, после `load_task_for_record` и до `complete_task`; демонстрирует `test_the_pre_gate_stages_run_before_the_gates_transcript_and_before_any_write` (строки стейджа раньше `PASS:`) и `test_a_run_whose_machinery_refused_refuses_the_completion` (ничего не записано). `test_both_commands_go_through_the_one_runner` показывает ровно два вызова `run_stages`: `pre-gate`, `post-gate`.

**Критерий 3 (пауза: refusal пока не смержено, warning когда смержено) — выполнен по механике.** `_candidate_merged` (`cli.py:999`) делает `git merge-base --is-ancestor` по разрешённым через `_resolve_commit` ссылкам и fail-closed возвращает `False` на `GateError`/`OSError`; ветки refusal/warning — `cli.py:1094-1116`. Демонстрируют `test_a_pause_while_the_candidate_is_not_an_ancestor_refuses_the_completion` (exit 3, ничего не записано), `test_the_pause_line_names_every_paused_stage` (порядок alpha→zeta в одной строке) и `test_a_pause_on_an_already_merged_candidate_is_a_warning`. Оговорка — в F2.

**Критерий 4 (post-gate после записи, нейтральность, проект без стейджей, `--findings`) — выполнен, кроме края из F1/F4.** Вызов `post-gate` в `cli.py:1166-1178` под `state is not None`, то есть только для embedded-ветки с кандидатом, и его статус отбрасывается; демонстрируют `test_the_post_gate_stages_run_after_the_completed_record_is_written` (строки стейджа после `completed`, `extension-event` с `phase=post-gate`) и `test_a_post_gate_result_changes_neither_the_record_nor_the_exit_status` (стейдж падает с 9, complete = 0). Тишину пустого плана пинит `test_a_plan_matching_no_stage_prints_nothing` (`captured.err == ""`), лейны без стейджей — `test_the_findings_lane_invokes_no_stage` и `test_a_sidecar_invokes_no_stage`.

**Критерий 5 (gate не меняется, accepted pause как в `stage run`, экранирование, других команд не трогаем) — выполнен.** `journal/complete.py` и `journal/gate.py` диффом не затронуты; чтение acceptance осталось внутри `run_stages` (`stages.py:1002-1030`), второго чтения в `complete` нет — демонстрирует `test_an_accepted_pause_stands_down_in_complete_as_in_stage_run`. Новые строки `complete` печатают только уже экранированные элементы `pauses` (`shown = escape_for_display(name)`, `stages.py:1086`). Про прохождение полного CI-прогона полагаюсь на примечание координатора, сам его не запускал.

## Находки

**F1-complete-refs-blamed-on-stage-run (blocking, contract-mismatch).** В embedded-ветке `run_stages` — первый вызов, который трогает git, и его `_resolve_commit` (`stages.py:795`) на неразрешимом `--commit`/`--base` печатает `stage run: git rev-parse … failed: …` и возвращает статус 1 (`stages.py:820-822`), после чего `complete` добавляет `complete: pre-gate stage run refused; task not completed` (`cli.py:1110-1115`); раньше ту же опечатку в ref'е репортил сам gate через `LifecycleError`. Это происходит в любом embedded-проекте, в том числе в проекте без единого extension, то есть прямо противоречит критерию 4 («prints exactly what `complete` prints today») и требованию дельты «A plan matching no stage SHALL print nothing» — и сообщение валит на extension то, что к нему отношения не имеет; ни один тест этот путь не покрывает (в `tests/` нет ни одного `complete` с неразрешимым ref'ом).

**F2-merged-warning-never-completes (advisory, contract-mismatch).** Ветка warning в `cli.py:1095-1103` проходит дальше к gate, но если кандидат — предок базы, то `merge-base(base, candidate) == candidate`, диапазон пуст и gate безусловно отказывает на `candidate range contains no changes` (`src/agentmarshal/journal/gate.py:1194-1195`), так что обещанное критерием 3 «the completion proceeds» недостижимо: собственный тест `test_a_pause_on_an_already_merged_candidate_is_a_warning` ассертит exit 1 и отсутствие записи `completed`. Дизайн это признаёт, а критерий 5 запрещает трогать gate, поэтому помечаю как advisory, но человеку стоит решить, достаточно ли «proceeds to the gate» для ADR-0013 decision 2.

**F3-run-stages-never-writes-docstring (advisory, claim-accuracy).** Новый docstring `run_stages` — «Run every shared extension stage matching *phase*; never writes.» (`stages.py:767`) — неверен буквально: функция дописывает `extension-event` в process log через `record_event`/`write_event` (`stages.py:925-985`), что и проверяет `test_the_post_gate_stages_run_after_the_completed_record_is_written`; модульный docstring формулирует это точно («nothing is written to the **journal**», `stages.py:22-23`), и однострочник стоит привести к той же формулировке, тем более что на «nothing is written» опирается ветка отказа `complete`.

**F4-operational-line-in-complete (advisory, contract-mismatch).** Проверка operational-лейна стоит до возврата пустого плана (`stages.py:806-818`), поэтому при завершении operational CR строка `stage run: pre-gate stages do not run on an operational change` попадает в stdout `complete` даже в проекте, где ни один shared extension не объявляет стейдж (манифесты к этому моменту ещё не читались) — это снова расходится с критерием 4, хотя сценарий дельты «an operational change's completion skips the pre-gate stages» и пинящий его `test_an_operational_changes_completion_skips_the_pre_gate_stages` эту строку прямо санкционируют; расхождение внутри самого контракта, решать человеку.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "80ff1fdaf395f12c626826d15955f5f98c5298a0",
  "verdict": "changes_required",
  "findings": ["F1-complete-refs-blamed-on-stage-run"],
  "advisory_findings": [
    "F2-merged-warning-never-completes",
    "F3-run-stages-never-writes-docstring",
    "F4-operational-line-in-complete"
  ],
  "classes": {
    "F1-complete-refs-blamed-on-stage-run": "contract-mismatch",
    "F2-merged-warning-never-completes": "contract-mismatch",
    "F3-run-stages-never-writes-docstring": "claim-accuracy",
    "F4-operational-line-in-complete": "contract-mismatch"
  },
  "verification": {
    "read": [
      "src/agentmarshal/cli.py:996-1180 (_candidate_merged, _run_complete)",
      "src/agentmarshal/stages.py:1-170 (module docstring, imports)",
      "src/agentmarshal/stages.py:403-470, 530-580 (_prepare_extension, _run_stage)",
      "src/agentmarshal/stages.py:737-1171 (StageRunResult, run_stages, _run_stages)",
      "src/agentmarshal/journal/complete.py:46-78 (complete_task)",
      "src/agentmarshal/journal/gate.py:288-342, 968-1016, 1180-1196",
      "src/agentmarshal/journal/status.py:164-185 (load_task_for_record)",
      "src/agentmarshal/localstate.py:1-120 (local_state creates nothing)",
      "tests/test_complete_stages.py (all 15 tests)",
      "tests/test_stages.py:1-200, 365-395 (helpers, invalid task id)",
      "openspec/specs/extension-stages/spec.md:1224-1390",
      "openspec/changes/archive/2026-10-24-complete-runs-stages/{proposal.md,design.md,tasks.md,specs/extension-stages/spec.md}",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:60-90, 275-288",
      "CHANGELOG.md:1-60, docs/threat-model.md:161-176"
    ],
    "executed": [
      {"what": "ls openspec/changes; ls openspec/changes/archive", "result": "only archive/ remains; 2026-10-24-complete-runs-stages present with proposal.md, design.md, tasks.md, specs/"},
      {"what": "grep -c '^#### Scenario:' delta spec; grep -c '^def test_' and docstring count in tests/test_complete_stages.py", "result": "15 / 15 / 15"},
      {"what": "grep -rn 'complete' tests/test_gate_operational.py tests/test_switch_off.py; grep -rn 'does not resolve' tests/*.py", "result": "no existing test completes an operational change and none pins complete's transcript for an unresolvable ref"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "this session may not execute interpreters or package tools (bash calls to python3/uv are refused); CI result taken from the coordinator's note"},
      {"what": "git show / diff against the parent commit", "why": "the snapshot is not a git repository"}
    ]
  },
  "evidence": {
    "F1-complete-refs-blamed-on-stage-run": "src/agentmarshal/cli.py:1084-1115 calls stages.run_stages before any gate work; src/agentmarshal/stages.py:793-822 resolves the refs first and returns StageRunResult(1) after printing 'stage run: <GateError>' (src/agentmarshal/journal/gate.py:298-302 raises it for a failed rev-parse); the empty-plan return that is supposed to keep a no-stage project silent is only reached later at src/agentmarshal/stages.py:851. grep over tests/ for 'does not resolve' shows no complete-lane test.",
    "F2-merged-warning-never-completes": "src/agentmarshal/cli.py:1095-1103 (warning, then fall through to complete_task) vs src/agentmarshal/journal/gate.py:1184-1195 ('candidate range contains no changes' when merge_base == candidate); tests/test_complete_stages.py:~470 asserts `_complete(head, 'master') == 1` and no completed record.",
    "F3-run-stages-never-writes-docstring": "src/agentmarshal/stages.py:767 'never writes' vs src/agentmarshal/stages.py:925-985 record_event/write_event appending extension-event, and the module docstring's precise wording at src/agentmarshal/stages.py:21-23 ('nothing is written to the journal').",
    "F4-operational-line-in-complete": "src/agentmarshal/stages.py:806-818 prints the operational line before manifests are read and before the empty-plan return at src/agentmarshal/stages.py:851; tests/test_complete_stages.py asserts that line in complete's stdout in test_an_operational_changes_completion_skips_the_pre_gate_stages, while acceptance criterion 4 and openspec/specs/extension-stages/spec.md:1291-1295 promise a no-stage project reads exactly as complete reads today."
  }
}
AGENTMARSHAL_VERDICT_END
