Разобрался. Ниже — прозой по каждому критерию и по двум advisory-находкам.

## Критерии приёмки

**1. Отказ на symlink в пути outbox.** `src/agentmarshal/outbox.py:181-194` проверяет `outbox.parent` (`.agentmarshal`) и сам `upstream` через `is_symlink()` (lstat, без перехода) внутри `_locate`, то есть до любого `iterdir`, `open` или `git add` — отказ общий для всех четырёх подкоманд. Аргумент design-документа, что других компонентов быть не может, держится: `find_project_root` идёт по `_ancestors_from`, а тот делает `start.resolve()` (`project.py:50`), так что корень возвращается уже разрешённым и между ним и `.agentmarshal` символьных ссылок не остаётся. Со стороны `init` то же самое делает `_scaffold_outbox` (`project.py:343`), причём `.agentmarshal` отсекается ещё раньше — `write_project_file` (`project.py:190`) отказывает на symlink-родителе и дополнительно сверяет `resolved_parent != parent`, а вызывается он до scaffold (`project.py:475-480`). Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (реальный symlink на `tmp_path/outside`, четыре подкоманды, `list(outside.iterdir()) == []` и `rev-list --count --all == 0`), `test_a_linked_agentmarshal_component_refuses_the_command`, `test_init_never_scaffolds_through_a_linked_outbox` и `test_a_sidecars_linked_outbox_never_writes_the_host` — последний буквально проверяет формулировку threat-model «a sidecar never writes its host» (`docs/threat-model.md:192`).

**2. Отказ, когда staged-байты расходятся с проверенными.** `_pinned_blob` (`outbox.py:825-845`) берёт `hash-object --stdin --path=<rel>` (атрибуты применены) и `hash-object --stdin --no-filters` от тех же байт и возвращает `None` при расхождении; вызывающий код в `_check` (`outbox.py:692-704`) вместо pin кладёт problem «git would transform it on staging — …», что ставит `refused = True`, а `_run_send` отказывает через `result.status != 0`. Манифест `SENT` держится тем же правилом (`outbox.py:745-763`). Демонстрируют реальным clean filter (`sed s/a/b/` через `.gitattributes` + `filter.x.clean`): `test_send_refuses_a_draft_a_clean_filter_would_transform` (проверяет и `rev-list --count --all == 0`, и пустой `diff --cached`), `test_send_refuses_when_a_filter_would_transform_the_sent_manifest`, `test_check_refuses_a_draft_a_clean_filter_would_transform`, плюс eol-ветка — `test_an_end_of_line_refusal_names_the_attribute_that_turns_it_off` и `test_an_autocrlf_refusal_names_the_same_remedy`.

**3. `status` экранирует имена.** Все четыре места печати в `_run_status` переведены на `_printable` (`outbox.py:1231`, `1241`, `1249`) — маскировка сначала, экранирование потом, тот же порядок, что у `check`. Демонстрирует `test_a_control_character_in_a_file_name_is_escaped_in_the_report`.

**4. Delta и архив.** Архив лежит в `openspec/changes/archive/2026-10-25-outbox-boundaries/`, `openspec/changes/` больше ничего кроме `archive` не содержит — значит, прошла именно команда архивации. Delta несёт две ADDED-требования и одно MODIFIED; MODIFIED-блок воспроизводит заголовок `### Requirement: \`outbox status\` reports which findings an index file claims` байт в байт и все 11 сценариев в том же порядке, что и `openspec/specs/outbox/spec.md:276-349`. На каждый из девяти сценариев есть тест, docstring которого его называет (включая «the refusal line names the linked component masked» → `test_a_linked_components_path_is_masked_in_the_refusal`).

**5. Поведение без symlink/трансформации не изменилось.** `escape_for_display` (`journal/display.py:38-43`) возвращает строку как есть, когда `forges_rendered_text` ложно, так что печатаемые ASCII- и обычные Unicode-пути выглядят ровно как раньше; смена типа `InitializedProject.outbox` с `Path` на `str` безопасна — единственный потребитель `cli.py:555,560` подставляет его в f-строку. Полную CI-последовательность я не запускал и полагаюсь на заявление координатора о зелёном прогоне на d9af69c.

## Находки (обе не блокирующие)

**ADV-outbox-symlink-toctou** — проверка symlink сделана по схеме «lstat, затем открыть по имени»: `_locate` проверяет компоненты на `outbox.py:182`, а фактическая запись происходит позже и по пути — `draft.open("x")` в `_write_draft` (`outbox.py:357`), `sent_path.write_bytes` в `_run_send` (`outbox.py:1106`), `outbox.mkdir` в `_scaffold_outbox` (`project.py:352`). Между проверкой и записью `upstream` можно подменить на ссылку, и открытие по имени через неё пройдёт. В том же репозитории для project-файла применён более сильный приём — `_create_exclusive` с no-follow-дескриптором каталога (`project.py:180-207`); для outbox он не использован. Контракт требует только отказа «before any write», поэтому это не блокирует, но остаточное окно стоит зафиксировать.

**ADV-check-requires-git** — удаление флага `pin` сделало вычисление pin безусловным, и `outbox check` тем самым приобрёл жёсткую зависимость от работающего `git`: при `_OutboxGitError` из `_pinned_blob` (`outbox.py:693-697`) каждый файл получает problem «cannot be pinned», `refused` становится истиной и команда выходит с 1. Раньше при `pin=False` `check` не вызывал git вовсе, так что в окружении без git-бинарника или без рабочего дерева (например, проект скопирован вместе с `.agentmarshal/project.json`, но без `.git`) прежде он печатал отчёт о конформности и выходил 0, а теперь откажет. Вывод сделан чтением кода, не прогоном.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "d9af69c5b10641e5ff1006b5ec7ad63e24c696f2",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-outbox-symlink-toctou", "ADV-check-requires-git"],
  "classes": {
    "ADV-outbox-symlink-toctou": "security",
    "ADV-check-requires-git": "correctness"
  },
  "verification": {
    "read": [
      "src/agentmarshal/outbox.py (module docstring, _locate, _printable, _markers, _write_draft, _check, _pinned_blob, _autocrlf, _transform_cause, _batch_mismatch, _run_send, _run_status)",
      "src/agentmarshal/project.py (_ancestors_from, find_project_root, write_project_file, InitializedProject, _printable_path, _scaffold_outbox, initialize_project)",
      "src/agentmarshal/cli.py:535-575 (_run_init, the only consumer of InitializedProject.outbox)",
      "src/agentmarshal/journal/display.py:27-43 (escape_for_display)",
      "openspec/specs/outbox/spec.md (requirement and scenario headings; status requirement body at 276-349; new requirements at 495-556)",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/{proposal.md,design.md,tasks.md,specs/outbox/spec.md}",
      "docs/adr/ADR-0020-the-outbox-command-group.md decisions 3-5",
      "docs/threat-model.md:188-200 (\"A sidecar never writes its host\")",
      "tests/test_outbox.py (_project/_project_sha256 helpers and all tests added by the diff)",
      "AGENTS.md, CONTRIBUTING.md (grep for CHANGELOG convention)"
    ],
    "executed": [
      {
        "what": "ls openspec/changes/ && ls openspec/changes/archive/",
        "result": "openspec/changes/ holds only 'archive'; 2026-10-25-outbox-boundaries present there — the change was archived, not left in flight"
      },
      {
        "what": "grep -rn '\\.outbox\\b|outbox_error|InitializedProject|initialize_project' over src and tests",
        "result": "only cli.py:555,560 consume InitializedProject.outbox, both inside f-strings; tests touch outbox_error only — the Path->str change needs no out-of-scope edit"
      },
      {
        "what": "grep -n 'pin=|pin:' src/agentmarshal/outbox.py tests/test_outbox.py",
        "result": "no output — no leftover references to the removed pin parameter"
      },
      {
        "what": "grep -n '^### Requirement|^#### Scenario' openspec/specs/outbox/spec.md",
        "result": "status requirement carries 11 scenarios in the same order as the delta's MODIFIED block; the two ADDED requirements appear once each at lines 495 and 525"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "snapshot is not a git repository and the sandbox declined to run python/git/uv here; relied on the coordinator's statement that the sequence passed on d9af69c"
      },
      {
        "what": "a live probe of `git hash-object --stdin --no-filters` and of `git check-attr -z` output framing",
        "why": "sandbox refused the git invocation; both are exercised indirectly by the added tests and by the existing suite's passing no-transformation cases"
      },
      {
        "what": "an executed reproduction of ADV-check-requires-git in a project without a git work tree",
        "why": "no execution available; the claim is derived from outbox.py:692-697 alone and reported as advisory"
      }
    ]
  },
  "evidence": {
    "ADV-outbox-symlink-toctou": "src/agentmarshal/outbox.py:182 (is_symlink check in _locate) versus the later path-named writes at src/agentmarshal/outbox.py:357 (draft.open(\"x\")) and src/agentmarshal/outbox.py:1106 (sent_path.write_bytes), and src/agentmarshal/project.py:352 (outbox.mkdir); the stronger no-follow primitive the repo already has is src/agentmarshal/project.py:180-207 (write_project_file / _create_exclusive)",
    "ADV-check-requires-git": "src/agentmarshal/outbox.py:692-697 — `pinned_blob = _pinned_blob(...)` is now unconditional for every non-SENT entry and `except _OutboxGitError` appends to `problems`, which sets `refused = True` (outbox.py:731-733) and makes `_run_check` return 1; before the diff this ran only under `if pin and entry.name != _SENT`, and `_run_check` passed `pin=False`"
  }
}
AGENTMARSHAL_VERDICT_END
