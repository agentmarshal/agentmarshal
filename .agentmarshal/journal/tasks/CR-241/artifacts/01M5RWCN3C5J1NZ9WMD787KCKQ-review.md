Проверил diff статически: прочитал `src/agentmarshal/outbox.py`, `src/agentmarshal/project.py`, `src/agentmarshal/cli.py`, новые тесты, delta и архивированный spec, а также ADR-0020, `docs/threat-model.md` и `extension_trust._managed_directory`. Запустить `pytest`/`git`-пробы не смог: в снапшоте нет `uv`, а выполнение `python3` и `git` в этой среде заблокировано — поэтому зелёный CI на 57b3953 беру из записки координатора, сам не воспроизводил.

## Acceptance criteria

**AC-1 (отказ на symlink до любой записи) — выполнен.** `_locate` проверяет `outbox.parent` и `outbox` через `is_symlink()` (lstat, без разыменования) сразу после `find_project_root`, до `outbox.is_dir()` и до любого I/O (`src/agentmarshal/outbox.py:181-195`), а `_scaffold_outbox` — до `mkdir` и до открытия README (`src/agentmarshal/project.py:341-346`). Корень проекта действительно resolved: `_ancestors_from` делает `start.resolve()` (`project.py:48-52`), так что между корнем и `upstream` остаются ровно два компонента, и оба проверены. Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (`tests/test_outbox.py:1923`, все четыре подкоманды, `outside` пуст, `rev-list --count --all == 0`), `test_a_linked_agentmarshal_component_refuses_the_command` (:1959), `test_init_never_scaffolds_through_a_linked_outbox` (:1985), `test_a_sidecars_linked_outbox_never_writes_the_host` (:2018) и `test_a_linked_components_path_is_masked_in_the_refusal` (:2189) — последний проверяет и маскировку.

**AC-2 (отказ при расхождении staged-байтов) — выполнен.** `_pinned_blob` (`outbox.py:832-851`) сравнивает `hash-object --stdin --path=<rel>` с `hash-object --stdin --no-filters` тех же байтов и возвращает `None` при расхождении; вызывающий код пишет problem вместо пина (`outbox.py:692-710`), то же для `SENT` на содержимом, которое запишет `send` (`outbox.py:751-770`). Сравнение живёт в `check`, что согласуется с ADR-0020 решением 3 («Its exit status refuses on a failure, so a batch wrapper can refuse to send before publication», `docs/adr/ADR-0020-the-outbox-command-group.md:87-88`) — противоречия с названным решением нет. Побочный эффект приятный: поскольку пин теперь равен blob'у сырых байтов, `_batch_mismatch` ловит фильтр и во второй раз, уже после `git add`. Демонстрируют: `test_send_refuses_a_draft_a_clean_filter_would_transform` (:2046, реальный `filter.x.clean = sed s/a/b/`), `test_check_refuses_a_draft_a_clean_filter_would_transform` (:2114), `test_send_refuses_when_a_filter_would_transform_the_sent_manifest` (:2073), `test_an_end_of_line_refusal_names_the_attribute_that_turns_it_off` (:2139), `test_an_autocrlf_refusal_names_the_same_remedy` (:2166), `test_a_filter_refusal_names_no_eol_remedy_under_unset_text` (:2229), `test_check_refuses_when_git_cannot_verify_a_files_staged_bytes` (:2256), `test_the_cannot_verify_reason_is_masked_and_display_escaped` (:2282), `test_a_transformation_with_no_known_cause_names_none` (:2318). Логика `-text` в `_transform_cause` совпадает с `convert_attrs()` в git: `-text` даёт `CRLF_BINARY` и глушит и `eol`, и `core.autocrlf`, поэтому remedy названо только там, где оно что-то меняет.

**AC-3 (escaping в `outbox status`) — выполнен.** `_run_status` печатает имена через `_printable` (`outbox.py:1259`), и путь индекса с путём аутбокса тоже (`:1240`, `:1251`); единственное, что печатается мимо — hex-дайджест. Демонстрирует `test_a_control_character_in_a_file_name_is_escaped_in_the_report` (:2095): `bad\\nname.md` в выводе, сырого `bad\nname.md` нет.

**AC-4 (delta + архив) — выполнен.** Delta несёт ADDED на два требования и MODIFIED с полным текстом для `outbox check` scans… и `outbox status` reports…; число сценариев совпадает с архивированным файлом (12 и 11), новые сценарии на месте, каждый назван в docstring соответствующего теста. В `openspec/specs/outbox/spec.md` каждое требование встречается ровно один раз (`:502`, `:532`), `openspec/changes/` пуст кроме `archive/`, а `.openspec.yaml` архива совпадает по форме с соседними. Все затронутые пути — внутри scope контракта; departures нет.

**AC-5 (никаких регрессий + CI) — не проверял сам.** Статически обычный путь не меняется: `safe_path`/`escape_for_display` возвращают строку как есть, если маскировать и экранировать нечего, а `text=auto`/`autocrlf=true` на LF-содержимом дают одинаковые blob id, так что отказ не срабатывает. Прогон CI не воспроизводил — помечаю как not_run.

## Находки

**ADV-init-agentmarshal-link-dead-branch** (advisory, `src/agentmarshal/project.py:343`): новая проверка `project_directory.is_symlink()` в `_scaffold_outbox` недостижима из `initialize_project` — `write_project_file` отказывает на симлинке `.agentmarshal` раньше (`project.py:189-193`) и бросает `UnsafeProjectPathError`, так что `init` падает с кодом 1 вместо best-effort-предупреждения, а путь печатается сырым (`msg = f"refusing to write through a symlink: {offender}"`), не через `_printable_path`. Половина нового поведения «`init`'s outbox scaffold SHALL refuse the same» для компонента `.agentmarshal` фактически обеспечивается другим, не-best-effort отказом, и ни один тест её не покрывает: `test_init_never_scaffolds_through_a_linked_outbox` линкует `upstream`, а `tests/test_project.py` зовёт `_scaffold_outbox` только на нормальном каталоге. Ветка безвредна (защитная, и `_scaffold_outbox` вызывается из тестов напрямую), поэтому advisory, но именованный в AC-1 случай «component between the project root and it» у `init` стоит закрыть тестом либо маскировкой в `write_project_file`.

**ADV-init-project-root-unescaped** (advisory, `src/agentmarshal/cli.py:550`): `init` печатает первой строкой `Initialized AgentMarshal project at {initialized.project_root}` сырым `Path`, тогда как соседняя строка про аутбокс теперь идёт через `_printable_path`. Собственный тест диффа это и показывает: `test_init_names_the_linked_outbox_escaped` (:2346) создаёт репозиторий с именем `re\npo` и утверждает `captured.err.count("\n") == 1`, но stdout в том же прогоне получает лишний перевод строки из `project_root`. То есть подделка строки, закрытая для пути аутбокса, остаётся открытой строкой выше. `cli.py` вне scope контракта, и сырая печать путей — сложившийся стиль модулей вне outbox (`journal/open_task.py:58`, `journal/records.py:1966`), поэтому только advisory: правка потребовала бы файла за пределами scope и её стоило бы назвать departure.

Блокирующих дефектов не нашёл.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "57b3953a36d3e9aae383df930ee2978d636c8222",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-init-agentmarshal-link-dead-branch",
    "ADV-init-project-root-unescaped"
  ],
  "classes": {
    "ADV-init-agentmarshal-link-dead-branch": "test-gap",
    "ADV-init-project-root-unescaped": "scope"
  },
  "verification": {
    "read": [
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/project.py",
      "src/agentmarshal/cli.py (init output, lines 540-580)",
      "src/agentmarshal/extension_trust.py (_managed_directory)",
      "src/agentmarshal/journal/capture.py (safe_path, imports)",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "src/agentmarshal/journal/records.py (imports)",
      "tests/test_outbox.py",
      "tests/test_project.py",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/design.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/proposal.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/tasks.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/threat-model.md (line 192)",
      "AGENTS.md",
      "CONTRIBUTING.md (changelog mentions)",
      "pyproject.toml (pytest config)"
    ],
    "executed": [
      {
        "what": "grep -rn 'a sidecar never writes its host' / 'never writes' docs/",
        "result": "docs/threat-model.md:192 '**A sidecar never writes its host.**' — the quoted threat-model property exists"
      },
      {
        "what": "grep -n '_managed_directory' -A 25 src/agentmarshal/extension_trust.py",
        "result": "extension_trust.py:212-227 checks (managed.parent, managed) with is_symlink() and raises 'refusing a symbolic link' — the comment's claim in _locate is accurate"
      },
      {
        "what": "grep -n '^from|^import' src/agentmarshal/journal/capture.py src/agentmarshal/journal/display.py src/agentmarshal/journal/records.py",
        "result": "capture.py:41 and records.py:31 both import agentmarshal.project, so the function-level import in _printable_path is genuinely required to avoid a cycle"
      },
      {
        "what": "grep -rn '\\.outbox\\b|InitializedProject|_scaffold_outbox' --include=*.py .",
        "result": "only cli.py:555,560 consume InitializedProject.outbox (f-string interpolation) and tests/test_project.py uses _scaffold_outbox's Path return — the Path->str field change breaks no caller"
      },
      {
        "what": "grep -n '^### Requirement|^#### Scenario' openspec/specs/outbox/spec.md",
        "result": "each new requirement appears exactly once (:502, :532); check-scan requirement has 12 scenarios and status requirement 11, matching the delta's MODIFIED blocks one for one"
      },
      {
        "what": "grep -rn 'refusing to write through a symlink' --include=*.py .",
        "result": "project.py:192 prints the raw offender (reached when .agentmarshal is a link, before _scaffold_outbox runs); project.py:345 is the new masked one — evidence for ADV-init-agentmarshal-link-dead-branch"
      },
      {
        "what": "ls openspec/changes/ ; ls openspec/changes/archive/ | tail -5",
        "result": "openspec/changes/ holds only archive/; the archived directory name and .openspec.yaml match the convention of neighbouring 2026-10-24/25 entries"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "uv is not installed in this snapshot and executing python3 is not permitted in this environment; relying on the coordinator's statement that the sequence passed on 57b3953a"
      },
      {
        "what": "git probes of hash-object --stdin --path vs --no-filters, core.autocrlf with --type=bool-or-str, and check-attr -z field shape",
        "why": "running git and python3 is blocked here; verified instead by reading git's documented semantics and convert_attrs()/index_mem() behaviour against the tests that assert them"
      }
    ]
  },
  "evidence": {
    "ADV-init-agentmarshal-link-dead-branch": "src/agentmarshal/project.py:343-346 adds `for component in (project_directory, outbox): if component.is_symlink(): return outbox, f\"refusing to write through a symlink: {_printable_path(component)}\"`, but initialize_project calls write_project_file first (project.py:480 after :477), and write_project_file already refuses at project.py:189-193 with `msg = f\"refusing to write through a symlink: {offender}\"` (raw, unmasked, unescaped) raising UnsafeProjectPathError, which cli.py:546-548 turns into exit 1. No test linksomething at .agentmarshal and then runs init: tests/test_outbox.py:1985 and :2346 and :2378 all link .agentmarshal/upstream, and tests/test_project.py:15,33 call _scaffold_outbox on a plain tmp_path.",
    "ADV-init-project-root-unescaped": "src/agentmarshal/cli.py:550 `print(f\"Initialized AgentMarshal project at {initialized.project_root}\")` interpolates a raw Path, while cli.py:555 and :560 now print the escaped str from project.py:481 `_printable_path(outbox)`. tests/test_outbox.py:2346-2376 builds `repo = tmp_path / \"re\\npo\"`, asserts `captured.err.count(\"\\n\") == 1`, and never inspects stdout, where the unescaped project_root adds a second line."
  }
}
AGENTMARSHAL_VERDICT_END
