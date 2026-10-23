Разобрался. Ниже — прозовые строки по каждому finding и соответствие критериям приёмки.

**Scope.** Диффом тронуты только `src/agentmarshal/stages.py`, `src/agentmarshal/cli.py` (три строки: импорт `src/agentmarshal/cli.py:22`, `stages.register` на `:481`, диспетч на `:1608`), `tests/test_stages.py`, `openspec/changes/archive/2026-10-24-extension-stage-run/**` и `openspec/specs/extension-stages/spec.md` — всё внутри объявленного scope; `journal/gate.py` не изменён.

**stage-command-symlink-component (blocking).** В `src/agentmarshal/stages.py:387-391` запуск проверяет только последний компонент пути команды (`command.is_symlink()`), а `command.is_file()` проходит по симлинкам в промежуточных компонентах: если базовое дерево содержит запись-симлинк `bin/sub` (она материализуется как настоящая ссылка в `src/agentmarshal/stages.py:265-266`), а манифест объявляет `command = "bin/sub/x.py"`, то в CI — где проверка гранта пропущена (`src/agentmarshal/stages.py:298-299`) — выполняется файл, лежащий вообще вне материализованного base-каталога; собственное правило проекта для тех же путей (`src/agentmarshal/journal/extensions.py:525-561`, применяется из `:632` при чтении манифеста из рабочего дерева) обходит все компоненты от пути до каталога extension'а и отказывает на ссылке в любом из них и на нерегулярном файле, и `docs/threat-model.md:156-162` формулирует это как инвариант («reached through no `..` component and through no symlink»), так что исполнитель здесь мягче валидатора; побочно тот же участок рапортует каталог по пути команды как `does not exist`. На рабочей станции дыру закрывает хеш гранта (`_hash_directory` отказывает на любой ссылке внутри каталога), поэтому расхождение поведения CI/станция для одного и того же базового дерева — часть той же проблемы; эксплуатация требует права коммита в базу, то есть это не эскалация привилегий, а нарушение заявленного «what runs is what was approved» и несогласованность с существующим правилом — починка: применить к `prepared.directory` и `stage.command` ту же покомпонентную проверку.

**stage-minimal-path-defpath (advisory, unconfirmed).** В `src/agentmarshal/stages.py:340` минимальный `PATH` задан как `os.defpath`: исторически `posixpath.defpath` — это `':/bin:/usr/bin'` с ведущим двоеточием, а пустой элемент `PATH` для `execvp` означает текущий каталог, то есть снапшот кандидата (рабочий каталог стадии), и тогда кандидат может положить в корень репозитория исполняемый `git`/`node`/`uv` и перехватить любой вызов внешней утилиты по имени из доверенного base-кода стадии — это прямо против ADR-0013 решения 6 и смысла запрета `PATH`-поиска в решении 13; значение константы я в этой песочнице проверить не смог (запуск `python3 -c` и чтение stdlib вне рабочего каталога запрещены), поэтому помечаю **unconfirmed** — проверяется одной командой `python3 -c "import os; print(repr(os.defpath))"`, и если двоеточие на месте, то лечится литералом `"/bin:/usr/bin"`, а тест `tests/test_stages.py:626` (`assert env["PATH"] == os.defpath`) эту ошибку не поймает, потому что сравнивает с той же константой.

**stage-timeout-unbounded-wait (advisory).** В `src/agentmarshal/stages.py:422-425` после `TimeoutExpired` группа процессов убивается, но следующий `process.communicate()` вызван без `timeout`: потомок, ушедший из группы (`setsid`/`start_new_session`) и унаследовавший pipe stdout, держит его открытым, и `stage run` висит до закрытия pipe вместо обещанного спецификацией (`openspec/specs/extension-stages/spec.md:218-232`) предела и строки `did not finish (timeout)` — для pre-gate-шага в CI это зависание всего конвейера; раздел Risks в design.md упоминает беглого потомка, но не этот эффект, а лечится ограниченным вторым ожиданием с отказом от хвоста вывода.

**spec-per-stage-materialization-unspecified (advisory).** Свежая материализация и свежий снапшот на каждую стадию — несущее решение (`src/agentmarshal/stages.py:555-578`, design.md «Decisions» и Risks), но спецификация требует лишь «a fresh temporary directory» и удаление временных каталогов к возврату команды, отдельного требования/сценария на «ни одна стадия не переиспользует копию предыдущей» в `openspec/specs/extension-stages/spec.md` нет, а единственный тест на это свойство — `tests/test_stages.py:516-556` — подписан docstring'ом «Scenario: the base commit's code runs, not the candidate's or the working tree's», дублирующим docstring на `tests/test_stages.py:378` и называющим не тот сценарий, который тест демонстрирует; итог — очевидная оптимизация (вынести материализацию из цикла) пройдёт спеку и список сценариев, сломав свойство, и упадёт только на неверно подписанном тесте.

**changed-after-approval-spelling (advisory).** Спецификация в обоих экземплярах (`openspec/specs/extension-stages/spec.md:240-249` и дельта в архиве) фиксирует строку результата как `not run (changed after approval: <file>)`, а код в `src/agentmarshal/stages.py:310-312` печатает `not run (changed after approval: <file> (<kind>))` — суффикс вида изменения записан только в design.md, так что нормативный текст и реализация расходятся по буквальному написанию (тест `tests/test_stages.py:883-907` проверяет лишь подстроки и расхождение не ловит).

**Критерии приёмки.** AC1 выполнен: `proposal.md`, `design.md`, `tasks.md` и дельта `specs/extension-stages/spec.md` лежат в `openspec/changes/archive/2026-10-24-extension-stage-run/`, `openspec/changes/` содержит только `archive/`, опубликованная capability — `openspec/specs/extension-stages/spec.md` (355 строк дельты против 354 опубликованных — ровно нормализация заголовков `ADDED Requirements`→`Requirements` и пустой строки после `## Purpose`, как у `openspec/specs/extension-trust/spec.md`); 42 заголовка `#### Scenario:` и 43 docstring'а `"""Scenario:` в `tests/test_stages.py` дают по тесту на каждый сценарий (единственный дубль — см. spec-per-stage-materialization-unspecified); Purpose называет решения 1, 2, 4, 5, 7 и 14 номерами, а решение 6 — по существу («from the base commit — never the candidate's tree and never the working tree»), что критерий «covering» покрывает. AC2 выполнен: выбор режимов по `--phase` — `test_pre_gate_invokes_the_pre_gate_warn_and_pre_gate_stop_stages` и `test_post_gate_invokes_the_post_gate_stages`, порядок — `test_stages_run_in_extension_name_order_and_manifest_order_within`, чтение и материализация из merge base, а не из кандидата или рабочего дерева — `test_the_base_commits_code_runs_not_the_candidates_or_the_working_trees`, argv под интерпретатором ядра без шелла — `test_the_command_runs_under_the_cores_interpreter_never_through_a_shell`, предел времени и его потолок — `test_a_stage_over_its_declared_timeout_is_killed_and_did_not_finish` и `test_the_cores_limit_caps_a_longer_declared_timeout` (с оговоркой stage-timeout-unbounded-wait). AC3 выполнен: протокол записан в design.md (блоки решений про рабочий каталог, окружение и argv) и в требовании «the command runs as an argv process under the core's interpreter»; демонстрируют `test_the_working_directory_is_a_snapshot_of_the_candidate_commit`, `test_the_environment_carries_the_protocol_variables_and_a_minimal_path` (с оговоркой stage-minimal-path-defpath), `test_only_the_environment_variables_the_manifest_names_are_passed`, `test_a_protocol_variable_cannot_be_overridden_by_a_declared_name`, `test_exit_status_zero_checks_and_any_other_fails`. AC4 выполнен: грант на станции и его отсутствие в CI — `test_no_grant_on_a_workstation_is_not_run`, `test_a_grant_matching_the_base_contents_runs_the_stage`, `test_a_grant_for_different_contents_is_not_run_naming_the_changed_file`, `test_in_ci_no_grant_is_needed`, `test_a_malformed_trust_toml_fails_the_command_naming_it`; ровно одна строка результата и рамка вывода — `test_every_stage_gets_exactly_one_result_line` и `test_the_extensions_output_is_framed_so_it_cannot_read_as_a_result_line`; события — `test_each_stages_result_appends_one_extension_event`, `test_a_post_gate_stages_event_carries_the_result_field`, `test_a_lost_process_log_is_a_warning_not_a_changed_verdict` (поля совпадают с ADR-0022 раздел 7, строки 229-231). AC5 выполнен: `test_a_failed_pre_gate_stop_stage_pauses_the_process_before_the_gate`, `test_a_pre_gate_stop_stage_that_did_not_run_pauses_the_process`, `test_a_failed_pre_gate_warn_stage_warns_and_the_exit_is_0`, `test_a_checked_pre_gate_stop_stage_does_not_pause`, `test_a_post_gate_stages_outcome_never_pauses`, `test_the_journal_is_untouched`; новых команд, кроме `stage`, не появилось, гейт не тронут, прохождение полной последовательности CI я беру из заметки координатора, сам её не запускал.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "5304bd4973106f74a7f4d2bd9ea7a34eaf392b09",
  "verdict": "changes_required",
  "findings": ["stage-command-symlink-component"],
  "advisory_findings": [
    "stage-minimal-path-defpath",
    "stage-timeout-unbounded-wait",
    "spec-per-stage-materialization-unspecified",
    "changed-after-approval-spelling"
  ],
  "classes": {
    "stage-command-symlink-component": "security",
    "stage-minimal-path-defpath": "security",
    "stage-timeout-unbounded-wait": "correctness",
    "spec-per-stage-materialization-unspecified": "test-gap",
    "changed-after-approval-spelling": "contract-mismatch"
  },
  "verification": {
    "read": [
      "src/agentmarshal/stages.py (whole file)",
      "src/agentmarshal/cli.py (lines 19-25, 475-485, 1600-1612 via grep)",
      "tests/test_stages.py (scenario docstrings; lines 505-565 in full)",
      "src/agentmarshal/journal/gate.py:279-335, 525-636, 1120-1200",
      "src/agentmarshal/journal/extensions.py:170-243, 515-641",
      "src/agentmarshal/extension_trust.py:112-139, 193-233, 258-295, 377-420, 560-579",
      "src/agentmarshal/journal/review.py:1151-1184 (_extract_snapshot)",
      "src/agentmarshal/process_log.py:1-140, 199-219",
      "src/agentmarshal/journal/placement.py:16-46",
      "src/agentmarshal/journal/contracts.py:112-134",
      "src/agentmarshal/steps.py:69-119 (register/run convention)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (sections A-D, decisions 1-15)",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md (section 7, extension-event)",
      "docs/threat-model.md:144-174",
      "openspec/specs/extension-stages/spec.md",
      "openspec/changes/archive/2026-10-24-extension-stage-run/{proposal.md,design.md,tasks.md,specs/extension-stages/spec.md}",
      "openspec/specs/extension-trust/spec.md (Purpose and first requirement)",
      "pyproject.toml (ruff/mypy/pytest configuration)"
    ],
    "executed": [
      {
        "what": "grep -c '^#### Scenario: ' openspec/specs/extension-stages/spec.md; grep -c '\"\"\"Scenario: ' tests/test_stages.py",
        "result": "42 scenario headings, 43 test docstrings; the extra one is tests/test_stages.py:519 duplicating tests/test_stages.py:378"
      },
      {
        "what": "grep -n 'stages' src/agentmarshal/cli.py",
        "result": "only three touched lines: 22 (import), 481 (stages.register), 1608 (stages.run dispatch)"
      },
      {
        "what": "grep -rn 'extension-event' src/",
        "result": "only src/agentmarshal/stages.py — this change is the first writer of the event kind"
      },
      {
        "what": "grep -rn 'defpath|\"PATH\"' src/ tests/",
        "result": "src/agentmarshal/stages.py:340 sets {\"PATH\": os.defpath}; tests/test_stages.py:626 asserts env[\"PATH\"] == os.defpath"
      },
      {
        "what": "grep -n '_require_existing_directory_file' src/agentmarshal/journal/extensions.py",
        "result": "defined at 525, applied at 632 for every stage command of a directory-form manifest read from the working tree — the per-component symlink rule stage run does not apply"
      },
      {
        "what": "grep -rn 'return 3' src/agentmarshal/",
        "result": "only src/agentmarshal/stages.py:600 — exit 3 collides with no existing command's status"
      },
      {
        "what": "ls openspec/changes/ and ls openspec/changes/archive/",
        "result": "changes/ holds only archive/; archive/ holds 2026-10-24-extension-stage-run — the change is archived"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "the snapshot is not a git repository and command execution is sandboxed here; the coordinator's note records the full CI sequence as passing on this commit, and no finding above claims otherwise"
      },
      {
        "what": "python3 -c \"import os; print(repr(os.defpath))\"",
        "why": "running python and reading the stdlib outside the working directory are both refused in this sandbox — hence stage-minimal-path-defpath is advisory and marked unconfirmed"
      },
      {
        "what": "a reproduction of the intermediate-symlink command and of the escaped-process timeout hang",
        "why": "no git and no interpreter available to build a fixture repository; both findings rest on the code paths and line numbers cited in the evidence"
      }
    ]
  },
  "evidence": {
    "stage-command-symlink-component": "src/agentmarshal/stages.py:387-391 checks only command.is_symlink() on the final component and then command.is_file(), which follows an intermediate link materialized by src/agentmarshal/stages.py:265-266; the grant check that would catch it is skipped in CI at src/agentmarshal/stages.py:298-299; the project's own rule for the same paths is src/agentmarshal/journal/extensions.py:525-561 applied at :632, and the stated invariant is docs/threat-model.md:156-162",
    "stage-minimal-path-defpath": "src/agentmarshal/stages.py:340 ({\"PATH\": os.defpath}) with cwd set to the candidate snapshot at src/agentmarshal/stages.py:404-405; the test that would pin the value compares against the same constant at tests/test_stages.py:626; unconfirmed — check with python3 -c \"import os; print(repr(os.defpath))\"",
    "stage-timeout-unbounded-wait": "src/agentmarshal/stages.py:420-425 — process.communicate() after _kill_process_group carries no timeout, against the bound required by openspec/specs/extension-stages/spec.md:218-232",
    "spec-per-stage-materialization-unspecified": "implementation src/agentmarshal/stages.py:555-578; no requirement or scenario for per-stage freshness in openspec/specs/extension-stages/spec.md:93-139; the only test is tests/test_stages.py:516-556, whose docstring at :519 duplicates the scenario named at tests/test_stages.py:378",
    "changed-after-approval-spelling": "code emits the kind suffix at src/agentmarshal/stages.py:310-312; the normative spelling without it is openspec/specs/extension-stages/spec.md:240-249 (and the archived delta), while design.md records the suffix"
  }
}
AGENTMARSHAL_VERDICT_END
