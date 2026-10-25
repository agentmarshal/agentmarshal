Разобрал дифф по исходникам (запустить `pytest`/`git` в этой песочнице нельзя — bash отказал и в `git`, и в `python3`, так что всё проверено чтением файлов; прохождение CI беру из записки координатора).

## Критерии приёмки

**AC-1 (отказ на симлинке до любой записи)** — выполнен. `_locate` (`src/agentmarshal/outbox.py:181-195`) проверяет `.agentmarshal` и `upstream` через `is_symlink()` (lstat, без перехода) до `outbox.is_dir()` и до любого I/O, так что все четыре подкоманды отказывают одинаково; строка печатается через `_printable`, т.е. маскированной. Корень проекта у `find_project_root` уже resolved (`project.py:49-74`), поэтому «компонентов между корнем и outbox» ровно два — проверены оба. `init` закрыт в `_scaffold_outbox` (`project.py:342-346`) до `mkdir`/README. Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (реальный симлинк на `tmp_path/outside`, 4 отказа, `outside` пуст, `rev-list --count --all == 0`), `test_a_linked_agentmarshal_component_refuses_the_command`, `test_a_sidecars_linked_outbox_never_writes_the_host` (`host/stolen` не появляется), `test_init_never_scaffolds_through_a_linked_outbox`, `test_a_linked_components_path_is_masked_in_the_refusal`, плюс `test_init_names_the_linked_outbox_escaped` / `_masked`.

**AC-2 (только проверенные байты коммитятся)** — выполнен. `_pinned_blob` (`outbox.py:832-851`) сравнивает `hash-object --stdin --path=…` с `--no-filters` тех же байтов, расхождение не пиннится, а отказывается (`outbox.py:704-708`), и манифест `SENT` держится тем же правилом (`outbox.py:751-770`); сбой самого git — тоже отказ, а не тихий пропуск. Демонстрируют: `test_check_refuses_a_draft_a_clean_filter_would_transform` и `test_send_refuses_a_draft_a_clean_filter_would_transform` (настоящий clean-фильтр `filter.x.clean = sed s/a/b/`, у send ещё `rev-list == 0` и пустой `diff --cached`), `test_send_refuses_when_a_filter_would_transform_the_sent_manifest`, `test_an_end_of_line_refusal_names_the_attribute_that_turns_it_off`, `test_an_autocrlf_refusal_names_the_same_remedy`, `test_check_refuses_when_git_cannot_verify_a_files_staged_bytes`, `test_the_cannot_verify_reason_is_masked_and_display_escaped`, `test_a_transformation_with_no_known_cause_names_none`.

**AC-3 (`status` экранирует имена)** — выполнен: `safe_path(_shown_name(...))` заменён на `_printable` во всех трёх местах, где `status` печатает имя (`outbox.py:1241`, `1251`, `1259`). Демонстрирует `test_a_control_character_in_a_file_name_is_escaped_in_the_report` (имя с `\n`, в выводе `bad\\nname.md`, сырого перевода строки нет).

**AC-4 (дельта и архивирование)** — выполнен: дельта несёт два ADDED-требования и два MODIFIED с полным текущим текстом — я сверил блок «`outbox check` scans what would be sent…» из дельты со `openspec/specs/outbox/spec.md:91-180`, совпадает включая заголовок и порядок сценариев; каждый сценарий назван докстрингом теста (перечислены выше). В `openspec/specs/outbox/spec.md` девять требований, каждое ровно один раз; живого каталога `openspec/changes/outbox-boundaries/` нет, change лежит под `archive/2026-10-25-outbox-boundaries/` с `.openspec.yaml`, как у остальных 34 архивных changes.

**AC-5 (прежнее поведение)** — выполнен в части вывода: для печатаемых имён `_printable` и `_printable_path` дают ту же строку, что `str(path)`, а успешный вывод `check` не изменился; пины в выводе не участвуют. Прохождение полной последовательности CI не проверял сам — беру из записки координатора.

## Замечания (не блокирующие)

**advisory-check-now-requires-git** — `outbox check` из git-независимой команды стал git-зависимой: теперь он на каждую запись outbox поднимает два `git hash-object` (плюс `check-attr`/`config` при расхождении) и отказывает, если git не запускается (`outbox.py:692`, `751-754` — раньше этот блок жил под `pin=True`, т.е. только в `send`). Это сознательно записано в спеку (`openspec/specs/outbox/spec.md:110-113`, сценарий на строке 175) и мотивировано ADR-0020 decision 3, но контракт просил отказ только у `send`, так что стоит знать: цена нового гарантированного свойства — несколько процессов git на файл и новый класс отказа, не покрытый тремя условиями AC-5.

**advisory-filter-cause-misattributed** — `_transform_cause` (`outbox.py:908-911`) объявляет «a clean filter applies — the filter must not apply to the outbox» по одному факту, что атрибут `filter` выставлен, не проверяя, настроен ли для него `clean`. При `.gitattributes` вида `.agentmarshal/upstream/** filter=x working-tree-encoding=UTF-16` без `filter.x.clean` в конфиге байты переписывает кодировка, а отказ назовёт несуществующий clean-фильтр и единственное предложенное средство («фильтр не должен применяться к outbox») расхождение не снимет — тогда как спека требует назвать «the file and the remedy». Класс — plausible: выполнить git здесь я не мог, но то, что `working-tree-encoding` действительно даёт расхождение, подтверждает проходящий `test_a_transformation_with_no_known_cause_names_none`.

**advisory-threat-model-not-updated** — `docs/threat-model.md` остался индексом прежних гарантий: абзац «The symlink refusals the specifications state» (`:166-176`) по-прежнему перечисляет для outbox только «A non-regular file in the outbox is named as not checked», а открытый вопрос 2 (`:522-537`) повторяет тот же список, хотя спека теперь содержит требование «the outbox refuses a symbolic link in its path» (`openspec/specs/outbox/spec.md:502-530`) — то самое, ради которого контракт цитирует «a sidecar never writes its host». `docs/` вне scope контракта, поэтому это не правка, а departure, которую следовало назвать в итоговом отчёте.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "57b3953a36d3e9aae383df930ee2978d636c8222",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-check-now-requires-git",
    "advisory-filter-cause-misattributed",
    "advisory-threat-model-not-updated"
  ],
  "classes": {
    "advisory-check-now-requires-git": "scope",
    "advisory-filter-cause-misattributed": "correctness",
    "advisory-threat-model-not-updated": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n '^### Requirement:' openspec/specs/outbox/spec.md", "result": "9 requirement headings, each exactly once; new ones at :502 (symbolic link in its path) and :532 (refuse a file git would transform)"},
      {"what": "ls openspec/changes/ and openspec/changes/archive/2026-10-25-outbox-boundaries/", "result": "openspec/changes/ holds only archive/; the change dir holds .openspec.yaml, design.md, proposal.md, specs/, tasks.md — .openspec.yaml present in 34 archived changes, so consistent with the archive command"},
      {"what": "grep -rn 'InitializedProject|outbox_created|\\.outbox\\b' src tests (excluding test_outbox.py)", "result": "only cli.py:555,558,560 print the field and test_journal.py reads outbox_created — the Path->str change breaks no consumer"},
      {"what": "grep -rn 'MINIMUM_GIT_VERSION' src/", "result": "doctor.py:72 MINIMUM_GIT_VERSION = (2, 31), so `git config --type=bool-or-str` (git >= 2.22) is always available — no finding on _autocrlf"},
      {"what": "grep -n 'outbox|symlink|never writes its host' docs/threat-model.md", "result": ":166-176 and :522-537 still list only the non-regular-file statement for the outbox — evidence for advisory-threat-model-not-updated"}
    ],
    "read": [
      "src/agentmarshal/outbox.py (whole file)",
      "src/agentmarshal/project.py (whole file)",
      "tests/test_outbox.py:1-120 and :1860-2402",
      "openspec/specs/outbox/spec.md:1-194, :283-358, :498-565",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/ (design.md, proposal.md, tasks.md, specs/outbox/spec.md via the diff)",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/threat-model.md:160-205, :505-549",
      "src/agentmarshal/cli.py:525-565",
      "src/agentmarshal/journal/capture.py (safe_path)",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "tests/test_journal.py:2440-2545",
      "gitflic-ci.yaml, README.md:108-125"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the sandbox denied python3 and every git invocation, so the suite could not be executed here; CI result taken from the coordinator's note on this commit"},
      {"what": "git hash-object --path/--no-filters and git check-attr -z probes in a scratch repo", "why": "bash refused every git command in this session (permission required, non-interactive), so git's behaviour was taken from its documented semantics and from the passing new tests"}
    ]
  },
  "evidence": {
    "advisory-check-now-requires-git": "src/agentmarshal/outbox.py:692 and :751-754 call _pinned_blob unconditionally (the `pin` flag is gone from _check, outbox.py:534); _pinned_blob (outbox.py:843-850) runs two `git hash-object` processes per entry and _transform_cause (outbox.py:896-917) adds `check-attr` and `config` on a mismatch; openspec/specs/outbox/spec.md:110-113 and :175-179 sanction the new refusal",
    "advisory-filter-cause-misattributed": "src/agentmarshal/outbox.py:908-911 — `if attributes.get(\"filter\", \"unspecified\") not in (\"unspecified\", \"unset\"): causes.append(\"a clean filter applies — the filter must not apply to the outbox\")`, with no check that filter.<name>.clean is configured; the remedy contract is openspec/specs/outbox/spec.md:532-540",
    "advisory-threat-model-not-updated": "docs/threat-model.md:166-176 (\"A non-regular file in the outbox is named as not checked\" is still the only outbox entry) and :522-537 (open question 2 repeats that list) versus openspec/specs/outbox/spec.md:502-530 (new requirement) — docs/ is outside the contract's scope list"
  }
}
AGENTMARSHAL_VERDICT_END
