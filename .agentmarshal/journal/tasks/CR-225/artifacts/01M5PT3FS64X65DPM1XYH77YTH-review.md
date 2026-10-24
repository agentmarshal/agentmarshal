Прочитал код и документы на месте; тесты и CI-последовательность здесь запустить нельзя (нет venv, каталог не git-репозиторий), поэтому по прохождению CI опираюсь на заметку координатора.

**По критериям приёмки — где дифф их выполняет:**

1. **Change + архив + сценарии.** Выполнен: `openspec/changes/archive/2026-10-24-complete-runs-stages/` содержит `proposal.md`, `design.md`, `tasks.md` и delta-спеку `specs/extension-stages/spec.md`; `openspec/changes/` больше не содержит рабочего каталога (только `archive/`), т.е. архивация прошла командой; 210 строк ADDED-требований пришиты в `openspec/specs/extension-stages/spec.md:1228-1433`. Все 17 сценариев delta-спеки закрыты тестами с docstring, который их называет, в `tests/test_complete_stages.py` (один — слабо, см. F4).
2. **Один runner, `stage run` без изменений, `pre-gate` до gate и до записи.** Выполнен: `stages.run_stages` (`src/agentmarshal/stages.py:758`) и тонкая обёртка `_run_stages` (`stages.py:1195`), которая сама печатает no-stage-строку и pause-строки; `complete` зовёт его на `pre-gate` после `load_task_for_record` и до `complete_task` (`cli.py:1109`). Демонстрируют `test_stage_runs_transcript_is_unchanged_by_the_shared_runner`, `test_both_commands_go_through_the_one_runner`, `test_the_pre_gate_stages_run_before_the_gates_transcript_and_before_any_write`, `test_a_run_whose_machinery_refused_refuses_the_completion` плюс нетронутый `tests/test_stages.py`. Оговорка — F2.
3. **`--target`, pause отказывает пока не смержено, warning после.** Выполнен: флаг — `cli.py:353`, проверка — `_candidate_merged` (`cli.py:1004`, fail-closed на `GateError`/`OSError`), развилка — `cli.py:1119-1141`, статус паузы 3 возвращается из `stages.py:1190`. Демонстрируют `test_a_pause_while_the_candidate_is_not_an_ancestor_refuses_the_completion`, `test_the_pause_line_names_every_paused_stage` (нерешаемый `--target` → пауза стоит), `test_a_pause_on_an_already_merged_candidate_is_a_warning`, `test_an_accepted_pause_stands_down_in_complete_as_in_stage_run`.
4. **`post-gate` после записи, нейтральный к verdict; проект без stage печатает то же; `--findings` не запускает stage.** Выполнен: `cli.py:1200` после `print("completed")`, статус отброшен; `state is None` на findings- и sidecar-ветках. Демонстрируют `test_the_post_gate_stages_run_after_the_completed_record_is_written`, `test_a_post_gate_result_changes_neither_the_record_nor_the_exit_status`, `test_a_plan_matching_no_stage_prints_nothing`, `test_the_findings_lane_invokes_no_stage`, `test_a_sidecar_invokes_no_stage` и нетронутые существующие complete-тесты. Оговорка — F3.
5. **Gate не изменён, escaping, другие команды не менялись.** Выполнен: `journal/gate.py` и `journal/complete.py` в диффе отсутствуют; `base`/`commit` у `run_gate` используются только как аргумент `_resolve_commit` (`gate.py:1183-1184`), поэтому передача уже разрешённых SHA из `cli.py` эквивалентна; pause-записи собираются из `escape_for_display`-значений (`stages.py:1177`), так что строки `complete:` экранированы; `run_stages` вызывается только из `stage run` и `complete`.

**Находки (все advisory, ни одна не блокирует):**

**F1** — `openspec/changes/archive/2026-10-24-complete-runs-stages/proposal.md:26` всё ещё утверждает, что пауза решается «while the candidate is not an ancestor of the resolved **base**», и нигде не упоминает `--target`; это прямо противоречит поправке к контракту от 2026-10-24 («Merged-ness is decided against a new --target ref, not --base»), собственной `design.md` (её блок «Amended 2026-10-24»), delta-спеке и реализации (`cli.py:1121` передаёт `args.target`).

**F2** — в `stage run` изменился порядок отказов: `validate_task_id` переехал внутрь `run_stages` (`stages.py:802`), а обёртка сначала вызывает `_resolve(stderr)` (`stages.py:1204`), поэтому `stage run --task "not a task"` вне инициализированного проекта теперь печатает «agentmarshal stage run must be run inside an initialized project…» (`stages.py:269`) вместо прежнего отказа по task id; это расходится с добавленным же требованием «unchanged byte for byte» — существующий тест `test_an_invalid_task_identifier_refuses_before_any_stage_is_planned` эту комбинацию не покрывает, так как работает внутри проекта (exit-статус 1 в обоих случаях).

**F3** — вызов `post-gate` в `cli.py:1200` стоит вне `try/except` блока `_run_complete`, тогда как `run_stages` гасит почти всё, но не `tempfile.TemporaryDirectory(prefix="agentmarshal-stage-")` (`stages.py:1115`): в проекте, объявляющем только `post-gate` stage (pre-gate-план пуст, временный каталог ещё не создавался), неудача создания временного каталога даст traceback уже после записи `completed` — запись останется, а exit-статус изменится, что нарушает добавленное требование «its outcome SHALL change neither the record nor the exit status» (ADR-0013 решение 4).

**F4** — `tests/test_complete_stages.py:155-185` носит docstring сценария «both commands go through the one runner», но под spy прогоняет только `complete` (`assert calls == ["pre-gate", "post-gate"]`) и ни разу не вызывает `stage run`, так что половина сценария про `stage run` этим тестом не демонстрируется (косвенно её закрывает соседний transcript-тест).

**F5** — документированный post-merge-поток завершения в `docs/self-hosting-workflow.md:43-50` («Completion may run before or after the implementation merges») вызывает `complete --task --commit --base` без `--target`, а при отсутствии `--target` кандидат читается как не-смерженный, поэтому для адоптера, следующего документации, ветка warning после мержа недостижима и любая пауза `pre-gate-stop` отказывает уже смерженному кандидату; `docs/` вне scope контракта, так что правка здесь невозможна — это нужно назвать departure/follow-up.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4e78bacf4b9efb1d0b2f2e7e84ca3c99a0275875",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["F1", "F2", "F3", "F4", "F5"],
  "classes": {
    "F1": "claim-accuracy",
    "F2": "claim-accuracy",
    "F3": "correctness",
    "F4": "test-gap",
    "F5": "scope"
  },
  "verification": {
    "read": [
      "src/agentmarshal/cli.py (_build_parser complete flags, _candidate_merged, _run_complete, imports)",
      "src/agentmarshal/stages.py (StageRunResult, run_stages, _run_stages, _resolve, _base_extensions, _base_switches, _prepare_extension, _run_stage)",
      "src/agentmarshal/journal/complete.py (complete_task, record_commit_completion)",
      "src/agentmarshal/journal/gate.py (run_gate, _resolve_commit, _manifest_from_tree, _manifest_blob_present)",
      "src/agentmarshal/journal/status.py (load_task_for_record)",
      "src/agentmarshal/localstate.py (local_state)",
      "src/agentmarshal/process_log.py (write_event)",
      "src/agentmarshal/isolation.py (probe)",
      "tests/test_complete_stages.py",
      "tests/test_stages.py (helpers and test_an_invalid_task_identifier_refuses_before_any_stage_is_planned)",
      "openspec/specs/extension-stages/spec.md",
      "openspec/changes/archive/2026-10-24-complete-runs-stages/{proposal.md,design.md,tasks.md,specs/extension-stages/spec.md}",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decisions 2-5)",
      "docs/self-hosting-workflow.md, README.md, docs/quickstart.md (complete invocations)"
    ],
    "executed": [
      {"what": "grep -rn 'run_stages' src/ tests/", "result": "only cli.py:1109, cli.py:1200, stages.py:254 and the test spy call it — no other command changed"},
      {"what": "grep -n 'base' src/agentmarshal/journal/gate.py", "result": "the run_gate `base` parameter is used only at gate.py:1184 (_resolve_commit), so passing pre-resolved SHAs is equivalent"},
      {"what": "find openspec/changes/archive/2026-10-24-complete-runs-stages -type f; ls openspec/changes/", "result": "proposal.md, design.md, tasks.md, specs/extension-stages/spec.md; openspec/changes/ holds only archive/"},
      {"what": "grep -n 'ancestor|target|base' archive/.../proposal.md", "result": "line 26: 'the candidate is not an ancestor of the resolved base' — no mention of --target"},
      {"what": "wc -l on the delta and live spec", "result": "210-line delta; openspec/specs/extension-stages/spec.md grew from 1223 to 1433 lines"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "no virtualenv or uv in this environment and python execution was not permitted; CI status taken from the coordinator's note for this commit"},
      {"what": "git diff / git log against the reviewed commit", "why": "the snapshot is not a git repository"}
    ]
  },
  "evidence": {
    "F1": "openspec/changes/archive/2026-10-24-complete-runs-stages/proposal.md:26 'while the candidate is not an ancestor of the resolved base the completion is refused' vs the contract amendment of 2026-10-24, design.md's 'Amended 2026-10-24 (review round 1)' block, openspec/specs/extension-stages/spec.md:1359+ and cli.py:1121 (_candidate_merged(..., args.target))",
    "F2": "stages.py:802 validate_task_id(task_id) now inside run_stages; stages.py:1204 'resolved = _resolve(stderr)' runs first in the wrapper; stages.py:269 prints 'agentmarshal stage run must be run inside an initialized project…'; tests/test_stages.py:372-394 exercises the invalid task id only inside an initialized project",
    "F3": "cli.py:1200 stages.run_stages(..., 'post-gate', ...) sits after the try/except that ends at cli.py:1153-1174; stages.py:1115 'with tempfile.TemporaryDirectory(prefix=\"agentmarshal-stage-\")' is the one call in the loop not wrapped (contrast _prepare_extension at stages.py:431-442 and _run_stage at stages.py:543 which catch everything, and process_log.write_event which converts OSError to ProcessLogError)",
    "F4": "tests/test_complete_stages.py:155-185 — docstring 'Scenario: both commands go through the one runner', body calls only _complete(head, base) and asserts calls == ['pre-gate', 'post-gate']; no _stage_run call under the spy",
    "F5": "docs/self-hosting-workflow.md:43-50 'agentmarshal complete --task <id> --commit <sha> --base <base> … Completion may run before or after the implementation merges' with no --target, against cli.py:1119-1133 where 'args.target is not None and _candidate_merged(...)' is the only path to the warning"
  }
}
AGENTMARSHAL_VERDICT_END
