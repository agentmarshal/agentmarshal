Разобрал контракт, диф и окружающий код. Прогнать CI не смог — в снапшоте нет venv и запуск Python в этой сессии не разрешён, поэтому утверждение координатора о зелёном CI беру как факт и ничего про падение инструментов не заявляю. Всё остальное проверял чтением кода и грепом.

## Что по acceptance criteria

**AC1 (change + scenario↔test + архив) — выполнен.** Архивный change несёт `proposal.md`, `design.md`, `tasks.md` и delta-spec с четырьмя ADDED-требованиями; все 19 заголовков `#### Scenario:` из delta-спеки присутствуют дословно как docstring'и тестов в `tests/test_switch_off.py` (два из них продемонстрированы двумя тестами каждый — malformed-файл и необрамляемая запись), и `openspec/specs/extension-stages/spec.md` получил каждое требование по одному разу.

**AC2 (контракт задачи, запись switch, вывод путей, ничего не коммитит) — выполнен.** Форму контракта демонстрирует `test_the_opened_contract_names_the_extension_scopes_the_switches_file_and_accepts_the_switch_off` (проверяет `header.scope == (".agentmarshal/switches.toml",)`), запись записи — `test_the_switches_entry_is_written_for_the_opened_task`, создание отсутствующего файла — `test_a_missing_switches_file_is_created_with_format_and_the_switches_table`, сохранность остального текста — `test_an_existing_on_entrys_table_is_replaced_and_the_files_other_content_is_kept`, печать трёх путей и неподвижность HEAD — `test_the_paths_are_printed_and_nothing_is_committed`.

**AC3 — выполнен частично.** Parse-back демонстрирует `test_the_new_text_is_parsed_back_before_it_replaces_the_file`, правило reason — `test_a_reason_outside_its_rule_is_refused_before_anything_is_written`, уже выключенное расширение — `test_an_extension_already_switched_off_is_refused_naming_the_task_that_switched_it_off`, битый файл — `test_a_malformed_switches_file_is_refused_naming_it_and_nothing_is_written`, обе формы объявления — `test_a_file_form_extension_is_a_shared_extension_the_command_switches_off`. Именно на половине «name must be a shared extension the working tree declares» лежат оба блокирующих findings ниже.

**AC4 (атомарная замена, провал после открытия задачи, sidecar) — выполнен.** `test_the_file_is_replaced_by_a_temporary_file_renamed_in_the_same_directory`, `test_a_failure_after_the_task_is_opened_names_the_task_on_one_line_and_exits_non_zero`, `test_a_sidecar_refuses_saying_operational_tasks_are_not_available`. Advisory ниже — частный дефект этой же атомарной замены.

**AC5 (escaping, неизменность trust/untrust/list, gate и stage run) — выполнен в проверяемой части.** `test_a_value_that_could_forge_a_line_is_escaped_on_display` и `test_every_path_the_command_prints_is_escaped_on_display`; `test_the_extension_group_takes_switch_off_with_a_name_and_a_reason` закрывает регистрацию. Диф в `extension_trust.py` трогает только `register` и ветку диспетча в `run`, файлы gate и `stages.py` не изменены вовсе.

## Findings

**SWITCHOFF-BROKEN-EXTENSION-UNSWITCHABLE** — `src/agentmarshal/switch_off.py:620-635`: расширение, манифест которого reader отвергает (битый TOML, объявленный в `bin/` файл удалён — `_require_existing_directory_file` в `journal/extensions.py:631`, манифест в обеих формах), выключить этой командой нельзя вообще: `read_extension_manifest` бросает `ExtensionManifestError`, и `_run_off` печатает сообщение reader'а и выходит с 1. Это ровно тот случай, который ADR-0013 решение 17 называет недопустимым своими словами — `docs/adr/ADR-0013-...md:282`: «extensions' `pre-gate` stages do not run on it — otherwise **a broken extension blocks its own switching off**». Сломанное расширение при этом валит `stage run` целиком (`stages.py:606-609` пробрасывает `ExtensionManifestError` в отказ команды), и единственный санкционированный путь его отключить закрыт. Подтверждает это и названный документ: `openspec/specs/extension-stages/spec.md:497` требует, чтобы `doctor` показывал `switched off since <task> (<reason>)` «and on the line of an extension whose manifest cannot be read» — состояние, которое новая команда создать не может.

**SWITCHOFF-NAMESET-DIVERGES-FROM-READERS** — `src/agentmarshal/switch_off.py:147-177`: `_shared_extension_names` прогоняет каждого кандидата из `.agentmarshal/extensions/` через `read_extension_manifest` и выбрасывает тех, кого reader не принял, а полученный суженный набор уходит в `parse_switches` на строке 649. Оба существующих читателя того же файла набор имён так не сужают: `doctor._extension_names` (`src/agentmarshal/doctor.py:488-511`) оставляет symlink-запись «под именем, которое она несёт, чтобы отказ reader'а мог о ней сообщить», а `stages._base_extensions` (`src/agentmarshal/stages.py:215-260`) прямо комментирует, что «a switches entry may still name it». Следствие: файл, который `doctor` и `stage run` читают без замечаний, `extension switch off` объявляет malformed — и отказ срабатывает до любой другой проверки, то есть блокирует выключение совершенно здорового расширения. Сценарий: в дереве есть `.agentmarshal/extensions/ghost.toml` как symlink (или с битым манифестом), в `switches.toml` для `ghost` стоит запись — тогда `extension switch off openspec --reason "…"` падает с `…switches.toml: malformed: switch 'ghost' names no shared extension`, хотя файл валиден по общему правилу проекта. Это ровно то, что фиксирует собственный тест дифа `test_a_switch_naming_a_symlinked_extension_is_refused_naming_the_file`. Хуже всего устойчивый случай: если уже выключенное сломанное расширение записано в файл (а `doctor` обязан его показывать), файл становится навсегда недоступным для этой команды. Лечится переиспользованием `doctor._extension_names` вместо дублирующего перечисления в `_shared_extension_names`.

**SWITCHOFF-REPLACE-DROPS-FILE-MODE** (advisory) — `src/agentmarshal/switch_off.py:552-559`: `tempfile.mkstemp` создаёт staging-файл с режимом `0600`, а `os.replace` переносит режим источника на цель, так что отслеживаемый в git `.agentmarshal/switches.toml`, лежавший с `0644`, после перезаписи молча становится `0600`. Для `trust.toml` (`extension_trust.py:387-394`) этот же приём уместен — это local state; здесь же речь о файле рабочего дерева, который читает `doctor` и который операторы держат в репозитории. Содержимое не страдает, поэтому finding не блокирующий, но стоит скопировать прежний режим или выставить его по umask перед `os.replace`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "bd7a3f6ea7ff81a3f5bd1427dd7916c42e8cf302",
  "verdict": "changes_required",
  "findings": [
    "SWITCHOFF-BROKEN-EXTENSION-UNSWITCHABLE",
    "SWITCHOFF-NAMESET-DIVERGES-FROM-READERS"
  ],
  "advisory_findings": [
    "SWITCHOFF-REPLACE-DROPS-FILE-MODE"
  ],
  "classes": {
    "SWITCHOFF-BROKEN-EXTENSION-UNSWITCHABLE": "contract-mismatch",
    "SWITCHOFF-NAMESET-DIVERGES-FROM-READERS": "correctness",
    "SWITCHOFF-REPLACE-DROPS-FILE-MODE": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "grep -c '^#### Scenario: ' openspec/changes/archive/2026-10-24-extension-switch-off/specs/extension-stages/spec.md",
        "result": "19 scenarios; grep -o 'Scenario: .*' tests/test_switch_off.py printed 21 docstring lines covering all 19 unique headings (two scenarios demonstrated twice)"
      },
      {
        "what": "grep -rn 'read_switches|shared_extension_names|extension_names' src/agentmarshal/ (excluding switch_off)",
        "result": "only doctor._extension_names (doctor.py:488) and stages._base_extensions (stages.py:215) enumerate shared extension names; neither filters candidates through read_extension_manifest"
      },
      {
        "what": "grep -n 'blocks its own switching off' docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
        "result": "line 282 — 'otherwise a broken extension blocks its own switching off'"
      },
      {
        "what": "grep -n 'manifest cannot be read' openspec/specs/extension-stages/spec.md",
        "result": "line 497 — doctor shows the switched-off line on the line of an extension whose manifest cannot be read"
      },
      {
        "what": "grep -rn 'os.replace|mkstemp|chmod' src/agentmarshal/",
        "result": "switch_off.py:552/559 mkstemp + os.replace with no chmod; no mode-preserving helper exists in the package"
      },
      {
        "what": "grep -n 'def write_record' -A 40 src/agentmarshal/journal/records.py",
        "result": "write_record uses _create_exclusive, not os.replace — so the two tests that monkeypatch os.replace do not disturb open_task"
      }
    ],
    "read": [
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/journal/open_task.py",
      "src/agentmarshal/journal/display.py",
      "src/agentmarshal/journal/extensions.py (_validate_name, _manifest_candidate, read_extension_manifest)",
      "src/agentmarshal/journal/contracts.py (parse_contract_text, reject_control_characters, validate_scope_entry)",
      "src/agentmarshal/journal/records.py (forges_rendered_text, write_record)",
      "src/agentmarshal/journal/placement.py (Placement, resolve_placement)",
      "src/agentmarshal/doctor.py (_extension_names, the switches section)",
      "src/agentmarshal/stages.py (_base_extensions, _base_switches)",
      "src/agentmarshal/cli.py (_run_open)",
      "tests/test_switch_off.py",
      "tests/test_stages.py (helpers), tests/test_placement.py (_host_and_sidecar)",
      "openspec/specs/extension-stages/spec.md",
      "openspec/changes/archive/2026-10-24-extension-switch-off/ (proposal.md, design.md, tasks.md, delta spec)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md section E",
      "docs/adr/ADR-0014-where-things-live.md (switches.toml placement)",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md sections 7 and 8",
      "AGENTS.md, pyproject.toml"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "the snapshot has no virtualenv and no installed pytest/ruff/mypy, and executing Python in this session was not permitted; the coordinator's statement that the full CI sequence passed on this commit is taken as given and no tool-failure claim is made"
      },
      {
        "what": "dynamic probing of _entry_span/_key_pair/_switches_text against hand-built switches.toml variants",
        "why": "script execution was refused; the rewrite logic was traced by hand instead, and the two blocking findings do not depend on it"
      }
    ]
  },
  "evidence": {
    "SWITCHOFF-BROKEN-EXTENSION-UNSWITCHABLE": "src/agentmarshal/switch_off.py:620-635 refuses on any ExtensionManifestError from read_extension_manifest; src/agentmarshal/journal/extensions.py:623-634 makes a directory-form manifest whose declared bin/ path is missing, or a manifest in both forms, exactly such an error; src/agentmarshal/stages.py:606-609 shows the same error aborts `stage run`; docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:282 'otherwise a broken extension blocks its own switching off'; openspec/specs/extension-stages/spec.md:497 requires doctor to show the switched-off line for an extension whose manifest cannot be read",
    "SWITCHOFF-NAMESET-DIVERGES-FROM-READERS": "src/agentmarshal/switch_off.py:147-177 filters candidates through read_extension_manifest and src/agentmarshal/switch_off.py:649 feeds that narrowed set to parse_switches, which refuses an entry naming anything outside it (src/agentmarshal/switches.py:120-123); src/agentmarshal/doctor.py:488-511 and src/agentmarshal/stages.py:215-260 keep such names, the latter commenting 'though a switches entry may still name it'; the diff's own tests/test_switch_off.py::test_a_switch_naming_a_symlinked_extension_is_refused_naming_the_file asserts the refusal of a file that doctor reads without complaint",
    "SWITCHOFF-REPLACE-DROPS-FILE-MODE": "src/agentmarshal/switch_off.py:552-559 — tempfile.mkstemp (documented mode 0600) then os.replace over the git-tracked .agentmarshal/switches.toml, with no chmod anywhere in src/agentmarshal (grep -rn 'chmod' src/agentmarshal returns nothing)"
  }
}
AGENTMARSHAL_VERDICT_END
