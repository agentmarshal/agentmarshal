Проверил дифф против кода, спецификаций и журнала. Ниже — по критериям, потом одно advisory-замечание.

**Как дифф закрывает критерии приёмки**

- **Критерий 1 (секция 0.6.0).** `CHANGELOG.md:11` — `## 0.6.0 — unreleased` стоит над `## 0.5.0 — 2026-10-23` (`CHANGELOG.md:276`), секция сгруппирована по сюжетам, каждый заголовок называет свои задачи, открывающий абзац говорит про неизменность record-, contract-header- и manifest-схем и ссылается на `UPGRADING.md`. Покрытие задач полное: все CR-205…CR-236, завершённые после v0.5.0, либо названы в записи, либо перечислены в закрывающей строке `CHANGELOG.md:273` (CR-205, CR-226, CR-230); CR-237 несёт только `opened`, поэтому в список не входит. Атрибуция задач верна — сверил с заголовками контрактов (например, CR-209 — trust/untrust/list, CR-211 — `stage run`, CR-208 — строка про implementer session, CR-210 — предупреждение гейта и `status --base`). Теста нет: критерий документационный.
- **Критерий 2 (что покрыто и сверено с кодом).** Проверил каждое утверждение по исходникам: строки результата стадии (`stages.py:950-962`, `failed (exit <n>)` — `stages.py:918`, `did not finish (timeout)` — `stages.py:913`), отказы без строки стадии (`stages.py:1035,1043,1098`), грант и `CI=true` (`stages.py:500-516,1124`), `record-ext` (`record_ext.py:15-34,182-211`), `doctor` (`doctor.py:400,557,575,766-790`), WARN у `validate` (`validate.py:188-191`), switches с базы и `switch off` (`stages.py:1145-1154`, `switch_off.py:463,579`), операционная линия (`gate.py:969-1017,1355,1384-1430`), изоляция — слово в слово в границах `docs/threat-model.md:447-470`, `complete` со стадиями и `--target` (`cli.py:1121-1232`), personal-расширения (`stages.py:640-690,755-782,1460-1524`), `SENT` и `skipped as sent` (`outbox.py:60-66,723`), unmeasured (`status_view.py:316`, `report.py:731,779,812` — на Cost-строке действительно `unmeasured_without_cost`), пин OpenSpec 1.15.0, `check_release_audit.py`. Теста нет: документация.
- **Критерий 3 (что не вошло).** `CHANGELOG.md:252-271` — schema 8 (ADR-0022; максимум в коде — 7, `records.py:227-300`), user-scope (ADR-0013), `next`/`plan.toml` (ADR-0023 + ADR-0022 §7; команды `next` в `cli.py` нет), watchdog/monitor (044→042), merge slot и resolution-review (043). Формулировка «while the queue model is under review» совпадает с решением оператора в `CR-204/contract.md:34-38`. Теста нет.
- **Критерий 4 (UPGRADING 0.5.0 → 0.6.0).** `UPGRADING.md:3-56`, стоит над `## 0.4.1 → 0.5.0`: отсутствие схемных изменений и порядка апгрейда, гранты на workstation, операционная линия, `complete --target` (поведение подтверждено `cli.py:1133-1147`), пропуск отправленных файлов в `outbox check`/`send`, пин продукта через манифест. Теста нет.
- **Критерий 5 (индексы и threat model).** `docs/proposals/README.md` — 020 теперь «shipped in 0.5.0» (`:218`), все проверенные мной «shipped» подтверждены кодом (`acknowledge.py`, `record_check.py`, `records.py:209` `report_ready`, `session.py:124` `cli_session`, `steps.py`, `outbox status --index` в `outbox.py:132-140,1060-1105`), а оставшиеся «not shipped» — действительно не отгружены. `docs/threat-model.md:252-268` перечисляет command-level отказы — сверено с `stages.py:1035,1043,1098` и `cli.py`/`stages.py:1564`. README называет outbox среди того, что пишет `init` (`project.py:298-331`). `docs/README.md:87-88` — строки для 044 и 045 в формате строк 041–043. Теста нет.
- **Критерий 6 (правки по findings аудита).** `docs/overview.md:138-147` — journal-only = всё под `.agentmarshal/journal/` (константа `gate.py:78`), операционная линия добавлена, «0.4.1» как текущий релиз убран. `docs/self-hosting-workflow.md:37-40,143-147` — acceptance, точно покрывающий блокирующие findings (`gate.py:1770-1771` — сравнение множеств), и отсутствие review на обеих линиях. `UPGRADING.md:153-159` — строка счётчика подтверждена `gate.py:2274`. `docs/threat-model.md:522-533` — отсылка к gate-lanes, где отказ симлинка зафиксирован (`openspec/specs/gate-lanes/spec.md:241-250`, реализация `gate.py:1044-1045`). Теста нет.
- **Критерий 7 (версия).** `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11` — `0.6.0`; демонстрируют тесты `tests/test_smoke.py::test_version_is_declared` (`:47-48`) и `tests/test_smoke.py::test_console_version_prints_package_version` (`:51-59`), который прогоняет реальный `--version` через `cli.py:129-131`.
- **Критерий 8 (границы).** Диффом затронуты только пути из scope; добавленные ссылки резолвятся (`docs/adr/ADR-0013-…`, `ADR-0015`, `ADR-0018`, `ADR-0022`, `docs/proposals/044-…`, `045-…` — файлы существуют); исторические секции CHANGELOG не тронуты, единственная правка истории — оговорённая в контракте в `UPGRADING.md`. Полную CI-последовательность я не запускал (снапшот не git-репозиторий, read-only review) — опираюсь на утверждение координатора.

**Advisory-замечание**

ADV-OVERVIEW-OPERATIONAL-SCOPE — `docs/overview.md:141-144` описывает операционную линию только через набор изменённых путей («changes only `.agentmarshal/switches.toml` and anything inside its own task's journal subtree»), но в коде линия дополнительно требует, чтобы контракт задачи объявлял `scope` ровно этот один файл (`gate.py:1006-1008`: `contract.scope != (switches_module.SWITCHES_RELPATH,)` → линия закрыта), а также чтобы switches-файл базы читался и парсился (`gate.py:1009-1016`). Кандидат с ровно такой диффой, но контрактом иного scope, на линию не попадёт и потребует review. Не блокирует: оговорка «the lane `extension switch off` opens a task onto» указывает читателю единственный поддерживаемый путь попадания на линию, а CHANGELOG (`CHANGELOG.md:100-103`) условие про `scope` называет явно.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "7b5386687d6932b75bd5340a7b8d25cd69f68012",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-OVERVIEW-OPERATIONAL-SCOPE"],
  "classes": {
    "ADV-OVERVIEW-OPERATIONAL-SCOPE": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep of version declarations in pyproject.toml, src/agentmarshal/__init__.py, uv.lock, tests/test_smoke.py", "result": "all four read 0.6.0; cli.py:129-131 passes __version__ to --version"},
      {"what": "grep of stage result strings in src/agentmarshal/stages.py", "result": "stages.py:950-962 checked/failed/did not finish/switched off/not run; :918 'exit <n>'; :913 'timeout'; :1475-1500 '(personal)' mark and 'pause accepted by <party> (<reason>)'; :1495-1500 'stage run: note: … not enforced'"},
      {"what": "read of stages.py:1030-1160 (command-level refusals, CI, switches)", "result": "unknown phase, sidecar, unreadable base manifest each return status 1 before any stage is planned; ci = os.environ.get('CI') == 'true'; unreadable switches block the named stages with 'shared switches file unreadable'"},
      {"what": "read of gate.py:969-1017 and 1340-1440 (operational lane)", "result": "lane requires switches.toml plus only the task's own subtree AND contract.scope == ('.agentmarshal/switches.toml',); verdict line 'PASS: operational transaction (operational lane; review not required)' at :1355; a link at the file refuses as 'not a file' (:1044-1045)"},
      {"what": "grep of _JOURNAL_PREFIX in src/agentmarshal/journal/gate.py", "result": "gate.py:78 _JOURNAL_PREFIX = '.agentmarshal/journal/' — overview's journal-only definition matches"},
      {"what": "read of gate.py:2056-2165 (other-task projection and CR-210 warning)", "result": "merged projection per affected task with the same closed-at-base admission; FAIL names task and reason; 'WARN: candidate adds opened/amendment records of other tasks'"},
      {"what": "read of records.py:598-636, 1410-1428, 1585-1600, 2092-2125", "result": "timestamp-text and artifact-ref-text rules bound to schema 8 (write-time only); write_record encodes before creating the file"},
      {"what": "read of review.py:599-616, 1273-1292", "result": "raw reviewer bytes preserved on a refused verdict; parsing uses the decoded text"},
      {"what": "grep/read of outbox.py (SENT manifest, --index on check/send/status)", "result": "outbox.py:60-66 SENT and its line format; :117-140 --index on check, send, status; :723 'skipped as sent: <n>'; :1060-1105 Source: digest matching"},
      {"what": "read of cli.py:1100-1232 (complete)", "result": "pre-gate stages run before the gate; status 3 refuses unless --target shows the candidate merged; post-gate run after the completed record, its status informing nothing"},
      {"what": "read of project.py:232-331", "result": "init scaffolds .agentmarshal/upstream/README.md — README's new claim holds"},
      {"what": "ls and grep over .agentmarshal/journal/tasks (CR-200..CR-237 lifecycle records and titles)", "result": "CR-205..CR-236 all carry completed records, CR-234 only opened, CR-237 only opened; CR-200..CR-203 completed before CR-204 (0.5.0), so '0.5.0's CR-200 through CR-203' is correct"},
      {"what": "grep of .agentmarshal/extensions/openspec.toml and .github/scripts/check_release_audit.py", "result": "schema = 1, version = '1.15.0'; the script checks the model allowlist, ancestry, dispositions and the paths changed since the audit"},
      {"what": "existence check of every link added (ADR-0013/0015/0018/0022, proposals 044 and 045)", "result": "all targets exist"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section and the 0.5.0 section it sits above)",
      "UPGRADING.md",
      "README.md",
      "docs/overview.md",
      "docs/threat-model.md",
      "docs/proposals/README.md",
      "docs/README.md",
      "docs/self-hosting-workflow.md",
      "CONTRIBUTING.md (Versions and Releases)",
      "AGENTS.md",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/record_ext.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/project.py",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/review.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/validate.py",
      "src/agentmarshal/journal/extensions.py",
      "templates/journal-transaction.sh",
      "tests/test_smoke.py",
      "tests/test_gate.py (released_030)",
      "openspec/specs/gate-lanes/spec.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/adr/ADR-0023-next-the-next-step-of-a-task.md",
      ".agentmarshal/journal/tasks/CR-204/contract.md",
      ".agentmarshal/journal/tasks/CR-234/contract.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review of a snapshot that is not a git repository and has no synced environment; the coordinator attests the full sequence passed on the reviewed commit, and the diff is documentation plus a version string"},
      {"what": "an end-to-end run of stage run / complete / gate against a live repository", "why": "no git repository in the snapshot; the behaviour claims were checked against the implementing code and the openspec requirements instead"}
    ]
  },
  "evidence": {
    "ADV-OVERVIEW-OPERATIONAL-SCOPE": "docs/overview.md:141-144 states the operational lane admits a candidate that changes only .agentmarshal/switches.toml and its own task's journal subtree; src/agentmarshal/journal/gate.py:1006-1008 additionally requires contract.scope == ('.agentmarshal/switches.toml',) and :1009-1016 requires the base's switches file to read and parse, otherwise operational_candidate returns None and the candidate takes the review-bound lane. CHANGELOG.md:100-103 states the scope condition explicitly."
  }
}
AGENTMARSHAL_VERDICT_END
