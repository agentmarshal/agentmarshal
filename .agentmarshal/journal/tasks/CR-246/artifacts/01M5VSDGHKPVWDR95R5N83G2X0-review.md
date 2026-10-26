Проверил diff статически: исходники, спеки, доки и новые тесты прочитал; запустить тесты/линтеры в этом снапшоте не вышло (нет venv, снапшот не git-репозиторий, запуск python не разрешён) — поэтому результаты CI беру из записки координатора и помечаю прогон как не выполненный.

## Что по критериям приёмки

**1. Файловая форма манифеста читается через base-tree reader.** `_base_extensions` заменён на `_base_manifests` (`src/agentmarshal/stages.py:335-350`), который читает `_manifest_from_tree` для **каждого** перечисленного имени, а не только для directory-form; вызовы — `stages.py:1118` (обычный путь) и `stages.py:1106` (quiet-ветка операционной полосы). Отказ reader'а действительно падает командой с именем расширения и его tree-источником: сообщение приходит из `journal/extensions.py:383` (`invalid TOML extension manifest: <sha>:…`) и из `_refuse_single_file_directory_paths` (`journal/extensions.py:542-545`) для манифеста, объявляющего `bin/`-путь. Демонстрируют `tests/test_stages.py::test_a_broken_file_form_manifest_at_the_base_fails_the_run` и `::test_a_command_declaring_file_form_manifest_at_the_base_fails_the_run`, а через общий runner — `tests/test_complete_stages.py::test_a_file_form_manifest_the_base_refuses_fails_the_completion`. «Файловая форма по-прежнему не планирует стадий» держится существующим `tests/test_stages.py::test_a_file_form_extension_has_no_stage_to_run` (schema-1 без `[[stage]]` — reader пропускает, план пуст); собственный `.agentmarshal/extensions/openspec.toml` этого репозитория (schema 1, без стадий и локов) новую читку тоже проходит, так что `stage run` самого проекта не ломается.

**2. Диагностика leak-scan маскируется.** `cli.py:1791` — `escape_for_display(safe_path(str(error), markers))`, именно в заявленном порядке; `markers` к этой точке уже прочитаны с доверенного дерева (`cli.py:1734-1743`). Путь в сообщении даёт `TaskStatusError` (подкласс `ValueError`, `journal/status.py:65,212`), так что ветка `except (…, ValueError)` его ловит. Демонстрирует `tests/test_leak_scan_acknowledgements.py::test_a_marker_in_a_task_directory_name_is_masked_in_the_diagnostic`.

**3. Операционная полоса отказывает на shared-имени в `--skip-ext`.** Перечисление имён (`stages.py:1059`, `_extension_names_at_tree(...)[0]` — только листинг дерева, без чтения манифестов) и цикл отказа (`stages.py:1064-1076`) стоят **до** `operational_candidate` (`stages.py:1080`). Демонстрируют `tests/test_gate_operational.py::test_a_shared_name_in_skip_ext_is_refused_on_the_operational_lane` и `::test_complete_skip_ext_naming_a_shared_extension_is_refused_on_the_lane`; оба используют расширение с намеренно битым манифестом и проверяют, что `invalid TOML` в stderr нет, — то есть манифест действительно не читается, и ADR-0013 решение 17 не нарушено. Регрессии в обработке ошибок разделение одного `try` на два не вносит: оба блока ловят ту же пару `(GateError, ExtensionManifestError)`, а сбой перечисления и раньше заканчивался выходом 1, потому что `operational_candidate` сам глотает его и возвращает `None` (`journal/gate.py:1094-1100`).

**4. Непреализованный runtime-lookup раскрыт.** `docs/threat-model.md:506-513` и `CHANGELOG.md:347-352`. Проверил по коду: в `stages.py` слова `runtime` нет вообще, проверка живёт только в `doctor.py:575` (`extension runtime <name>`), `_MINIMAL_PATH = "/usr/bin:/bin"` (`stages.py:180`), и ссылка на спеку («the command runs as an argv process under the core's interpreter», `openspec/specs/extension-stages/spec.md:174`) точна — спека сама фиксирует `PATH` и никакого lookup не обещает.

**5. git 2.31.** `README.md:117-122`, `docs/quickstart.md:19-23`, `docs/sidecar.md:83-87`. Подтверждено кодом: `project.py:407` зовёт `rev-parse --path-format=absolute`, `doctor.py:72` объявляет `MINIMUM_GIT_VERSION = (2, 31)` с тем же обоснованием; `complete` падает на `LocalStateError` (`cli.py:1175`), а `status` деградирует до «unavailable» (`cli.py:1469-1475`) — то есть оговорка про `status` верна. Правка quickstart лежит выше секции «The governed loop», которую парсит `tests/test_quickstart.py`, так что транскрипты не затронуты.

**6. Запись аудита.** `release/audit-0.6.0.toml:134-162` — пять `[[finding]]` (`SOL-extensions-1`, `SOL-extensions-2`, `SOL-commands-2`, `SOL-docs-claims-1-1`, `SOL-docs-claims-1-3`), `disposition = "fixed"`, `task = "CR-246"`, с комментарием про измерительный аудит gpt-6.1-sol по тем же коммитам после релизного; `CHANGELOG.md:227` называет CR-246 в заголовке абзаца про audit-fixes. Сам `check_release_audit.py` я не запускал (нет git-репозитория), но прочитал его: формат таблиц он принимает, а diff-покрытие сходится — каждый путь этого diff'а попадает либо в `ALWAYS_ALLOWED`, либо в scope CR-246 (`openspec/changes/archive/`, `openspec/specs/extension-stages/`, `openspec/specs/gate-lanes/`, `docs/…`, `src/…`, `tests/`); остаётся требование `completed`-записи у CR-246, которую пишет harness.

**7. UPGRADING и README.** Пункт про `outbox` стоит внутри секции «0.5.0 → 0.6.0» (`UPGRADING.md:55-65`) и совпадает с кодом: отказ и проверка застейдженных блобов (`outbox.py:700-710`), а формулировка средства — дословно из `_transform_cause` (`outbox.py:920-923`), где `_OUTBOX_DIR_SPEC` разворачивается в `.agentmarshal/upstream` (`outbox.py:75`). Правка `README.md:53-54` («launcher's refusal of malformed reviewer output keeps the raw output at any level») тоже верна: `_reject`/`_preserve_output` (`journal/review.py:599-825`, `1565`, `1616`) сохраняют сырой вывод независимо от capture level, а уровень управляет только прозой записанного вердикта.

**8. MODIFIED-блоки.** Дельты `openspec/changes/archive/2026-10-26-operational-skip-ext-refusal/specs/extension-stages/spec.md` и `.../gate-lanes/spec.md` несут требования с заголовками дословно и всеми сценариями (9 и 3 соответственно); сверил чтением с архивированным результатом — `openspec/specs/extension-stages/spec.md:30-118` и `openspec/specs/gate-lanes/spec.md:344-379` совпадают с дельтами построчно, включая новый сценарий. Docstring'и обоих новых тестов (`tests/test_gate_operational.py:749,782`) повторяют заголовок сценария дословно. Противоречий с соседним требованием «a shared extension is never named in a personal switch» (`spec.md:1721-1727`) нет — новая формулировка прямо на него ссылается.

**9.** Поведенческих изменений помимо заявленных не нашёл: комментарии и docstring'и в `stages.py` обновлены под новую читку, устаревших утверждений про directory-form в модуле нет.

## Findings (оба advisory, ни одно не блокирует)

- `ADV-leak-scan-diff-diagnostic-unmasked` — тот же дефект класса SOL-commands-2 остался на соседнем call-site в том же файле: `src/agentmarshal/cli.py:1751` печатает `leak-scan: git diff failed: {error}` с сырым текстом ошибки, без `safe_path` и без `escape_for_display`, хотя `markers` в этой точке уже прочитаны (`cli.py:1734-1743`), а сообщение `GateError` целиком состоит из stderr git'а (`journal/gate.py:312-316`). Критерий 2 требовал только диагностику acknowledgements, так что это не невыполненный критерий — но для 0.7.0 это ровно та же правка.
- `ADV-dead-directory-names-return` — после замены `_base_extensions` на `_base_manifests` второй элемент кортежа `_extension_names_at_tree` (`src/agentmarshal/journal/gate.py:949-1002`, «(every name, directory-form)») больше никем не используется: оба вызова берут `[0]` (`gate.py:1095`, `stages.py:1059`). Чистка лежит в `journal/gate.py`, которого в scope CR-246 нет, так что здесь это только пометка — но в отчёте о задаче departure/следствие не упомянуто.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8c6bffd5d35ac6d4d9e4b2da3baab52f4ff88cbf",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-leak-scan-diff-diagnostic-unmasked",
    "ADV-dead-directory-names-return"
  ],
  "classes": {
    "ADV-leak-scan-diff-diagnostic-unmasked": "security",
    "ADV-dead-directory-names-return": "style"
  },
  "verification": {
    "read": [
      "src/agentmarshal/stages.py (module docstring, _base_manifests 335-350, run_stages 980-1230)",
      "src/agentmarshal/journal/gate.py (_manifest_from_tree 661-728, _extension_names_at_tree 949-1002, operational_candidate 1054-1102, _run_git_bytes 302-317, leak_scan_diff 1161-1198, operational-lane manifest reads 1580-1715)",
      "src/agentmarshal/journal/extensions.py (_manifest_directory_paths 514-545, invalid-TOML message 383)",
      "src/agentmarshal/cli.py (_run_leak_scan 1677-1855, complete refusal 1156-1190, status local-state degradation 1460-1495)",
      "src/agentmarshal/journal/capture.py (safe_path 312-331)",
      "src/agentmarshal/journal/display.py (escape_for_display 27-43)",
      "src/agentmarshal/journal/status.py (TaskStatusError 65, list_task_statuses 196-219)",
      "src/agentmarshal/doctor.py (MINIMUM_GIT_VERSION 70-73, git check 130-158, extension runtime check 515-580)",
      "src/agentmarshal/project.py (git_common_dir 390-425), src/agentmarshal/localstate.py (local_state 104-122)",
      "src/agentmarshal/outbox.py (check refusals 690-770, _transform_cause 879-930, _OUTBOX_DIR_SPEC 75)",
      "src/agentmarshal/journal/review.py (_preserve_output 599-616, _reject 814-825, launcher 1540-1625, dry run 1240-1300)",
      "openspec/specs/extension-stages/spec.md (30-118, 174-215, 1695-1745), openspec/specs/gate-lanes/spec.md (343-379), openspec/specs/leak-scan/spec.md (1-60, 395-470)",
      "openspec/changes/archive/2026-10-26-operational-skip-ext-refusal/ (proposal.md, design.md, tasks.md, specs/extension-stages/spec.md, specs/gate-lanes/spec.md)",
      "docs/threat-model.md (255-270, 488-520, 605-620), docs/quickstart.md (16-24), docs/sidecar.md (78-90), README.md (40-70, 112-124), CHANGELOG.md (28-45, 224-230, 268-285, 300-356, 473-490), UPGRADING.md (1-75)",
      "release/audit-0.6.0.toml, .github/scripts/check_release_audit.py",
      "tests/test_stages.py (helpers 44-93, 330-420), tests/test_complete_stages.py (1-130, 258-300), tests/test_gate_operational.py (1-60, 743-815), tests/test_leak_scan_acknowledgements.py (1-95, 302-330), tests/test_personal_extensions.py (_stage_run_skip 98-119, _complete 144-169), tests/test_quickstart.py (13-40)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decision 13, manifest example), .agentmarshal/extensions/openspec.toml"
    ],
    "executed": [
      {
        "what": "grep -rn \"_extension_names_at_tree\" src/ tests/ openspec/ docs/",
        "result": "only two production call sites, both taking [0] (stages.py:1059, gate.py:1095) — the tuple's directory-form half is unused"
      },
      {
        "what": "grep -rn \"runtime\" src/agentmarshal/stages.py; grep -rn \"extension runtime\" src/",
        "result": "no hit in stages.py; the check exists only at doctor.py:524,575 — the threat-model/CHANGELOG disclosure is accurate"
      },
      {
        "what": "grep -rn \"path-format\" src/ docs/; grep -n MINIMUM_GIT_VERSION src/agentmarshal/doctor.py",
        "result": "project.py:407 uses the flag; doctor.py:72 declares (2, 31) with the same rationale as the new doc text"
      },
      {
        "what": "grep -c \"^#### Scenario:\" on both delta spec files; grep -rn \"Scenario: a shared name in --skip-ext\" openspec/ tests/",
        "result": "9 and 3 scenarios; the new scenario heading appears in both archived specs, both deltas and the two test docstrings"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "no virtualenv in the snapshot and python/uv execution not permitted here; relying on the coordinator's statement that the sequence passed at this commit"
      },
      {
        "what": "python3 .github/scripts/check_release_audit.py v0.6.0 in a throwaway clone",
        "why": "the snapshot is not a git repository and has no tag; verified the audit file's shape and the script's diff-coverage rule by reading instead"
      },
      {
        "what": "byte-for-byte diff of the delta MODIFIED blocks against the archived specs",
        "why": "shell quoting/permissions blocked the extraction; compared line by line by reading both files"
      }
    ]
  },
  "evidence": {
    "ADV-leak-scan-diff-diagnostic-unmasked": "src/agentmarshal/cli.py:1751 `print(f\"leak-scan: git diff failed: {error}\", file=stderr)` — no safe_path, no escape_for_display, while markers are already resolved at cli.py:1734-1743; the GateError text is raw git stderr (src/agentmarshal/journal/gate.py:312-316). Compare the fixed site at cli.py:1791 and the same idiom in src/agentmarshal/outbox.py:700-702.",
    "ADV-dead-directory-names-return": "src/agentmarshal/journal/gate.py:949-951 returns `tuple[frozenset[str], frozenset[str]]` documented as \"(every name, directory-form)\"; after this diff both callers discard the second element — src/agentmarshal/stages.py:1059 and src/agentmarshal/journal/gate.py:1095 each take `[0]` (grep -rn \"_extension_names_at_tree\" src/ tests/ shows no other use)."
  }
}
AGENTMARSHAL_VERDICT_END
