Прочитал весь затронутый код в снапшоте (запускать `git`/`python` в этой сессии не разрешено — тесты и CI не прогонял, опираюсь на заявление координатора).

**Как diff закрывает критерии приёмки**

- **Критерий 1 (отказ на симлинк до любой записи).** `_locate` (`src/agentmarshal/outbox.py:175-194`) проверяет `.agentmarshal` и `upstream` через `is_symlink()` до `outbox.is_dir()` и до любого I/O, и все четыре подкоманды идут через `_locate` (`_run_new:368`, `_check:644`, `_run_send:1065`, `_run_status:1217`). Претензия design-документа, что хватает двух компонентов, проверяема: `find_project_root` → `_ancestors_from` делает `start.resolve()` (`src/agentmarshal/project.py:50`), так что корень проекта уже без симлинков. Для `init` то же в `_scaffold_outbox` (`project.py:343-347`), причём `write_project_file` ещё и требует `parent.resolve() == parent` (`project.py:198-204`). Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (все четыре команды, реальный симлинк на `tmp_path/outside`, плюс `rev-list --count --all == "0"`), `test_a_linked_agentmarshal_component_refuses_the_command`, `test_init_never_scaffolds_through_a_linked_outbox`, `test_a_sidecars_linked_outbox_never_writes_the_host` (форма из threat-model, `docs/threat-model.md:192`), `test_a_linked_components_path_is_masked_in_the_refusal`, `test_init_names_the_linked_outbox_escaped/masked`.
- **Критерий 2 (только проверенные байты коммитятся).** `_pinned_blob` (`outbox.py:825-845`) сравнивает `hash-object --stdin --path=<relative>` с `--no-filters` тех же байтов; равенство blob-id в одном object-формате эквивалентно равенству байтов, так что проверка действительно формат-агностична. Несовпадение не пинится, а отказывает (`outbox.py:692-703` для файлов, `746-762` для `SENT`), и `_batch_mismatch` по-прежнему держит индекс на пинах. Демонстрируют: `test_send_refuses_a_draft_a_clean_filter_would_transform` и `test_send_refuses_when_a_filter_would_transform_the_sent_manifest` (реальный `filter.x.clean = sed s/a/b/`), плюс check-сторона: `test_check_refuses_a_draft_a_clean_filter_would_transform`, `test_an_end_of_line_refusal_names_the_attribute_that_turns_it_off`, `test_an_autocrlf_refusal_names_the_same_remedy`, `test_a_filter_refusal_names_no_eol_remedy_under_unset_text`.
- **Критерий 3 (`status` экранирует имена).** `_run_status` печатает через `_printable` все три места, где раньше был `safe_path(_shown_name(...))` (`outbox.py:1230`, `1241`, `1248`); остальное, что печатает `status` — только hex-дайджесты и числа. Демонстрирует `test_a_control_character_in_a_file_name_is_escaped_in_the_report`.
- **Критерий 4 (delta + архив).** Delta лежит в `openspec/changes/archive/2026-10-25-outbox-boundaries/specs/outbox/spec.md`: два ADDED-требования со сценарием на каждое поведение и MODIFIED-требование `outbox status`, заголовок которого совпадает байт в байт с `openspec/specs/outbox/spec.md:276` и несёт все 11 сценариев (10 прежних + новый). В `openspec/specs/outbox/spec.md` каждое требование встречается ровно один раз (9 заголовков, проверено grep'ом), архив расположен как у соседних изменений.
- **Критерий 5 (без симлинка/трансформации печатает как раньше).** `escape_for_display` экранирует только то, что отвергает `forges_rendered_text` (`src/agentmarshal/journal/display.py:27-41`), так что печатные имена не меняются; файлы, которые пишет сам инструмент (`new`, README, `SENT`), создаются с `newline="\n"`, поэтому ни `text=auto`, ни `core.autocrlf` их не трансформируют. CI на d9af69c5 — по заявлению координатора.

**Замечания (все advisory, ни одно не блокирует)**

- `ADV-check-needs-git`: `outbox check` теперь на каждом запуске вызывает `git` для каждого файла аутбокса (`outbox.py:692`, `748`), тогда как раньше hash-object был под `if pin` и `check` не трогал git вовсе. В проекте без рабочего git-репозитория (git не установлен, `.git` удалён или не смонтирован) `check` теперь откажет с `cannot be pinned: git hash-object failed: ...` там, где раньше валидировал черновики и гонял leak-scan — это изменение поведения при условиях «no symlink, no git transformation» из критерия 5.
- `ADV-exit-zero-scenario-unmodified`: прежний сценарий `openspec/specs/outbox/spec.md:137-139` («WHEN every draft conforms and the scan finds nothing THEN the command exits 0») стал ложным, когда применяется clean-фильтр или eol-конверсия, а delta это требование не взяла в MODIFIED. Формулировка критерия 5 («no git transformation») оправдывает чтение сценария как условного, поэтому это не блокирует, но требование стоило бы оговорить.
- `ADV-new-prints-raw-path`: `outbox new` печатает путь черновика сырым (`outbox.py:380`), а `init` печатает `project_root` сырым рядом с уже экранированным `initialized.outbox` (`src/agentmarshal/cli.py:550` против `555`). Класс AUD-commands-6 (неэкранированное имя в выводе outbox) для `status` закрыт, для `new` и для stdout `init` остался открытым, так что утверждение proposal'а «the masked, display-escaped rendering the other subcommands use» шире фактического. Контракт просил только `status`, так что это follow-up, а не отступление.
- `ADV-transform-cause-asserts-unverified`: fallback `_transform_cause` печатает «a clean filter or eol conversion applies» (`outbox.py:918`) для любого несовпадения, включая вызванное `working-tree-encoding`, которое `check-attr` здесь не спрашивает; docstring той же функции говорит, что такой случай отказывается «without a named remedy» — строка всё же называет причину, которой может не быть.
- `ADV-git-stderr-not-escaped`: текст ошибки git печатается маскированным, но не display-escaped (`outbox.py:695`, `752-753`), а при `hash-object --path` в stderr попадает вывод самого clean-фильтра — то есть перевод строки оттуда может добавить строку в отчёт `check`. Код не новый, но diff делает его достижимым из `check`, где раньше его не было.
- `ADV-changelog-and-threat-model-stale`: новые отказы — наблюдаемое изменение поведения без записи в `CHANGELOG.md` (ср. запись для CR-228, `CHANGELOG.md:186`), а перечисление «The symlink refusals the specifications state» в `docs/threat-model.md:166-191` и пункт 2 его gap-списка (`docs/threat-model.md:522`) не знают о новом требовании. Оба пути вне scope контракта, так что это follow-up; в финальном отчёте исполнителя они должны быть названы как departure.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "d9af69c5b10641e5ff1006b5ec7ad63e24c696f2",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-check-needs-git",
    "ADV-exit-zero-scenario-unmodified",
    "ADV-new-prints-raw-path",
    "ADV-transform-cause-asserts-unverified",
    "ADV-git-stderr-not-escaped",
    "ADV-changelog-and-threat-model-stale"
  ],
  "classes": {
    "ADV-check-needs-git": "contract-mismatch",
    "ADV-exit-zero-scenario-unmodified": "contract-mismatch",
    "ADV-new-prints-raw-path": "claim-accuracy",
    "ADV-transform-cause-asserts-unverified": "claim-accuracy",
    "ADV-git-stderr-not-escaped": "security",
    "ADV-changelog-and-threat-model-stale": "scope"
  },
  "verification": {
    "read": [
      "src/agentmarshal/outbox.py (whole module: _locate, _printable, _markers, _run_new, _check, _pinned_blob, _autocrlf, _transform_cause, _git, _batch_mismatch, _run_send, _run_status)",
      "src/agentmarshal/project.py (_ancestors_from, find_project_root, write_project_file, InitializedProject, _printable_path, _scaffold_outbox, initialize_project)",
      "src/agentmarshal/cli.py:540-575 (_run_init output)",
      "src/agentmarshal/journal/display.py",
      "tests/test_outbox.py (header/helpers and every test added by the diff, plus test_the_sent_manifest_is_pinned_once_with_the_content_send_writes)",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/ (proposal.md, design.md, tasks.md, specs/outbox/spec.md, .openspec.yaml)",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/threat-model.md:160-200, 515-545",
      "pyproject.toml (ruff/mypy/pytest config)",
      "CHANGELOG.md:1-60, 183-191"
    ],
    "executed": [
      {
        "what": "grep -c '^### Requirement:' openspec/specs/outbox/spec.md and grep -n of the headings",
        "result": "9 requirements, each heading once; the two ADDED ones at lines 495 and 525, the MODIFIED status one at 276"
      },
      {
        "what": "find openspec/changes -name .openspec.yaml",
        "result": "present in ~34 of 100 archived changes, so the new archive's .openspec.yaml is a normal artifact, not a hand-made one"
      },
      {
        "what": "grep -rn 'sidecar never writes its host' docs/threat-model.md",
        "result": "docs/threat-model.md:192 — the quote the contract cites exists"
      },
      {
        "what": "grep -n '_ancestors_from' -A 20 src/agentmarshal/project.py",
        "result": "line 50 'current = start.resolve()' — the project root is resolved, so .agentmarshal and upstream are the only components that can be links"
      },
      {
        "what": "grep -n 'print(draft)|cannot be pinned|a clean filter or eol conversion applies' src/agentmarshal/outbox.py",
        "result": "380, 695, 752, 918 — the lines the advisory findings cite"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "command execution (git, python, uv) is denied in this review session; the coordinator states the sequence passed on the reviewed commit"
      },
      {
        "what": "a live check that `git hash-object --stdin --path=X` applies a clean filter and core.autocrlf while `--stdin --no-filters` does not",
        "why": "no shell execution available; inferred from git's documented behaviour and from the four new tests that assert it"
      }
    ]
  },
  "evidence": {
    "ADV-check-needs-git": "src/agentmarshal/outbox.py:692 and 748 call _pinned_blob unconditionally; the diff removed the `if pin and` guards (old: `if pin and entry.name != _SENT:`, `if pin and (manifest_old is not None or manifest_new):`), and _git (outbox.py:792-820) raises _OutboxGitError on any non-zero git exit, which becomes `problems.append(f\"cannot be pinned: ...\")` -> refused. `outbox check` therefore now needs a working git repository where before it touched git not at all.",
    "ADV-exit-zero-scenario-unmodified": "openspec/specs/outbox/spec.md:137-139 (`#### Scenario: conforming drafts with a clean scan exit 0` / WHEN every draft conforms and the scan finds nothing / THEN the command exits 0) versus the ADDED requirement at openspec/specs/outbox/spec.md:525 and the refusal at src/agentmarshal/outbox.py:697-703; the delta at openspec/changes/archive/2026-10-25-outbox-boundaries/specs/outbox/spec.md carries no MODIFIED entry for the exit-status requirement.",
    "ADV-new-prints-raw-path": "src/agentmarshal/outbox.py:380 `print(draft)` (a Path, neither masked nor display-escaped) against outbox.py:1230/1241/1248 where status now uses _printable; src/agentmarshal/cli.py:550 prints initialized.project_root raw while cli.py:555/560 print the now-escaped initialized.outbox. tests/test_outbox.py::test_init_names_the_linked_outbox_escaped only asserts on captured.err, so the raw stdout path is untested.",
    "ADV-transform-cause-asserts-unverified": "src/agentmarshal/outbox.py:918 `causes.append(\"a clean filter or eol conversion applies\")` is reached for any blob mismatch whose cause is not in the queried attributes (outbox.py:898 queries only filter, text, eol), while the function's own docstring (outbox.py:860-872) says such a case is \"refused without a named remedy\".",
    "ADV-git-stderr-not-escaped": "src/agentmarshal/outbox.py:695 `f\"cannot be pinned: {safe_path(str(error), markers)}\"` and 752-753 use safe_path without escape_for_display, while _git (outbox.py:816) builds the error text from git's stderr decoded with backslashreplace; a clean filter invoked by `hash-object --path` contributes to that stderr. Contrast outbox.py:252 `_printable`, which masks then escapes.",
    "ADV-changelog-and-threat-model-stale": "grep -n outbox CHANGELOG.md shows an entry for CR-228 at CHANGELOG.md:186 but none for the new refusals; docs/threat-model.md:166-191 enumerates \"The symlink refusals the specifications state\" without the outbox path refusal, and docs/threat-model.md:522-537 still lists the outbox's only specified symlink statement as the non-regular-entry rule. Both paths are outside the contract's scope list."
  }
}
AGENTMARSHAL_VERDICT_END
