Я прочитал diff и исходники на коммите `5b748eef7d4830e196c5b9fc2c275b8819a1bf7f`; выполнить команды (pytest/ruff/mypy) в этой песочнице не удалось — запуск был заблокирован, так что все выводы ниже сделаны чтением кода, и ни одно из них не утверждает, что какой-либо инструмент CI падает.

## Находки

**PE-SWITCHES-REWRITE-DROPS-ENTRIES** (blocking) — `extension disable` и `extension enable` перезаписывают `.git/agentmarshal/switches.toml` целиком из словаря, который вернул `read_personal_switches`, а этот парсер по построению отбрасывает записи с именами вне переданного набора (`src/agentmarshal/switches.py:302-303`, `if name not in names: continue`) и не сохраняет ключи сверх `state`/`reason`. `_run_disable` читает файл с `names` = только живые personal extensions (`src/agentmarshal/extension_trust.py:837`) и тут же пишет его обратно (`:843`), то же делает `_run_enable` (`:876`, `:889`), а `_dump_personal_switches` (`:728-743`) печатает только `state` и `reason`. Итог: любая запись о расширении, которого сейчас нет в каталоге, молча исчезает при следующем `disable`/`enable` чего-то другого — то есть выключенное расширение, временно убранное из каталога, после возврата снова включится само. Это прямо противоречит заявленной в design.md решение 9 снисходительности («a stale switch passes unread») и комментарию в самом `_run_enable` о том, что запись может пережить своё расширение.

**PE-EXT-LEVEL-LINE-IGNORES-PHASE** (advisory) — в `_personal_entries` (`src/agentmarshal/stages.py:602-628`) проверки collision / `disabled` / `--skip-ext` стоят до чтения манифеста, а фильтр `stage.phase in modes` применяется только к последней ветке. Поэтому выключенное или пропущенное personal-расширение, объявляющее лишь `pre-gate-stop`, печатает свою строку и на `post-gate` — в том числе во втором, тихом вызове `run_stages` из `complete` уже после записи `completed`. Побочно это делает `personal` непустым и гасит `plan_empty`, так что `stage run --phase post-gate` теряет строку `no shared extension declares a post-gate stage`. Сценарий дельты «a personal extension declaring no matching stage prints nothing» для этого случая не выполняется; тест `test_a_disabled_personal_extension_prints_disabled_personal_and_does_not_run` гоняет только `pre-gate` и этого не ловит.

**PE-ADR-MISCITATION** (advisory) — docstring'и ссылаются не на то решение ADR-0013. `src/agentmarshal/switches.py:20` и `src/agentmarshal/extension_trust.py:26` называют personal switch «decision 11», но решение 11 в `docs/adr/ADR-0013-...md:192` — это «Local state lives outside the working tree»; `--skip-ext` / `extension disable` / `.git/agentmarshal/switches.toml` описаны решением 16 (`:269-275`), как и сам контракт говорит «personal switches (decision 16)». Там же `src/agentmarshal/stages.py:524` приписывает отсутствие grant'а решению 10 («no footprint»), хотя правило живёт в решении 14 («a **shared** extension … only under a valid grant», `:243-246`) и в 15(a).

**PE-DOCTOR-PERSONAL-GATED-BY-SHARED** (advisory) — персональный блок `doctor` стоит после раннего `return` по общей директории: `src/agentmarshal/doctor.py:707-715` выходит из `_report_extensions`, а `:538-547` возвращает единственный проваленный check из `_extension_checks`, если `_managed_directory` отказал (symlink на `.agentmarshal` или `.agentmarshal/extensions`). В этом случае клон не получает ни строк `extension <name>: personal scope, …`, ни `personal extensions: unavailable (…)`, хотя требование дельты обещает строку на каждое personal-расширение.

**PE-STATUS-NOT-EXERCISED** (advisory) — сценарий «a clone with no personal extension prints exactly what it prints today» называет `stage run`, `complete`, `doctor` **и `status`**, но тест `tests/test_personal_extensions.py:1005` прогоняет только первые три; `status` не вызывается ни разу во всём файле.

## Критерии приёмки

1. **Change + delta + архив** — выполнен: `openspec/changes/archive/2026-10-25-personal-extensions/` содержит `proposal.md`, `design.md`, `tasks.md` и `specs/extension-stages/spec.md`, дата-префикс каталога соответствует работе `openspec archive`, а `openspec/specs/extension-stages/spec.md` получил те же ADDED-требования. Все 37 сценариев дельты имеют по тесту, docstring которого дословно их называет (сверил поимённо, например `test_a_personal_extensions_stage_runs_on_a_workstation_without_a_grant` ↔ «a personal extension's stage runs on a workstation without a grant»).
2. **Запуск personal-стадий в клоне** — выполнен: `run_stages` планирует их только вне CI (`src/agentmarshal/stages.py:1061-1064`), читает манифест из `state.extensions` (`:617`), гоняет через тот же `_run_stage` (`:1341-1362`), без grant'а (`_prepare_personal_extension`, `:512-544`). Демонстрируют `test_a_personal_extensions_stage_runs_on_a_workstation_without_a_grant`, `test_the_clones_directory_is_what_runs_never_the_base`, `test_no_personal_stage_is_planned_or_printed_in_ci`, `test_complete_runs_the_personal_stages_through_the_shared_runner`, `test_a_pausing_personal_pre_gate_stop_stage_pauses_the_local_run_marked_personal`, `test_a_personal_extension_named_like_a_shared_one_is_not_run_and_is_named_on_one_line`.
3. **Запрет `footprint`/`documents`/`artifacts`, никакой власти над журналом, scope в `doctor`** — выполнен: проверка на сырой таблице до парсера (`src/agentmarshal/extension_trust.py:294-300`); демонстрируют `test_a_personal_manifest_declaring_footprint_documents_or_artifacts_is_refused_and_does_not_run`, `test_doctor_fails_the_check_of_a_personal_manifest_carrying_a_forbidden_field`, `test_record_ext_refuses_a_kind_only_a_personal_manifest_declares`, `test_doctor_lists_a_personal_extension_with_the_scope_personal`.
4. **Personal switches** — выполнен по поведению команд (`test_stage_run_skip_ext_skips_a_personal_extension_for_that_run`, `test_complete_skip_ext_skips_a_personal_extension_for_that_run`, `test_extension_disable_writes_the_off_switch_to_the_clones_switches_toml`, `test_a_disabled_personal_extension_prints_disabled_personal_and_does_not_run`, `test_extension_enable_removes_the_switch_and_the_extension_runs_again`, и три теста отказа на shared-имя), но с дефектом записи файла — см. PE-SWITCHES-REWRITE-DROPS-ENTRIES.
5. **Клон без personal-расширений печатает ровно то же** — выполнен для `stage run`, `complete` и `doctor` (`test_a_clone_with_no_personal_extension_prints_exactly_what_it_prints_today`, `test_the_personal_scope_adds_no_mark_to_a_shared_stages_line`); gate не тронут, `.agentmarshal/extensions` ни один существующий тест в локальном состоянии не создаёт, так что прежние транскрипты не смещаются. `status` остался непродемонстрированным — PE-STATUS-NOT-EXERCISED.

Диффа за пределами scope контракта нет: тронуты только `stages.py`, `switches.py`, `extension_trust.py`, `doctor.py`, `cli.py`, `tests/` и `openspec/{changes/archive,specs/extension-stages}/`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "5b748eef7d4830e196c5b9fc2c275b8819a1bf7f",
  "verdict": "changes_required",
  "findings": ["PE-SWITCHES-REWRITE-DROPS-ENTRIES"],
  "advisory_findings": [
    "PE-EXT-LEVEL-LINE-IGNORES-PHASE",
    "PE-ADR-MISCITATION",
    "PE-DOCTOR-PERSONAL-GATED-BY-SHARED",
    "PE-STATUS-NOT-EXERCISED"
  ],
  "classes": {
    "PE-SWITCHES-REWRITE-DROPS-ENTRIES": "correctness",
    "PE-EXT-LEVEL-LINE-IGNORES-PHASE": "contract-mismatch",
    "PE-ADR-MISCITATION": "claim-accuracy",
    "PE-DOCTOR-PERSONAL-GATED-BY-SHARED": "contract-mismatch",
    "PE-STATUS-NOT-EXERCISED": "test-gap"
  },
  "verification": {
    "read": [
      "src/agentmarshal/stages.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/cli.py (complete lane, parser)",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/extensions.py (parse_extension_manifest_text, directory-form helpers)",
      "tests/test_personal_extensions.py",
      "openspec/changes/archive/2026-10-25-personal-extensions/{proposal,design,tasks}.md",
      "openspec/changes/archive/2026-10-25-personal-extensions/specs/extension-stages/spec.md",
      "openspec/specs/extension-stages/spec.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/threat-model.md"
    ],
    "executed": [
      {"what": "grep for other users of the clone's local-state extensions directory across src/ and tests/", "result": "no existing test or module creates .git/agentmarshal/extensions, so prior transcripts are unaffected"},
      {"what": "grep -n for '_build_parser' in src/agentmarshal/cli.py", "result": "parser is built fresh inside main(), so action=append with default=[] cannot leak across invocations"},
      {"what": "manual one-to-one comparison of the 37 '#### Scenario:' headings in the delta spec against the 37 'Scenario: ...' docstrings in tests/test_personal_extensions.py", "result": "every scenario has exactly one matching test docstring; no extras"}
    ],
    "not_run": [
      {"what": "uv run pytest tests/test_personal_extensions.py", "why": "the sandbox refused the command (approval required); no test execution was possible"},
      {"what": "uv run ruff check / ruff format --check / mypy", "why": "same approval refusal; the coordinator's note that the full CI sequence passed at this commit is taken as given and no tool-failure claim is made"}
    ]
  },
  "evidence": {
    "PE-SWITCHES-REWRITE-DROPS-ENTRIES": "src/agentmarshal/switches.py:302-303 ('if name not in names: continue') filters stale entries out of the parse result; src/agentmarshal/extension_trust.py:837 and :876 read with that filter, :843 and :889 write the filtered dict back through _write_personal_switches, and _dump_personal_switches (:728-743) emits only 'state' and 'reason'. Failure scenario: disable alpha and beta, move .git/agentmarshal/extensions/beta aside, run 'extension enable alpha' -> the rewritten file holds an empty [switches] table and beta's off switch is gone, so restoring beta silently runs it again.",
    "PE-EXT-LEVEL-LINE-IGNORES-PHASE": "src/agentmarshal/stages.py:602-615 appends the collision/disabled/skipped/refused line before any phase check, while the 'stage.phase in modes' filter appears only at :626-628; run_stages:1063-1064 then makes 'personal' non-empty, which defeats the plan_empty returns at :1075 and :1092. Failure scenario: a personal extension declaring only pre-gate-stop, switched off with 'extension disable', makes 'complete' print 'mycheck: disabled (personal)' a second time after the completed record and makes 'stage run --phase post-gate' drop its 'no shared extension declares a post-gate stage' line.",
    "PE-ADR-MISCITATION": "src/agentmarshal/switches.py:20 and src/agentmarshal/extension_trust.py:26 cite 'decision 11'; docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:192 is 'Local state lives outside the working tree', while the personal switch (--skip-ext, extension disable, .git/agentmarshal/switches.toml) is :269-275, decision 16 — the number the contract itself uses. src/agentmarshal/stages.py:524 attributes 'needs no grant' to decision 10 (:177, footprint) rather than decision 14 (:243-246) and 15(a) (:255-259).",
    "PE-DOCTOR-PERSONAL-GATED-BY-SHARED": "src/agentmarshal/doctor.py:707-715 returns from _report_extensions and :538-547 returns from _extension_checks when _managed_directory (src/agentmarshal/extension_trust.py:205-220) refuses a symlink at .agentmarshal or .agentmarshal/extensions, both before the personal blocks at :572-598 and :782-844. Failure scenario: a clone whose .agentmarshal/extensions is a symlink gets neither the 'extension <name>: personal scope, ...' lines nor a 'personal extensions: unavailable (...)' line, although personal extensions are present and readable.",
    "PE-STATUS-NOT-EXERCISED": "tests/test_personal_extensions.py:1005 is the byte-identity test; it invokes _stage_run, _complete and doctor only, and 'status' appears nowhere in the file, while the scenario it names (openspec/specs/extension-stages/spec.md, 'a clone with no personal extension prints exactly what it prints today') lists 'stage run, complete, doctor and status'."
  }
}
AGENTMARSHAL_VERDICT_END
