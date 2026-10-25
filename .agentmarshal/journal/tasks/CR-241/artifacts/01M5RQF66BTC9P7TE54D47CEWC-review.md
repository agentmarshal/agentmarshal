Разобрался. Прочитал `src/agentmarshal/outbox.py`, `src/agentmarshal/project.py`, `src/agentmarshal/cli.py:538-580`, `tests/test_outbox.py`, оба spec-файла, ADR-0020, `docs/threat-model.md` и `extension_trust._managed_directory`; выполнил сверку delta↔spec через `diff` и проверил digest `_CONFORMING` через `sha256sum`. Запустить CI не смог — в снапшоте нет `uv`, а исполнение Python в этой песочнице не разрешено; факт зелёного CI на 3f57e02 беру из записки координатора.

**Что по acceptance criteria**

Критерий 1 (отказ на symlink до любой записи) выполнен: `outbox.py:181-195` проверяет `.agentmarshal` и `upstream` через `is_symlink()` (lstat) внутри `_locate`, то есть раньше проверки `outbox.is_dir()` и раньше любого создания файла; project root от `find_project_root` действительно уже resolved (`project.py:49-74`, `_ancestors_from` делает `start.resolve()`), поэтому «любой компонент между root и outbox» — это ровно `.agentmarshal`, и оба проверены. Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (реальный symlink на `tmp_path/outside` вне проекта, четыре подкоманды, `captured.out == ""`, `outside` пуст, `rev-list --count --all == "0"`), `test_a_linked_agentmarshal_component_refuses_the_command`, `test_a_sidecars_linked_outbox_never_writes_the_host`, `test_a_linked_components_path_is_masked_in_the_refusal` (маскировка через `_printable`), и для `init` — `test_init_never_scaffolds_through_a_linked_outbox` против `project.py:317-319`.

Критерий 2 (коммитятся только проверенные байты) выполнен: `_pinned_blob` (`outbox.py:825-844`) сравнивает `hash-object --stdin --path=<rel>` с `--no-filters` тех же байтов и при расхождении возвращает `None`, а вызывающий отказывает вместо того, чтобы пиновать (`outbox.py:698-702` для файлов, `756-761` для `SENT`); пин остаётся блобом проверенных байтов, так что `_batch_mismatch` на send — второй рубеж. Демонстрируют настоящим git clean filter (`filter.x.clean = sed s/a/b/`): `test_send_refuses_a_draft_a_clean_filter_would_transform`, `test_send_refuses_when_a_filter_would_transform_the_sent_manifest`, `test_check_refuses_a_draft_a_clean_filter_would_transform`, плюс eol-ветка — `test_an_end_of_line_refusal_names_the_attribute_that_turns_it_off` и `test_an_autocrlf_refusal_names_the_same_remedy`.

Критерий 3 (`outbox status` экранирует каждое имя) выполнен: `_run_status` печатает через `_printable` и путь index (`outbox.py:1222`), и путь outbox (`1230`), и имя каждой записи (`1238`); остальное, что он печатает, — hex-digest и номера строк. Демонстрирует `test_a_control_character_in_a_file_name_is_escaped_in_the_report` (`bad\nname.md` → в выводе `bad\\nname.md`, сырого перевода строки нет).

Критерий 4 (delta + архив) выполнен: `diff` показал, что секция ADDED архивной delta побайтово совпадает с `openspec/specs/outbox/spec.md:495-554`, а MODIFIED-требование — с `spec.md:276-349`, вместе с заголовком и всеми 11 сценариями (полный текущий текст, как требует контракт); все 9 новых сценариев имеют тест, docstring которого их называет; change лежит в `openspec/changes/archive/2026-10-25-outbox-boundaries/` с `.openspec.yaml` того же вида, что у 34 других архивных changes, активной директории `openspec/changes/outbox-boundaries/` не осталось.

Критерий 5 выполнен в части, которую я могу проверить: диффом не затронут ни один путь вне scope контракта, печатаемый вывод на обычном outbox не изменился (пины не печатаются), а зелёный CI беру из записки координатора. Одна трещина в «ведёт себя ровно как сегодня» — ниже, ADV-1.

**Findings (все advisory)**

ADV-1 — `advisory-check-requires-git`: в `outbox.py:684` и `745` пин стал безусловным (параметр `pin` удалён), поэтому `outbox check` впервые запускает git — два `hash-object` на каждый файл outbox, включая `README.md`, плюс пин `SENT`; в проекте, где git недоступен или `.git` отсутствует (а `find_project_root` требует только `project.json`), `check` теперь печатает `README.md: cannot be pinned: cannot run git: …` и выходит 1 там, где раньше выходил 0. Отказ fail-closed и решение осознанное (design.md, ADR-0020 decision 3), но ни сценария, ни теста на «git недоступен в check» нет.

ADV-2 — `advisory-eol-remedy-misleading`: в `_transform_cause` (`outbox.py:896-900`) `_autocrlf(project_root)` подмешан через `or` без оглядки на атрибут `text`, хотя собственный docstring функции (`outbox.py:871-873`) говорит «`core.autocrlf` where no attribute speaks»; при `.agentmarshal/upstream/** -text filter=x` и `core.autocrlf=true` отказ из-за clean filter дополнительно советует добавить `` `.agentmarshal/upstream/** -text` `` — средство, которое уже действует и байты не выровняет.

ADV-3 — `advisory-init-refusal-unmasked`: `project.py:319` возвращает `refusing to write through a symlink: {component}` с сырым путём, и `cli.py:556-560` печатает его без `safe_path`/`escape_for_display`, тогда как требование, которое этот код реализует, говорит, что отказ печатается «with the masking every outbox path gets», а `init`'s scaffold «SHALL refuse the same»; маскировка на момент `init` пуста по существу (markers ещё не настроены), но экранирование — нет: имя каталога с управляющим символом добавит строку в stderr `init` (это свойство уже было у двух обычных строк `init`, новая строка его наследует, а не вводит). Ср. `cli.py:599`, где текст ошибки наружу экранируется.

Отдельно, не как finding: `CHANGELOG.md` вне scope контракта, поэтому не тронут, — но конвенция репозитория фиксирует правки release audit отдельной секцией (`CHANGELOG.md:227`, «Fixes from the release audit (CR-235, CR-236)»), так что для AUD-commands-1/-2/-6 запись в 0.6.0 ещё предстоит сделать отдельной задачей.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "3f57e02f29601ad6f103851b945c5f121a448719",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-check-requires-git",
    "advisory-eol-remedy-misleading",
    "advisory-init-refusal-unmasked"
  ],
  "classes": {
    "advisory-check-requires-git": "contract-mismatch",
    "advisory-eol-remedy-misleading": "claim-accuracy",
    "advisory-init-refusal-unmasked": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {"what": "diff of the archived delta's ADDED section against openspec/specs/outbox/spec.md:495-554", "result": "identical apart from the '## ADDED Requirements' header"},
      {"what": "diff of the archived delta's MODIFIED requirement against openspec/specs/outbox/spec.md:276-349", "result": "identical apart from the '## MODIFIED Requirements' header; heading and all 11 scenarios present"},
      {"what": "grep -n '^### Requirement|^#### Scenario' openspec/specs/outbox/spec.md", "result": "9 new scenarios at lines 504-553, each matched by a test docstring in tests/test_outbox.py"},
      {"what": "find openspec -name .openspec.yaml", "result": "34 archived changes carry one; the new archive matches their 'schema: spec-driven' / 'created:' shape"},
      {"what": "ls openspec/changes/", "result": "only 'archive' — no leftover active outbox-boundaries directory"},
      {"what": "printf <_CONFORMING> | sha256sum", "result": "525780eeb61ad1c70358fd9c2cf4d4a164ea1176948a3bd3fffc96c126464134 — contains 'a', so the sed-based SENT filter test is deterministic, not flaky"},
      {"what": "grep -n '_managed_directory' -A 30 src/agentmarshal/extension_trust.py", "result": "extension_trust.py:212-227 uses the same lstat loop and the same 'refusing a symbolic link:' wording, confirming the design.md claim"},
      {"what": "grep -n 'never writes its host' docs/threat-model.md", "result": "docs/threat-model.md:192 — the quoted threat-model line exists"},
      {"what": "grep -rn 'AUD-commands' --include=*.md .", "result": "only the change's own proposal and the task contracts; no audit document needed updating"}
    ],
    "read": [
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/project.py",
      "src/agentmarshal/cli.py:530-605",
      "src/agentmarshal/journal/display.py:27-43",
      "tests/test_outbox.py",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/design.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/proposal.md",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/tasks.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/threat-model.md:192",
      "CHANGELOG.md:1-40,227-260"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "uv is not installed in this snapshot and running a Python interpreter was denied in this read-only session; the coordinator states the sequence passed on 3f57e02"},
      {"what": "the new symlink, clean-filter and control-character tests individually", "why": "same — the suite could not be executed here, so the tests were verified by reading them against the implementation"}
    ]
  },
  "evidence": {
    "advisory-check-requires-git": "src/agentmarshal/outbox.py:684 ('if entry.name != _SENT:' — was 'if pin and entry.name != _SENT:') and :745 ('if manifest_old is not None or manifest_new:' — was 'if pin and (...)'), with _run_check calling _check(stderr, index=index) at :531; _pinned_blob (:836-843) runs two 'git hash-object' subprocesses whose _OutboxGitError becomes 'cannot be pinned' at :694-696 and sets refused, so check exits 1 where it previously ran no git at all and exited 0",
    "advisory-eol-remedy-misleading": "src/agentmarshal/outbox.py:896-900 — 'attributes.get(\"text\", ...) not in (\"unspecified\", \"unset\") or attributes.get(\"eol\", ...) not in (...) or _autocrlf(project_root)'; git check-attr reports 'unset' for '-text', so the autocrlf disjunct still fires and :901-905 names the '-text' remedy, contradicting the docstring at :871-873 ('core.autocrlf where no attribute speaks')",
    "advisory-init-refusal-unmasked": "src/agentmarshal/project.py:317-319 returns f\"refusing to write through a symlink: {component}\" with the raw path; src/agentmarshal/cli.py:556-560 prints it as 'warning: could not create {initialized.outbox}: {initialized.outbox_error}' with neither safe_path nor escape_for_display, against openspec/specs/outbox/spec.md:497-502 ('printed with the masking every outbox path gets ... init's outbox scaffold SHALL refuse the same'); cf. src/agentmarshal/cli.py:599 where outward error text is escaped"
  }
}
AGENTMARSHAL_VERDICT_END
