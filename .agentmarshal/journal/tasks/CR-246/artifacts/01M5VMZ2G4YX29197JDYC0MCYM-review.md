Разобрался. Ниже — построчная проза по каждому критерию и по каждому finding.

## Что критерии закрывают

**AC1 (file-form манифест на базе).** `_base_extensions` заменён на `_base_manifests` (`src/agentmarshal/stages.py:335-348`), который читает манифест для *каждого* имени из `_extension_names_at_tree`, а не только для directory-form — то есть `<name>.toml` теперь проходит через тот же base-tree reader `_manifest_from_tree` (`src/agentmarshal/journal/gate.py:662`), и его refusal валит команду с именем extension и tree source. «File-form не планирует стадий» держится структурно: валидатор требует, чтобы `command` был путём под `bin/` (`journal/extensions.py:170-203`), а `_refuse_single_file_directory_paths` (там же, 524-545) отказывает file-form манифесту, назвавшему такой путь, — значит file-form либо не объявляет стадий, либо отказывается при чтении. Демонстрируют `tests/test_stages.py::test_a_broken_file_form_manifest_at_the_base_fails_the_run`, `::test_a_command_declaring_file_form_manifest_at_the_base_fails_the_run` (именно та пара «broken + command-declaring», которую требует контракт), сохранившийся `::test_a_file_form_extension_has_no_stage_to_run` и для `complete` — `tests/test_complete_stages.py::test_a_file_form_manifest_the_base_refuses_fails_the_completion`.

**AC2 (leak-scan маскирует путь).** `src/agentmarshal/cli.py:1789-1793` печатает `escape_for_display(safe_path(str(error), markers))` — тот же порядок, что во всех остальных call sites (`outbox.py:701`, `acknowledge.py:280`). `markers` в этой точке уже прочитаны из base tree. `TaskStatusError` — подкласс `ValueError` (`journal/status.py:65`), поэтому «invalid task directory: <path>» (там же, 212) реально попадает в этот except. Демонстрирует `tests/test_leak_scan_acknowledgements.py::test_a_marker_in_a_task_directory_name_is_masked_in_the_diagnostic`.

**AC3 (`--skip-ext` с shared-именем на операционной полосе).** Проверка поднята выше операционного early-return (`stages.py:1053-1077`) и решается только по именам из `_extension_names_at_tree`, манифесты не читаются. Регрессии на других путях нет: при symlink в `extensions/` старый код всё равно падал с тем же сообщением, потому что `operational_candidate` глотает `ExtensionManifestError` и закрывает полосу (`gate.py:1094-1099`). Демонстрируют `tests/test_gate_operational.py::test_a_shared_name_in_skip_ext_is_refused_on_the_operational_lane` и `::test_complete_skip_ext_naming_a_shared_extension_is_refused_on_the_lane` — оба со сломанным манифестом, и оба проверяют, что `invalid TOML` в выводе нет.

**AC4 (runtime lookup раскрыт).** `docs/threat-model.md:506-513` и `CHANGELOG.md:320-326` («What 0.6.0 leaves out»). Утверждения верны: в `stages.py` слова `runtime` нет вовсе, `_MINIMAL_PATH = "/usr/bin:/bin"` (`stages.py:180`), проверка живёт только в `doctor` (`doctor.py:575`), а ADR-0013 D13 действительно обещает lookup и в stage output (`docs/adr/ADR-0013-...:237-240`). Цитата спеки проверена: `openspec/specs/extension-stages/spec.md:164`.

**AC5 (git 2.31).** Назван в `README.md:117`, `docs/quickstart.md:19`, `docs/sidecar.md:83`; минимум совпадает с кодом (`doctor.py:72`, `project.py:400-410`). См. advisory SOL-docs-status-overstated ниже.

**AC6 и AC7 не выполнены** — ниже.

## Findings

**SOL-audit-record-missing (blocking).** `release/audit-0.6.0.toml` в диффе вообще не тронут: все 133 строки файла — это 22 `[[finding]]` вида `AUD-*`, ни одного `SOL-extensions-1/-2`, `SOL-commands-2`, `SOL-docs-claims-1-1/-1-3`, никакого `task = "CR-246"` и никакого комментария про gpt-6.1-sol measurement audit. Это не только пропущенный пункт контракта: `.github/scripts/check_release_audit.py:328-355` разрешает только `ALWAYS_ALLOWED` плюс scope задач, перечисленных как fix. `docs/` покрывает CR-244, `README.md` — CR-243, `tests/` — CR-237, `src/agentmarshal/cli.py` — CR-242, а `src/agentmarshal/stages.py` не покрыт ни одной из перечисленных задач (CR-234..CR-244) — значит гейт откажет строкой «src/agentmarshal/stages.py changed between the audited commit … and tag v0.6.0 and is covered neither by the release paths nor by the scope of a task listed as fixing a finding», и `release audit: passed` напечатать нельзя.

**SOL-changelog-cr246-missing (blocking).** Параграф audit-fixes в `CHANGELOG.md:227` по-прежнему озаглавлен «Fixes from the release audit (CR-234, CR-235, CR-236, CR-237, CR-238, CR-239, CR-240, CR-241, CR-242, CR-243, CR-244)» — CR-246 не назван нигде в файле.

**SOL-upgrading-outbox-missing (blocking).** В секции `0.5.0 → 0.6.0` (`UPGRADING.md:3-62`) про outbox есть только пункт «skip files already sent» (строки 50-54). Обещанного пункта — что `outbox check` и `outbox send` отказывают файлу, чьи байты git застейджил бы иначе (`core.autocrlf`, атрибут `text`/`eol`, clean filter), и средства (`.agentmarshal/upstream/** -text`, никакого filter на outbox) — нет; ни `autocrlf`, ни `-text`, ни `gitattributes` в файле не встречаются. Поведение при этом реально реализовано (`outbox.py:690-708`, `750-768`, `_transform_cause` на 879-891), так что отсутствует именно документация.

**SOL-readme-refused-output (blocking).** `README.md:53-54` всё ещё говорит «a verdict that is refused keeps the reviewer's raw output at any level» — та самая неточность из advisory CR-245. Сырой вывод сохраняется не у «отклонённого verdict», а при launcher-отказе от malformed вывода: `_reject` → `_preserve_output` (`journal/review.py:598-616`, `813-825`); у записанного verdict'а с решением `rejected` прозу определяет capture level. Формулировку надо было сделать именно про launcher refusal.

**SOL-docs-status-overstated (advisory).** `README.md:117-120` утверждает, что разрешение local state «`complete`, `status` and the stage runner all need», а `docs/quickstart.md:19-22` и `docs/sidecar.md:83-86` — «commands such as `complete` and `status` need it». Для `status` это завышение: `cli.py:1469-1478` ловит `LocalStateError` и деградирует до «unavailable», с явным комментарием «rather than failing a command that needed no git before»; на git 2.30 `status` печатает результат, а не падает. Сам контракт в скобках называет только `complete`.

**SOL-spec-lane-carve-out (advisory).** `openspec/specs/extension-stages/spec.md:44-52` для операционного pre-gate по-прежнему требует «SHALL print one line … returning success», а теперь `stage run --skip-ext <shared>` на этой полосе возвращает 1 без этой строки. `openspec/` вне scope контракта, так что править спеку здесь нельзя — но по AGENTS.md это надо было назвать в отчёте как departure (нужна оговорка в требовании или follow-up change).

Проверочную последовательность CI я не запускал: снапшот не git-репозиторий и исполнение команд в этой сессии ограничено чтением, так что заявлений о падении инструментов не делаю.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "c9ac48782a8a6a2db5692de04a8e783f64d6805f",
  "verdict": "changes_required",
  "findings": [
    "SOL-audit-record-missing",
    "SOL-upgrading-outbox-missing",
    "SOL-readme-refused-output",
    "SOL-changelog-cr246-missing"
  ],
  "advisory_findings": [
    "SOL-docs-status-overstated",
    "SOL-spec-lane-carve-out"
  ],
  "classes": {
    "SOL-audit-record-missing": "contract-mismatch",
    "SOL-changelog-cr246-missing": "contract-mismatch",
    "SOL-upgrading-outbox-missing": "contract-mismatch",
    "SOL-readme-refused-output": "claim-accuracy",
    "SOL-docs-status-overstated": "claim-accuracy",
    "SOL-spec-lane-carve-out": "scope"
  },
  "verification": {
    "read": [
      "src/agentmarshal/stages.py (300-360, 1000-1300)",
      "src/agentmarshal/cli.py (1110-1130, 1462-1560, 1652-1800)",
      "src/agentmarshal/journal/gate.py (600-720, 940-1140)",
      "src/agentmarshal/journal/extensions.py (170-230, 505-560)",
      "src/agentmarshal/journal/capture.py (312-331)",
      "src/agentmarshal/journal/review.py (590-640, 805-840)",
      "src/agentmarshal/journal/status.py (65, 212)",
      "src/agentmarshal/localstate.py (104-120)",
      "src/agentmarshal/doctor.py (60-160, 520-580)",
      "src/agentmarshal/project.py (390-425)",
      "src/agentmarshal/outbox.py (525-560, 690-770, 879-915)",
      "docs/threat-model.md (485-525)",
      "docs/quickstart.md, docs/sidecar.md (requirements lines)",
      "README.md (40-60, 110-125)",
      "CHANGELOG.md (215-345)",
      "UPGRADING.md (1-62)",
      "release/audit-0.6.0.toml (whole file, 133 lines)",
      ".github/scripts/check_release_audit.py (1-80, 230-375)",
      "openspec/specs/extension-stages/spec.md (30-100, 1700-1740)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (230-260, 405-425)",
      ".agentmarshal/journal/tasks/CR-23*/contract.md and CR-24*/contract.md (scope lists)",
      "tests/test_stages.py, tests/test_complete_stages.py, tests/test_gate_operational.py, tests/test_leak_scan_acknowledgements.py, tests/test_personal_extensions.py (new tests and helpers)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; command execution beyond file reads is not permitted in this session, and the coordinator states the sequence passed at this commit"},
      {"what": "python3 .github/scripts/check_release_audit.py v0.6.0 in a throwaway clone", "why": "the snapshot is not a git repository and no tag exists; the refusal was derived by reading the script's path-coverage logic against release/audit-0.6.0.toml and the listed tasks' contract scopes"}
    ]
  },
  "evidence": {
    "SOL-audit-record-missing": "release/audit-0.6.0.toml: `grep -n 'SOL-' release/audit-0.6.0.toml` -> no output; `grep -c '^\\[\\[finding\\]\\]'` -> 22, all AUD-*; `grep -n '^task = '` lists only CR-234..CR-244. .github/scripts/check_release_audit.py:328-355 allows only ALWAYS_ALLOWED (lines 33-43) plus listed tasks' contract scopes; `grep -rn 'src/agentmarshal/stages.py' .agentmarshal/journal/tasks/CR-23*/contract.md CR-24*/contract.md` -> no match, so stages.py is uncovered",
    "SOL-changelog-cr246-missing": "CHANGELOG.md:227 '### Fixes from the release audit (CR-234, … CR-244)'; `grep -n 'CR-246' CHANGELOG.md` -> no output",
    "SOL-upgrading-outbox-missing": "UPGRADING.md:3-62 (0.5.0 -> 0.6.0 section); `grep -n 'outbox\\|autocrlf\\|-text\\|gitattributes' UPGRADING.md` -> only lines 50-53 (SENT manifest) and 135; behaviour exists at src/agentmarshal/outbox.py:705-708 and 879-891",
    "SOL-readme-refused-output": "README.md:53-54 'the level governs a recorded verdict's prose; a verdict that is refused keeps the reviewer's raw output at any level'; preservation is the launcher's malformed-output path: src/agentmarshal/journal/review.py:813-825 (_reject) -> 598-616 (_preserve_output)",
    "SOL-docs-status-overstated": "README.md:117-120, docs/quickstart.md:19-22, docs/sidecar.md:83-86 vs src/agentmarshal/cli.py:1469-1478 (LocalStateError caught, paths degrade to 'unavailable', comment: 'rather than failing a command that needed no git before') and src/agentmarshal/localstate.py:104-121",
    "SOL-spec-lane-carve-out": "openspec/specs/extension-stages/spec.md:44-52 ('SHALL print one line … returning success') vs src/agentmarshal/stages.py:1065-1077 (refusal with StageRunResult(1) ahead of the lane), demonstrated by tests/test_gate_operational.py:746-812; openspec/ is not in the contract's scope"
  }
}
AGENTMARSHAL_VERDICT_END
