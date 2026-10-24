## Что я проверил

Прочитал `stages.py` (`run_stages`, `_personal_entries`, `_prepare_personal_extension`, `run_and_report`), `switches.py`, `extension_trust.py` (`read_personal_manifest`, `_run_disable/_run_enable`, дамп switches), `doctor.py`, `_run_complete` в `cli.py`, `journal/extensions.py` (парсер манифеста), `localstate.py`, хелперы `tests/test_stages.py` и ADR‑0013 (решения 9–11, 13, 16) и ADR‑0014. Тесты не запускал: в этой read‑only песочнице нет ни `uv`, ни `pytest` — про прохождение CI опираюсь на твою вводную, сам этого не проверял.

## Acceptance criteria

1. **Change + архив.** `openspec/changes/archive/2026-10-25-personal-extensions/` содержит `proposal.md`, `design.md`, `tasks.md`, `specs/extension-stages/spec.md` — та же раскладка, что у `2026-10-24-complete-runs-stages`, то есть вывод настоящей команды archive; `openspec/changes/` пуст, кроме `archive/`. Все 37 сценариев delta имеют по тесту, чей docstring называет сценарий дословно и в том же порядке (сверил `grep '^#### Scenario:'` против `grep 'Scenario:'` в `tests/test_personal_extensions.py` — 37/37). Тело delta (309 строк требований) дословно дописано в `openspec/specs/extension-stages/spec.md` — md5 совпадает.
2. **Stage run/complete гоняют personal stages из клона.** Планирование — `stages.py:1057-1064` через `_personal_entries` (только при `CI != "true"`), материализация копией — `_prepare_personal_extension`, запуск — тот же `_run_stage`, без grant. Демонстрируют: `test_a_personal_extensions_stage_runs_on_a_workstation_without_a_grant`, `test_the_clones_directory_is_what_runs_never_the_base`, `test_a_personal_stage_is_invoked_at_the_phase_its_manifest_declares`, `test_no_personal_stage_is_planned_or_printed_in_ci`, `test_complete_runs_the_personal_stages_through_the_shared_runner`, `test_a_pausing_personal_pre_gate_stop_stage_pauses_the_local_run_marked_personal`, `test_a_personal_extension_named_like_a_shared_one_is_not_run_and_is_named_on_one_line`.
3. **Forbidden fields, отсутствие journal‑авторитета, doctor.** `read_personal_manifest` (`extension_trust.py:320-325`) режет `footprint`/`documents`/`artifacts` по сырой таблице; `record-ext` не тронут и читает только shared манифесты (`record_ext.py:147`). Демонстрируют: `test_a_personal_manifest_declaring_footprint_documents_or_artifacts_is_refused_and_does_not_run`, `test_doctor_fails_the_check_of_a_personal_manifest_carrying_a_forbidden_field`, `test_record_ext_refuses_a_kind_only_a_personal_manifest_declares`, `test_doctor_lists_a_personal_extension_with_the_scope_personal`, `test_a_personal_stages_extension_event_carries_the_personal_scope`.
4. **Personal switches.** `--skip-ext` на обеих командах, `extension disable/enable` с атомарной записью `.git/agentmarshal/switches.toml`, отказ на shared‑имени одной строкой. Демонстрируют: `test_stage_run_skip_ext_skips_a_personal_extension_for_that_run`, `test_complete_skip_ext_skips_a_personal_extension_for_that_run`, `test_extension_disable_writes_the_off_switch_to_the_clones_switches_toml`, `test_a_disabled_personal_extension_prints_disabled_personal_and_does_not_run`, `test_extension_enable_removes_the_switch_and_the_extension_runs_again`, три теста отказа на shared‑имени, `test_a_name_no_personal_extension_declares_is_inert_for_skip_ext_and_refused_by_disable`.
5. **Клон без personal extension.** Gate не тронут (в diff нет `journal/gate.py`), `cli.py` меняет только `complete`. Демонстрируют: `test_a_clone_with_no_personal_extension_prints_exactly_what_it_prints_today` и `test_the_personal_scope_adds_no_mark_to_a_shared_stages_line` — правда, «byte-identical» они проверяют отсутствием меток scope, а не побайтовым сравнением транскрипта; плюс `test_a_personal_extension_declaring_no_matching_stage_prints_nothing`.

## Findings

**personal-run-fails-on-unreadable-trust** (blocking): в `src/agentmarshal/stages.py` оба ранних возврата теперь пропускают прогон, когда shared plan пуст, но есть хоть одна personal‑запись (`:1075`, `:1092`), — и управление доходит до чтения shared `trust.toml` (`:1146-1159`), чей отказ в конце превращает прогон в `status 1` (`:1476-1478`). До этого change при пустом shared plan trust‑файл вообще не читался. Итог: в клоне с нечитаемым или сломанным `.git/agentmarshal/trust.toml` (например `format = 2` от более новой версии, root‑овый файл, каталог на этом пути), где ни одно shared extension не объявляет stage этой фазы, personal stage отработает и напечатает `mycheck: checked (personal)`, а `stage run` всё равно выйдет с 1, а `complete` откажется писать `completed` («complete: pre-gate stage run refused; task not completed») — хотя personal scope grant не требует вовсе (критерий 2: «with no local grant required»). Достаточно `if not ci and plan:` вокруг чтения grants.

**personal-schema-1-refusal-misleads** (advisory): в `src/agentmarshal/extension_trust.py:326-333` проверка `manifest.schema != 2` недостижима — для `schema = 1` парсер падает раньше, на `journal/extensions.py:406`, где `artifacts` обязателен, а этот же reader `artifacts` в personal‑манифесте запрещает (`:320-325`). Автор personal extension со `schema = 1` получит строку `mycheck: not run (extension manifest field 'artifacts' must be an array of strings: …) (personal)`, то есть требование добавить поле, которое тут же запрещено, вместо обещанного docstring'ом «the directory form requires a manifest of schema 2».

**personal-command-python-only** (advisory): `src/agentmarshal/stages.py:728` строит argv как `[sys.executable, str(command)]` для обоих scope, поэтому personal `bin/check.sh` или `bin/check.js` исполняется интерпретатором Python и падает как `failed (exit 1) (personal)`. Это противоречит ADR‑0013, решение 13 (поправка 2026‑10‑03, строка 242: «A personal extension may be written in any language»); contract и delta spec при этом сами прибивают personal stage к неизменённому `_run_stage` («argv, snapshot, timeout, isolation»), так что расхождение именно с решением, а не с задачей.

**personal-switch-rewrite-drops-entries** (advisory): `src/agentmarshal/extension_trust.py:837-843` и `:876-889` перечитывают файл только по именам живых personal extensions (`switches.py:302-303` молча пропускает остальные) и затем пишут ровно этот dict через `_dump_personal_switches`, так что любой `disable`/`enable` стирает записи для имён, которых сейчас нет в каталоге, и ключи вне схемы (`note = …`). Если временно убрать каталог одного personal extension и выключить другой, состояние `off` первого пропадёт и он тихо включится при возврате каталога — хотя spec и design decision 9 обещают, что такие записи «pass unread».

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "5b748eef7d4830e196c5b9fc2c275b8819a1bf7f",
  "verdict": "changes_required",
  "findings": ["personal-run-fails-on-unreadable-trust"],
  "advisory_findings": [
    "personal-schema-1-refusal-misleads",
    "personal-command-python-only",
    "personal-switch-rewrite-drops-entries"
  ],
  "classes": {
    "personal-run-fails-on-unreadable-trust": "correctness",
    "personal-schema-1-refusal-misleads": "correctness",
    "personal-command-python-only": "contract-mismatch",
    "personal-switch-rewrite-drops-entries": "correctness"
  },
  "verification": {
    "executed": [
      {"what": "grep -c '^#### Scenario:' on the archived delta spec and grep -c 'Scenario:' on tests/test_personal_extensions.py", "result": "37 and 37; listing both showed the 37 titles matching one-to-one in order"},
      {"what": "tail -n 309 openspec/specs/extension-stages/spec.md | md5sum vs the same tail of the archived delta", "result": "96f1ace8ac52ad3931d29c5079347d7d both — the delta's requirements are appended verbatim"},
      {"what": "find on openspec/changes/archive/2026-10-25-personal-extensions and 2026-10-24-complete-runs-stages", "result": "identical layout (proposal.md, design.md, tasks.md, specs/extension-stages/spec.md); openspec/changes holds only archive/"},
      {"what": "grep -rn 'run_stages(|skip_ext' src tests", "result": "only stages.py:1505-1513 and cli.py:1122-1131, 1217-1226 pass skip; no caller left unpassed"},
      {"what": "grep -rn 'read_extension_manifest|record_kinds' src/agentmarshal/record_ext.py", "result": "record_ext.py:147 reads the working tree's shared manifest only — personal kinds cannot enter"},
      {"what": "grep -rn 'scope' src/agentmarshal/process_log.py", "result": "no output — the process log does not constrain the scope value, so scope=personal is writable"}
    ],
    "read": [
      "src/agentmarshal/stages.py (lines 380-900, 900-1523)",
      "src/agentmarshal/switches.py (whole file)",
      "src/agentmarshal/extension_trust.py (lines 80-440, 560-895)",
      "src/agentmarshal/doctor.py (lines 500-845)",
      "src/agentmarshal/cli.py (lines 1040-1235)",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/extensions.py (lines 60-360, 360-641)",
      "tests/test_personal_extensions.py (via the diff) and tests/test_stages.py helpers",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (lines 145-280)",
      "openspec/specs/extension-stages/spec.md (appended requirements)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff; mypy", "why": "neither uv nor pytest is installed in this read-only review sandbox and arbitrary interpreter runs were declined; the coordinator's note that the sequence passed on this commit is taken as given and no finding claims a tool failure"}
    ]
  },
  "evidence": {
    "personal-run-fails-on-unreadable-trust": "src/agentmarshal/stages.py:1075 'if not plan and not personal and quiet' and :1092 'if not plan and not personal' (the diff shows both were 'if not plan ...' before), :1146-1159 'if not ci: try: grants = _read_grants(state.trust_file) ... grants_unreadable = True', :1476-1478 'if grants_unreadable: return StageRunResult(1, tuple(paused))'; cli.py:1151-1156 turns that status into 'complete: pre-gate stage run refused; task not completed'",
    "personal-schema-1-refusal-misleads": "src/agentmarshal/extension_trust.py:320-325 rejects 'artifacts' outright, :326-333 then checks manifest.schema != 2; src/agentmarshal/journal/extensions.py:406 'if schema == 1 or \"artifacts\" in data: artifacts = _require_string_array(data, \"artifacts\", source)' with :119-127 raising \"must be an array of strings\" for a missing key, so schema 1 never reaches the schema-2 message",
    "personal-command-python-only": "src/agentmarshal/stages.py:728 'argv = [sys.executable, str(command)]' (one path for both scopes, reached from run_and_report at :1350); docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:242 'A personal extension may be written in any language.'",
    "personal-switch-rewrite-drops-entries": "src/agentmarshal/switches.py:302-303 'if name not in names: continue' and :330 keeping only state/reason; src/agentmarshal/extension_trust.py:837 'switches = read_personal_switches(state.switches_file, names)', :843 '_write_personal_switches(state, switches)', :728-744 _dump_personal_switches writing exactly that dict; :876 does the same with 'names | {args.name}'"
  }
}
AGENTMARSHAL_VERDICT_END
