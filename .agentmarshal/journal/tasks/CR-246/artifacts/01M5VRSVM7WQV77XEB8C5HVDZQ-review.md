Разбор по каждому критерию приёмки — что в диффе его выполняет и какой тест это демонстрирует.

**1. Файловая форма manifest читается base-tree reader'ом.** `_base_extensions` заменён на `_base_manifests` (`src/agentmarshal/stages.py:335`), который читает `_manifest_from_tree` для **всех** перечисленных имён, а не только для directory-form (`stages.py:1118`, и в тихой ветке операционного полосы — `:1106`). Отказ reader'а теперь валит команду через существующий `except (GateError, ExtensionManifestError)` на `:1119` с именем расширения и его tree source. Демонстрируют: `tests/test_stages.py:361` (битый `openspec.toml` → `invalid TOML extension manifest: <base>:.agentmarshal/extensions/openspec.toml`) и `tests/test_stages.py:392` (file-form manifest с `[[stage]] command = "bin/check.py"` → отказ `_refuse_single_file_directory_paths`, `journal/extensions.py:542`); через общий runner — `tests/test_complete_stages.py:261` под префиксом `complete:`. «File-form всё ещё не планирует stage» держится структурно: любой путь под `bin/`/`lock/` в file-form форме отвергается, а `stage.command` обязателен, так что корректный file-form manifest не может объявить stage; это пинит существующий `tests/test_stages.py:330`. Проверил и то, что собственный `.agentmarshal/extensions/openspec.toml` этого репозитория — schema 1 без stage/`[dependencies]`/`[wraps]` — то есть новое чтение его не ломает.

**2. Маскировка пути в диагностике leak-scan.** `cli.py:1791` — `escape_for_display(safe_path(str(error), markers))`; `markers` на этой точке уже прочитаны из base tree (`cli.py:1737`). `safe_path` (`journal/capture.py:312`) заменяет маркер на `<private marker #N>`. Демонстрирует `tests/test_leak_scan_acknowledgements.py:305`: директория задачи, названная маркером, роняет `list_task_statuses` через `TaskStatusError(ValueError)` с `invalid task directory: <path>` (`journal/status.py:212`), и тест требует `<private marker #1>` в stderr при полном отсутствии самого маркера. Остальные диагностики leak-scan, печатающие пути, стоят до чтения маркеров (`cli.py:1710`, `:1743`) — замаскировать их нечем, это не регрессия.

**3. Отказ `--skip-ext <shared>` на операционной полосе.** Перечисление имён поднято перед веткой полосы (`stages.py:1059`), цикл отказа — `:1068-1076`, то есть до `operational_candidate(...)` и до любого чтения manifest. Решение принимается только по именам из `_extension_names_at_tree`, manifest не читается. Демонстрируют `tests/test_gate_operational.py:746` (`stage run`) и `:779` (`complete`): у расширения намеренно битый manifest, а run всё равно печатает строку отказа, `"invalid TOML" not in captured.err`, `extension-event` нет, completed-записи нет. Отдельно проверил, что подъём перечисления не может сломать операционный путь: `operational_candidate` сама глотает `ExtensionManifestError` из того же перечисления и возвращает `None` (`journal/gate.py:1095-1101`), так что сбой перечисления и операционная полоса несовместимы — выход остаётся тем же `1` с тем же сообщением, что и раньше.

**4. Раскрытие нереализованного runtime lookup.** `docs/threat-model.md:506-513` — рядом с текстом про изоляцию stage, и `CHANGELOG.md` в «What 0.6.0 leaves out». Оба утверждения сверил с кодом: `_MINIMAL_PATH = "/usr/bin:/bin"` (`stages.py:180`, применяется на `:707`, и PATH из `isolation.env` не пробрасывается — `:1174-1186`); lookup действительно живёт только в `doctor` как `extension runtime <name>` (`doctor.py:575`, докстринг `:510-528`); формулировка ADR-0013 решение 13 с поправкой («`doctor` and the stage output name the path and version found») — `docs/adr/ADR-0013-...:229-242`.

**5. Минимум git 2.31.** `README.md:117-121`, `docs/quickstart.md:19-23`, `docs/sidecar.md:83-87`. Совпадает с уже закодированной в проекте границей `MINIMUM_GIT_VERSION = (2, 31)` (`doctor.py:72`) и с реальным вызовом `git rev-parse --path-format=absolute` (`project.py:400-407`). Оговорки тоже точны: `complete` падает, потому что идёт через `local_state` → `git_common_dir` (`localstate.py:113-121`, вызов `cli.py:1124`), а `status` деградирует до «unavailable» вместо отказа (`cli.py:1467-1476`).

**6. Запись аудита.** `release/audit-0.6.0.toml:135-162` — ровно пять `[[finding]]` с `disposition = "fixed"`, `task = "CR-246"` и комментарием про gpt-6.1-sol после release-аудита; заголовок абзаца фиксов в `CHANGELOG.md` назвал CR-246. Проверил по `check_release_audit.py`, что весь дифф покрыт: все затронутые пути попадают либо в `ALWAYS_ALLOWED`, либо в scope контракта CR-246 (в частности `openspec/changes/archive/` покрывает новый архив, `openspec/specs/gate-lanes/` — изменённый spec). Сам скрипт не запускал (см. ниже); он дополнительно требует `completed`-записи CR-246 в помеченном дереве, а её пишет harness уже после ревью — сейчас в `CR-246/records/` только opened и три amendment, что и ожидается.

**7. UPGRADING и формулировка про capture.** `UPGRADING.md:55-66` — в секции «0.5.0 → 0.6.0»; и причина, и средство совпадают с кодом: `check-attr filter/text/eol` плюс `core.autocrlf` (`outbox.py:898-918`) и ровно та же подсказка `.agentmarshal/upstream/** -text` (`outbox.py:920-923`), плюс проверка staged-блобов перед коммитом батча. `README.md:53` теперь говорит про отказ launcher'а от некорректного вывода reviewer'а — это и есть то, что сохраняет сырой вывод (`journal/review.py:812-824`, `_preserve_output` в temp-файл вне journal, то есть действительно на любом capture level), а не «отклонённый verdict».

**8. MODIFIED-блоки.** Сравнил построчно: блок requirement'а в `openspec/changes/archive/2026-10-26-operational-skip-ext-refusal/specs/extension-stages/spec.md:15-47` совпадает с `openspec/specs/extension-stages/spec.md:30-62` байт в байт, включая заголовок; все 9 сценариев requirement'а присутствуют (spec: строки 64, 71, 77, 83, 89, 95, 99, 104, 112). То же для gate-lanes: 3 сценария, заголовок и текст идентичны. Новый сценарий назван в докстрингах обоих новых тестов (`test_gate_operational.py:749` и `:782`). Change лежит под `archive/` с датой 2026-10-26 и без остатка в `openspec/changes/`, пин OpenSpec — `1.15.0` (`.agentmarshal/extensions/openspec.toml:20,33`).

**9. Никаких иных изменений поведения.** Единственный вызов, на который новое перечисление влияет вне фикса, — `_personal_entries`/`_base_switches`, и они получают тот же `extension_names`, что и прежде (старый `_base_extensions` возвращал объединение имён, не только directory-form). Существующий тест отказа `--skip-ext` (`tests/test_personal_extensions.py:870`) и существующие операционные транскрипты (`test_gate_operational.py:718`, `:730`) не затронуты. `# noqa: E501` на длинных докстрингах соответствует принятой в репозитории практике (`tests/test_switches.py:150`).

Блокирующих и advisory-замечаний нет.

Чего я не запускал: в этой песочнице команды `uv`/`python3` отклонены политикой разрешений, поэтому `pytest`, `ruff`, `mypy`, `agentmarshal validate`, `openspec validate` и `check_release_audit.py v0.6.0` не исполнялись — опирался на заметку координатора о прошедшем CI на этом коммите и на чтение кода, тестов и спеков. Снапшот к тому же не git-репозиторий, так что гейт релиза в нём в принципе не воспроизвести.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8c6bffd5d35ac6d4d9e4b2da3baab52f4ff88cbf",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "read": [
      "src/agentmarshal/stages.py (_base_manifests, run_stages ordering, _MINIMAL_PATH, module docstring)",
      "src/agentmarshal/cli.py (_run_leak_scan, _leak_scan_acknowledgements, complete pre-gate invocation, status local-state fallback)",
      "src/agentmarshal/journal/gate.py (_manifest_from_tree, _manifest_blob_present, _extension_names_at_tree, operational_candidate, _switches_at_tree)",
      "src/agentmarshal/journal/extensions.py (parse_extension_manifest_text, _manifest_directory_paths, _refuse_single_file_directory_paths)",
      "src/agentmarshal/journal/capture.py (safe_path)",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "src/agentmarshal/journal/status.py (list_task_statuses, TaskStatusError)",
      "src/agentmarshal/journal/review.py (_preserve_output, _reject, dry-run preservation)",
      "src/agentmarshal/doctor.py (MINIMUM_GIT_VERSION, _check_git_available, _extension_checks)",
      "src/agentmarshal/project.py (git_common_dir), src/agentmarshal/localstate.py (local_state)",
      "src/agentmarshal/outbox.py (_transform_cause, _autocrlf, pinned-blob verification)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md decision 13 as amended",
      "docs/threat-model.md:475-518, README.md:38-62 and :114-125, CHANGELOG.md:300-355, UPGRADING.md:52-68, docs/quickstart.md:16-24, docs/sidecar.md:80-90",
      "openspec/specs/extension-stages/spec.md and openspec/specs/gate-lanes/spec.md against the change's delta specs (requirement text and every scenario)",
      "openspec/specs/leak-scan/spec.md (the standing 'masked the way every printed name is' rule)",
      "release/audit-0.6.0.toml and .github/scripts/check_release_audit.py (ALWAYS_ALLOWED, _check_findings, _contract_scope, _last_lifecycle_record)",
      "tests/test_stages.py:330-425, tests/test_complete_stages.py:261-298, tests/test_gate_operational.py:718-825, tests/test_leak_scan_acknowledgements.py:1-100 and :305-330, tests/test_personal_extensions.py:98-168 and :870-890",
      ".agentmarshal/extensions/openspec.toml (this repo's own file-form manifest), .gitattributes, pyproject.toml ruff/mypy config"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "every uv/python invocation in this sandbox was refused by the permission policy; relied on the coordinator's note that the full CI sequence passed on 8c6bffd5"
      },
      {
        "what": "OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.15.0 validate",
        "why": "no node/npx execution available; the MODIFIED blocks were instead compared line by line against the archived specs by reading both files"
      },
      {
        "what": "python3 .github/scripts/check_release_audit.py v0.6.0 in a throwaway clone with a local tag",
        "why": "the snapshot is not a git repository and python3 execution was refused; the script's requirements were checked by reading it against release/audit-0.6.0.toml and CR-246's contract scope. CR-246's 'completed' record does not exist yet because the harness writes it after this review"
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
