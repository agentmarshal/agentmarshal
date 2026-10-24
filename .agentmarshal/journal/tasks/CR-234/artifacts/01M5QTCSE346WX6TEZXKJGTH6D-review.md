Проверил дифф против кода, спеков, ADR и журнала. Ниже — по каждому acceptance criterion, затем две advisory-находки и verdict.

## Что проверено по критериям

**AC1 (секция `## 0.6.0 — unreleased`, покрытие задач).** Секция стоит над `0.5.0`, открывается заявлением о неизменных схемах и ссылкой на UPGRADING.md. Схемы сверены с кодом: record max = 7 (`records.py:227,239,247,300`, схема 8 отказана), contract header ∈ {1,2,3} (`contracts.py:191`), manifest ∈ {1,2} (`extensions.py:387`) — то есть «0.5.0 читает журнал 0.6.0» держится (`tool_version` — свободная строка, `records.py:_check_tool_version`). Покрытие задач полное: `-completed.json` есть ровно у CR-205…CR-233, CR-235, CR-236 (CR-234 — эта задача, CR-237 только `opened`), и каждая из них либо названа в заголовке записи, либо в закрывающей строке (CR-205, CR-226, CR-230). Атрибуции заголовков сверены с `title` контрактов — совпадают все (CR-208 = status/implementer session, CR-209 = trust/untrust/list, CR-210 = gate warning + `status --base`, CR-211 = `stage run`, CR-212 = `record-ext`, CR-213 = doctor listing, CR-216 = doctor runtime, CR-215 = `accept --pause`). Тестов на CHANGELOG нет и быть не может — критерий проверяется чтением.

**AC2 (каждое утверждение секции против кода).** Выборочно, но плотно: grant-поля `directory_hash/granted_by/granted_by_source/granted_at/files` (`extension_trust.py:99-108`), строки `granted` / `not granted` / `changed after approval: <path> (<kind>)` и отсутствие строки у single-file манифеста (`extension_trust.py:719-742`, `continue` на `not entry.is_dir()`); вокабуляр результатов `checked` / `failed (exit <n>)` / `did not finish (timeout)` / `not run` / `switched off` (`stages.py:913-962`); `extension-event` и «журнал не трогается» (`stages.py:1004`); exit 3 на `pre-gate-stop` (`stages.py:969-971`, `cli.py:1150`); `CI == "true"` (`stages.py:1124`); `record-ext` флаги и 64 KiB + `payload_sha256` (`record_ext.py:28,90-104`); doctor `extension manifest <name>` с деталью `<form> form, manifest schema <n>` и `extension runtime <name>` (`doctor.py:400,557,575`); `WARN: <task>: ext record <id> kind '<kind>': addressee not found` (`validate.py:186-190`); операционная линия — «изменённая запись должна назвать задачу, удалённая отказывается, прочие top-level ключи идентичны» и `PASS: operational transaction (operational lane; review not required)` с тремя `NOT EXAMINED` (`gate.py:1355,1409-1449,1451,1483-1484`), демонстрируется `tests/test_gate_operational.py::test_the_operational_lane_admits_a_switches_only_candidate` и `::test_a_removed_entry_is_refused_naming_the_file_and_the_entry`; изоляция ровно в границах threat-model (`isolation.py:310-312,396-398,451`, `stages.py:1180-1194`), демонстрируется `tests/test_isolation.py`/`tests/test_stages.py`; `complete --target` и предупреждение вместо отказа на смёрженном кандидате (`cli.py:1134-1150`), демонстрируется `tests/test_complete_stages.py`; CR-233 перепроверен уже на master (`stages.py:70-92,667,675,766-776`, `tests/test_personal_extensions.py`); unmeasured на Cost-строке считает именно сессии без cost, оставленные вне сумм (`report.py:98-109,155,730-747`, `tests/test_report_cost_checks_findings.py`); аудит-гейт действительно только процесс — `check_release_audit.py` и шаг до `uv build` (`.github/workflows/release.yml:53-65`), демонстрируется `tests/test_release_audit_check.py`; CR-235/CR-236 — проекция чужих задач с FAIL-строкой (`gate.py:2070-2136`), `timestamp-text` на `created_at/started_at/ended_at/resets_at` (`records.py:618-637`, `tests/test_record_text_safety.py`), кодирование до создания файла (`records.py:2113-2124`), байт-в-байт сохранение вывода ревьюера (`review.py:599-617`).

**AC3 (что не вошло).** Все пять пунктов на месте и с источником; проверено, что ни один не выдан за поставленный: `plan.toml` только путь в local state и никем не читается (`localstate.py:70-73`, ссылок больше нет), `agentmarshal next` отсутствует, `carried_approval` / `mode: resolution` в record model и `record-schema` спеке нет вовсе, user-scope зарезервирован дословно «arrives when an adopter asks» (`ADR-0013:166`), таблица схем кончается на 7.

**AC4 (UPGRADING 0.5.0 → 0.6.0).** Секция над `0.4.1 → 0.5.0`, «нет схемы — нет порядка обновления» согласуется с проверенными выше границами схем; `not run (not granted)` / `not run (changed after approval: <path>)`, CI без гранта, `complete --target`, `SENT`/`check --index` (`outbox.py:120-141,643-647,722-723`) и чтение пина как декларации (`extension-manifest` спек, верхнеуровневый `version` нигде не сверяется с установленным продуктом) — всё сходится. Демонстрируют `tests/test_extension_trust.py`, `tests/test_stages.py`, `tests/test_outbox.py`.

**AC5 (индексы и threat model).** 020 показан как shipped в 0.5.0; строки 018, 019, 023–032, 034–037, 039–042, 044, 045 перепроверены против 0.5.0-секции CHANGELOG и кода — ни одна не объявляет поставленным то, чего нет (043 и 038 честно «not shipped yet», 032 честно разделяет «helper поставлен / экспозиция линии гейта — нет»: шаблон действительно гоняет полный гейт, `templates/github/agentmarshal-governance.yml:78`). Цитата ADR-0018 («…satisfies the contract» and nothing more) есть дословно (`ADR-0018:33`), `outbox status --index` действительно матчит по source-хешу (`outbox.py:1060-1130`). Threat model: четыре command-level отказа без stage-строки подтверждены кодом (`stages.py:1035-1049` — unknown phase, sidecar, task id проверен вызывающей командой; непарсящийся манифест базы — в том же try) и названия сценариев существуют в `openspec/specs/extension-stages/spec.md:80,92,96,308`; демонстрируют `tests/test_stages.py::test_a_sidecar_runs_no_stages`, `::test_an_invalid_task_identifier_refuses_before_any_stage_is_planned`, `::test_a_malformed_trust_toml_fails_the_command_naming_it`, `::test_a_manifest_the_base_cannot_parse_fails_the_run_naming_the_extension` (у unknown phase отдельного теста нет — его ловит `choices` argparse, `stages.py:284`). README про outbox подтверждён `project.py:311-326` и тестом `tests/test_journal.py::test_init_scaffolds_the_upstream_outbox`. docs/README.md — строки 044/045 в точной форме строк 041–043.

**AC6 (правки по аудиту).** journal-only = каждый путь под `.agentmarshal/journal/` (`gate.py:78,1252`), операционная линия существует — демонстрируют `tests/test_gate.py::test_the_journal_only_lane_prints_no_count_line` и `tests/test_gate_operational.py::test_pre_gate_stages_do_not_run_on_an_operational_change`; «0.4.1 как текущий релиз» в overview.md больше нет ни одного упоминания. self-hosting-workflow: acceptance, покрывающая блокирующие findings ровно, действительно удовлетворяет проверку вердикта (`gate.py:1757-1801`, сравнение множеств), демонстрируют `tests/test_gate.py::test_gate_passes_valid_acceptance_without_reporting_approval` и `::test_gate_re_derives_acceptance_findings_exactly`. Правка UPGRADING 0.4.1 → 0.5.0 точна: линия реализации печатает `INFO: changes_required verdicts for <task>: <count> (threshold <n>)` (`gate.py:2273-2276`), демонстрирует `tests/test_gate.py::test_the_implementation_lane_prints_the_count`. Открытый вопрос threat model: `gate-lanes` спек действительно покрывает ссылку на switches-файле (`openspec/specs/gate-lanes/spec.md:249-250`, реализация `gate.py:1044-1045`) — отдельного теста на симлинк нет, критерий выполнен утверждением спеки.

**AC7 (версия).** `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11` = `0.6.0`; `--version` печатает `__version__` (`cli.py:131`); демонстрируют `tests/test_smoke.py::test_version_is_declared` и `::test_console_version_prints_package_version`. Ни одного остатка `0.6.0.dev0` вне журнальных записей.

**AC8 (ничего лишнего).** Дифф трогает ровно 12 путей из scope, секция 0.5.0 и более ранние в CHANGELOG не изменены, под `.agentmarshal/journal/` ничего не пишется, все добавленные ссылки (ADR-0013/0015/0018/0022, UPGRADING.md, proposals/044, /045) ведут в существующие файлы. Полную CI-последовательность в этой read-only песочнице выполнить нельзя — нет `uv` и `pytest`; по координаторской заметке она прошла на этом коммите, своей проверки у меня нет.

## Advisory

**ADV-DOC-OPLANE-SCOPE-001** — в UPGRADING.md (секция 0.5.0 → 0.6.0, пункт «The operational lane carries a switches change») сказано, что кандидат, меняющий только `.agentmarshal/switches.toml` и пути внутри поддерева своей задачи, «passes the gate without review», но гейт требует ещё и чтобы контракт задачи объявлял `scope` ровно этим одним файлом — иначе линия закрыта (`src/agentmarshal/journal/gate.py:1007`, тест `tests/test_gate_operational.py:164 test_a_contract_declaring_another_scope_does_not_take_the_lane`); для задачи, открытой `extension switch off`, утверждение верно (`switch_off.py:463`), а для написанной руками — нет, и те же формулировки в `docs/overview.md:138-144` и `docs/threat-model.md` условие тоже не упоминают.

**ADV-DOC-RECORD-TYPES-002** — в `docs/overview.md:110-112` (файл в scope этой задачи) перечисление типов записей по-прежнему заканчивается на `opened/finding/review/acceptance/amendment/completed/reopened/abandoned` + `session` и не содержит четырёх типов схемы 7, поставленных ещё в 0.5.0 — `check`, `agreement`, `acknowledgement`, `ext` (`src/agentmarshal/journal/records.py:138,147,165` и `CHANGELOG.md:439-441`); это предсуществующая неточность, не входящая в перечисленные в AC6 правки аудита, поэтому чинить её в этом диффе означало бы расширить его — отмечаю, чтобы аудит не прошёл мимо.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "7b5386687d6932b75bd5340a7b8d25cd69f68012",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-DOC-OPLANE-SCOPE-001", "ADV-DOC-RECORD-TYPES-002"],
  "classes": {
    "ADV-DOC-OPLANE-SCOPE-001": "claim-accuracy",
    "ADV-DOC-RECORD-TYPES-002": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn version pyproject.toml src/agentmarshal/__init__.py uv.lock tests/test_smoke.py", "result": "all four read 0.6.0; no 0.6.0.dev0 left outside journal records"},
      {"what": "find .agentmarshal/journal/tasks -name '*-completed.json' -printf '%h\\n' | sort -u", "result": "completed: CR-205..CR-233, CR-235, CR-236; CR-234 and CR-237 only opened — matches the section's coverage and the closing line"},
      {"what": "grep -m1 '^title' of contracts CR-205..CR-236", "result": "every task id in a 0.6.0 heading matches the contract it is attributed to"},
      {"what": "grep -n '_JOURNAL_PREFIX\\|journal_only' src/agentmarshal/journal/gate.py", "result": "gate.py:78 '.agentmarshal/journal/'; gate.py:1252 all(path.startswith(prefix)) — overview.md's journal-only definition confirmed"},
      {"what": "sed -n '969,1017p' src/agentmarshal/journal/gate.py", "result": "operational_candidate admits switches.toml plus .agentmarshal/journal/tasks/<task>/ and requires contract.scope == (switches,) — basis of ADV-DOC-OPLANE-SCOPE-001"},
      {"what": "grep -n 'changes_required verdicts for' src/agentmarshal/journal/gate.py", "result": "gate.py:2274 INFO line on the implementation lane — UPGRADING's 0.4.1->0.5.0 correction confirmed"},
      {"what": "grep -rn scenario names cited by threat-model in openspec/specs/extension-stages/spec.md", "result": "lines 80, 92, 96, 308 — all four quoted scenarios exist"},
      {"what": "grep -n 'not a file' openspec/specs/gate-lanes/spec.md; sed -n '1040,1048p' src/agentmarshal/journal/gate.py", "result": "spec:249-250 and gate.py:1044 refuse a link at switches.toml — threat-model open question 2 confirmed"},
      {"what": "sed -n '298,331p' src/agentmarshal/project.py", "result": "init writes .agentmarshal/upstream/README.md — README claim confirmed"},
      {"what": "grep -rn 'plan_file\\|carried_approval\\|\"mode\"' src tests openspec", "result": "plan.toml only a path property (localstate.py:70), no carried_approval and no review mode anywhere — 'leaves out' paragraph confirmed"},
      {"what": "sed -n '585,640p' src/agentmarshal/journal/records.py; sed -n '2092,2125p'", "result": "timestamp-text rule over created_at/started_at/ended_at/resets_at and encode-before-create — CR-236 entry confirmed"},
      {"what": "sed -n '596,730p' src/agentmarshal/outbox.py", "result": "SENT manifest, 'skipped as sent: <n>', leak scan runs on every entry including sent ones — CR-228 entry confirmed"},
      {"what": "which uv pytest", "result": "not installed in the review sandbox"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section and the 0.5.0 section it refers to)",
      "UPGRADING.md (0.5.0->0.6.0 and the 0.4.1->0.5.0 note)",
      "README.md",
      "docs/overview.md",
      "docs/self-hosting-workflow.md",
      "docs/threat-model.md (stage-line refusals, isolation, open questions 2 and 5)",
      "docs/proposals/README.md (all batch tables)",
      "docs/README.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0018-governing-the-contract.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/quickstart.md (contract guidance)",
      "docs/proposals/032-the-journal-has-no-time-axis.md",
      "openspec/specs/gate-lanes/spec.md",
      "openspec/specs/extension-stages/spec.md",
      "openspec/specs/extension-manifest/spec.md",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/validate.py",
      "src/agentmarshal/journal/review.py",
      "src/agentmarshal/journal/status.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/isolation.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/record_ext.py",
      "src/agentmarshal/project.py",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/doctor.py",
      "templates/journal-transaction.sh",
      "templates/github/agentmarshal-governance.yml",
      ".github/workflows/release.yml",
      ".github/scripts/check_release_audit.py",
      ".agentmarshal/extensions/openspec.toml",
      ".agentmarshal/journal/tasks/CR-204..CR-237/contract.md (headers)",
      "tests/test_smoke.py",
      "tests/test_gate_operational.py",
      "tests/test_stages.py",
      "tests/test_gate.py (count line, acceptance, not-a-file)",
      "tests/test_journal.py (init outbox)",
      "tests/test_project.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "read-only review sandbox has neither uv nor pytest installed; the coordinator states the full sequence passed on this commit and I make no independent claim about it"},
      {"what": "agentmarshal --version at runtime", "why": "package not installed in the sandbox; verified statically through cli.py:131 and tests/test_smoke.py:48,59"}
    ]
  },
  "evidence": {
    "ADV-DOC-OPLANE-SCOPE-001": "src/agentmarshal/journal/gate.py:1007 — `if contract is None or contract.scope != (switches_module.SWITCHES_RELPATH,): return None`, i.e. the lane needs the contract's scope to be exactly that one file; tests/test_gate_operational.py:164 test_a_contract_declaring_another_scope_does_not_take_the_lane. UPGRADING.md's bullet 'The operational lane carries a switches change' states only the path condition ('A candidate that changes only .agentmarshal/switches.toml and paths inside its own task's journal subtree ... passes the gate without review'); docs/overview.md:138-144 and docs/threat-model.md open question 5 omit it too. src/agentmarshal/switch_off.py:463 writes `scope = [\".agentmarshal/switches.toml\"]`, so the command-generated task is unaffected.",
    "ADV-DOC-RECORD-TYPES-002": "docs/overview.md:110-112 lists `opened`, `finding`, `review`, `acceptance`, `amendment`, `completed`, `reopened`, `abandoned`, `session` only; src/agentmarshal/journal/records.py:138 ('check'), :147 ('agreement'), :165 ('ext') and the acknowledgement family (src/agentmarshal/acknowledge.py, records.py:239 _ACKNOWLEDGEMENT_RECORD_SCHEMA = 7) are live record types, and CHANGELOG.md:439-441 records them as shipped in 0.5.0."
  }
}
AGENTMARSHAL_VERDICT_END
