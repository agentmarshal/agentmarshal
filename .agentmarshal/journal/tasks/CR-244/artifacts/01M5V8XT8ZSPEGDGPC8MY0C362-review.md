Проверил diff против кода на `12c59c49b836f280217d2d32ea73278225f35b96`. Ниже — по одной строке прозы на каждый finding, затем разбор acceptance criteria.

**DOC-SIDECAR-REPORT-STALE** (blocking) — транскрипт `agentmarshal report --task CR-001` в `docs/sidecar.md:338-344` не совпадает с тем, что печатает 0.6.0: для отчёта по одной задаче `cli.py:1393-1396` вызывает `format_report(..., include_summary=task_id is None)`, то есть `include_summary=False`, а эта ветка в `report.py:1007-1020` после строк `Phases`/`Durations`/`Round` добавляет ещё `_cost_lines` и `_check_lines`. В примере из гайда записан один измеренный `record-session` (1200+300 токенов, `usage-method reported`) без `cost`, значит `_cost_sums` даёт `sessions=1, sessions_without_cost=1` (`report.py:407-423`) и вывод заканчивается тремя строками, которых в транскрипте нет: `Cost<TAB>sessions_without_cost=1`, `Checks<TAB>rejected_commits=0` и `A check record is the observer's declaration of what the pipeline found on the commit, not proof of it.` Ровно это закреплено тестами `tests/test_report_cost_checks_findings.py:261-266` и `:494-495` — оба гоняют именно `report --task CR-001`. Это прямое невыполнение критерия «sidecar's transcripts match what 0.6.0 prints».

**DOC-HARNESS-MIGRATE-NAME** (advisory) — `docs/harness-setup.md:80` и `_comment` в `docs/templates/claude-code-settings.local.json` называют write-команду `migrate`, но в CLI такой подкоманды нет: парсер регистрирует `migrate-journal` (`src/agentmarshal/cli.py:502`), и dispatch сравнивает с `"migrate-journal"` (`cli.py:1898`). Правило `Bash(agentmarshal migrate *)`, собранное по этому списку, не покрыло бы ничего.

**DOC-HARNESS-READONLY-LIST** (advisory) — `docs/harness-setup.md:84-87` перечисляет read-only подкоманды «`status`, `brief`, `validate`, `report`, `doctor`, `gate`, `leak-scan` — as the shipped template does», но шаблон разрешает ещё одну: `"Bash(agentmarshal prune)"` (`docs/templates/claude-code-settings.local.json:22`). Перечисление и «как в шаблоне» расходятся на один элемент.

**DOC-CONTRIBUTING-RESIDUAL** (advisory) — `CONTRIBUTING.md:83-84` сохраняет безоговорочное «the contract and prior task state are read from the base side, so a change cannot widen its own scope», то есть ровно то утверждение, которое критерий 3 требует дополнить исключением. Путь вне scope контракта (`docs/`), поэтому правильно не тронут, — но его следует назвать departure/follow-up, а не оставить молча.

**DOC-V1-SUBMODULE-NUANCE** (advisory, unconfirmed) — формулировка «operator tooling outside this repository, not files it ships» про `am-merge`/`mr.sh`/`merge-policy.sh` верна в том смысле, что это отдельный репозиторий, но репозиторий объявляет его submodule'ом: `.gitmodules` указывает `path = agentmarshal`, `url = …/agentmarshal-v1.git`, а `pyproject.toml` исключает `./agentmarshal` как «v1 archive submodule at repo root» — и прежние строки шаблона были как раз `Bash(./agentmarshal/scripts/*)` и `Bash(./agentmarshal/bin/*)`. В снапшоте каталог `agentmarshal/` пуст, содержимое submodule проверить не могу, поэтому не подтверждено; стоит одной оговоркой сказать, что при рекурсивном checkout эти скрипты всё же появляются в дереве клона.

Теперь по критериям — где diff их выполняет и чем это демонстрируется:

- **AC1 (thirteen record types)** — выполнен: `docs/known-defects.md:13` теперь говорит «thirteen», и реестр `RECORD_TYPES` в `src/agentmarshal/journal/attestation.py:62-115` содержит ровно 13 записей (opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext). Демонстрирует `tests/test_attestation.py:82` `test_the_three_modules_read_the_one_registry`, который прибивает все 13 predicate-URI литералами.
- **AC2 (user scope)** — выполнен: `docs/harness-setup.md:35-50` переносит trust/switches/extensions в `.git/agentmarshal/` и объявляет user-scope каталоги «decided but not implemented». Код совпадает: `src/agentmarshal/localstate.py:39-73` даёт `log`, `extensions`, `deps`, `trust.toml`, `switches.toml`, `plan.toml`; grep по `src/` не находит ни `~/.config`, ни `XDG_CONFIG`, ни `APPDATA`; `plan_file` нигде не читается и не пишется. Источники сверены: `docs/adr/ADR-0014-where-things-live.md:167` и `CHANGELOG.md:265-272`. Демонстрирует `tests/test_localstate.py` (в частности `:115` на `plan_file`).
- **AC3 (источник контракта на operational lane)** — выполнен, и покрыты все места: `threat-model.md:23-31`, `overview.md:75-82` и `:132-137`, `quickstart.md:323-328`, `self-hosting-workflow.md:160-165`, `sidecar.md:50-54`; единственное оставшееся «never from the candidate» в `threat-model.md:252` относится к манифестам и коду extensions, не к контракту. Код: `gate.py:1006-1034` читает контракт с candidate только когда его нет в merge-base, `gate.py:1082-1102` ограничивает diff `.agentmarshal/switches.toml` плюс поддеревом задачи и требует `scope == (".agentmarshal/switches.toml",)`, `gate.py:1387-1393` не предлагает lane в sidecar. Демонстрируют `tests/test_gate_operational.py:119` (`test_a_task_opened_within_the_candidate_reads_the_candidate_contract`), `:94`, `:164` и `:205`.
- **AC4 (write-time и outbox в threat-model)** — выполнен: `threat-model.md:128-135` называет четыре timestamp-поля и `artifacts.ref`, и оба правила действительно привязаны к схеме 8, то есть за пределами сегодняшних (`records.py:1594-1599`, реализация — `:618-636` и `:1410-1428`). Outbox-абзац `:186-200` совпадает с `outbox.py:174-195` (lstat на `.agentmarshal` и `upstream` до любой записи, `_locate` вызывают все четыре подкоманды — `:368, 551, 1078, 1229`), `:700-710`/`:837-851` (отказ на файле, который git преобразует) и `:1154-1181` (`_batch_mismatch` плюс возврат индекса). Цитаты в sidecar-абзаце `:319-332` дословны: `placement.py:45`, `cli.py:993`, `:1005`, `:950`, `:1204`, `:1206`, `placement.py:37`. Демонстрируют `tests/test_record_text_safety.py:321` и `:400`; `tests/test_outbox.py:1923`, `:1959`, `:2018`, `:2046`, `:2114`, `:2256`, `:761`; `tests/test_placement.py:394`.
- **AC5** — выполнен частично. Пины 0.6.0 стоят (`quickstart.md:6, 26, 250, 259, 459`; `sidecar.md:77, 127`) и совпадают с `pyproject.toml` `version = "0.6.0"`. Закрывающая строка gate в `github-enforcement.md:95-96` дословна относительно `cli.py:1007`, а `--without-review` в CI подтверждается `templates/github/agentmarshal-governance.yml:78`. Транскрипт gate в sidecar (`sidecar.md:225-238`) совпадает строка-в-строку с фикстурой `tests/fixtures/gate/sidecar-implementation.stdout`. Новые строки `status` (`sidecar.md:317-320`, `:357-359`, `:417`) совпадают с `status_view.py:852-861` и порядком вывода в `cli.py:1460-1474`. Заметка про `doctor` (`sidecar.md:475-478`) верна: `doctor.py:884` зовёт `resolve_placement` без `require_host`, а проверки существования/git-worktree живут только под `require_host` (`placement.py:86-97`). Упоминания `am-merge`/`mr.sh`/`scripts` переквалифицированы везде, `docs/templates/` содержит один файл без ссылок на скрипты, и в `templates/` действительно только `journal-transaction.sh`. Не выполнена часть «sidecar's transcripts match what 0.6.0 prints» — см. DOC-SIDECAR-REPORT-STALE.
- **AC6** — выполнен, кроме сверки одного транскрипта: все 11 относительных ссылок в восьми затронутых файлах разрешаются (включая anchor `#research-findings-loop` → `sidecar.md:424`); датированные исторические заметки не переписаны (`overview.md:93`, `quickstart.md:503, 536, 588, 591`, `sidecar.md:3`, `threat-model.md:440`); diff не выходит за `docs/`. Полную CI-последовательность я не прогонял — беру факт координатора; ни один тест не читает содержимое `docs/`, так что прозаические правки на неё не влияют.

Вердикт: `changes_required` — один блокирующий finding, остальные четыре советательные.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "12c59c49b836f280217d2d32ea73278225f35b96",
  "verdict": "changes_required",
  "findings": ["DOC-SIDECAR-REPORT-STALE"],
  "advisory_findings": [
    "DOC-HARNESS-MIGRATE-NAME",
    "DOC-HARNESS-READONLY-LIST",
    "DOC-CONTRIBUTING-RESIDUAL",
    "DOC-V1-SUBMODULE-NUANCE"
  ],
  "classes": {
    "DOC-SIDECAR-REPORT-STALE": "claim-accuracy",
    "DOC-HARNESS-MIGRATE-NAME": "claim-accuracy",
    "DOC-HARNESS-READONLY-LIST": "claim-accuracy",
    "DOC-CONTRIBUTING-RESIDUAL": "scope",
    "DOC-V1-SUBMODULE-NUANCE": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "count the entries of RECORD_TYPES in src/agentmarshal/journal/attestation.py:62-115", "result": "13 entries: opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext"},
      {"what": "grep -rn for the user-scope paths in src/ (.config/agentmarshal, XDG_CONFIG, APPDATA, LOCALAPPDATA, local/share)", "result": "no match; nothing in the tool reads or writes them"},
      {"what": "grep -rn 'plan_file|plan.toml' src/ tests/", "result": "only localstate.py:70-73 declares it and tests/test_localstate.py:115 pins the path; no reader or writer"},
      {"what": "grep -n 'add_parser(' over src/agentmarshal/cli.py and the registering modules", "result": "top-level commands include 'migrate-journal'; no 'migrate' subcommand exists"},
      {"what": "grep -rn 'am-merge|mr.sh|merge-policy.sh|task-lifecycle.sh|agmake|scripts/' docs/ (excluding adr/, incidents/, proposals/)", "result": "every remaining mention is qualified as operator tooling or as a host wrapper example (overview.md:157, github-enforcement.md:113)"},
      {"what": "find . -name '*.sh' and find templates -type f", "result": "templates/journal-transaction.sh is the only shell script; templates/ holds it plus github/agentmarshal-governance.yml"},
      {"what": "grep -rn the sidecar output strings in src/", "result": "placement.py:45, cli.py:950, 993, 1005, 1204, 1206 and placement.py:37 match the threat-model quotes verbatim"},
      {"what": "grep -n 'passed what it examined' docs/github-enforcement.md src/agentmarshal/cli.py", "result": "doc line 95-96 matches cli.py:1007 exactly"},
      {"what": "grep -n '^### Requirement' openspec/specs/gate-lanes/spec.md openspec/specs/outbox/spec.md", "result": "all four newly cited requirement names exist (gate-lanes:170; outbox:181, 502, 532)"},
      {"what": "resolve every relative markdown link target in the eight touched docs files with ls", "result": "all resolve, including the #research-findings-loop anchor at sidecar.md:424"},
      {"what": "compare docs/sidecar.md:225-238 with tests/fixtures/gate/sidecar-implementation.stdout", "result": "identical line for line (SHAs aside)"},
      {"what": "trace report --task through cli.py:1393-1396 and report.py:1007-1020, 961-972", "result": "include_summary=False appends _cost_lines and _check_lines; with one costless measured session that is Cost sessions_without_cost=1, Checks rejected_commits=0 and the check declaration"}
    ],
    "read": [
      "docs/harness-setup.md",
      "docs/sidecar.md",
      "docs/threat-model.md (lines 20-45, 120-210, 236-280, 310-335)",
      "docs/quickstart.md (lines 240-340, 450-640)",
      "docs/self-hosting-workflow.md",
      "docs/github-enforcement.md",
      "docs/overview.md (lines 70-160)",
      "docs/known-defects.md",
      "docs/templates/claude-code-settings.local.json",
      "docs/adr/ADR-0014-where-things-live.md (section 12)",
      "CHANGELOG.md ('What 0.6.0 leaves out')",
      "CONTRIBUTING.md (lines 78-92)",
      "src/agentmarshal/journal/attestation.py",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/gate.py (1000-1120, 1375-1500, 1660-1800, 2150-2210)",
      "src/agentmarshal/journal/records.py (580-640, 1410-1430, 1560-1610)",
      "src/agentmarshal/journal/report.py (375-434, 660-760, 900-1060)",
      "src/agentmarshal/journal/status_view.py (283-320, 753-862)",
      "src/agentmarshal/outbox.py (100-200, 1078-1190)",
      "src/agentmarshal/doctor.py (860-905)",
      "src/agentmarshal/cli.py (240-540, 900-1010, 1065-1210, 1380-1500, 1870-1915)",
      "src/agentmarshal/switches.py (SWITCHES_RELPATH)",
      "tests/test_attestation.py, tests/test_gate_operational.py, tests/test_report_cost_checks_findings.py, tests/test_outbox.py, tests/test_record_text_safety.py, tests/test_localstate.py (test name listings and cited cases)",
      "tests/fixtures/gate/sidecar-implementation.stdout",
      "pyproject.toml, .gitmodules"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review in a non-git snapshot without the environment; the coordinator states the sequence passed at this commit, and no test reads docs/ content"},
      {"what": "reading the v1 submodule at agentmarshal/", "why": "the directory is empty in the snapshot, so the contents of agentmarshal-v1 could not be checked (DOC-V1-SUBMODULE-NUANCE stays unconfirmed)"}
    ]
  },
  "evidence": {
    "DOC-SIDECAR-REPORT-STALE": "docs/sidecar.md:338-344 ends at 'Round\\t1\\tverdict=approved\\tsince=unknown'; src/agentmarshal/cli.py:1393-1396 passes include_summary=task_id is None, so --task takes include_summary=False; src/agentmarshal/journal/report.py:1007-1020 extends that branch with _cost_lines and _check_lines; report.py:961-963 prints 'Cost\\tsessions_without_cost=<n>' whenever sums.sessions is non-zero and report.py:972 prints 'Checks\\trejected_commits=<n>' plus _CHECK_DECLARATION (report.py:63-66); report.py:407-423 counts the example's measured, costless session as sessions=1, sessions_without_cost=1; tests/test_report_cost_checks_findings.py:261-266 asserts 'Cost\\tsessions_without_cost=1' in the output of main(['report','--task','CR-001']) and :494-495 asserts the declaration prints once for the same invocation",
    "DOC-HARNESS-MIGRATE-NAME": "docs/harness-setup.md:80 lists 'migrate'; docs/templates/claude-code-settings.local.json:4 repeats it in _comment; src/agentmarshal/cli.py:502 registers subparsers.add_parser('migrate-journal', ...) and cli.py:1898 dispatches on args.command == 'migrate-journal'; grep of every add_parser name in src/ returns no 'migrate'",
    "DOC-HARNESS-READONLY-LIST": "docs/harness-setup.md:84-87 enumerates status, brief, validate, report, doctor, gate, leak-scan 'as the shipped template does'; docs/templates/claude-code-settings.local.json:16-25 also allowlists \"Bash(agentmarshal prune)\" (exact form, so prune --delete stays excluded)",
    "DOC-CONTRIBUTING-RESIDUAL": "CONTRIBUTING.md:83-84: 'Evidence records are append-only; the contract and prior task state are read from the base side, so a change cannot widen its own scope.' — unqualified, while the contract's scope is ['docs/'] only, so the path may not be changed and must be reported as a departure",
    "DOC-V1-SUBMODULE-NUANCE": "docs/self-hosting-workflow.md:95-101 and :133-142 say the v1 scripts are 'operator tooling outside this repository, not files it ships'; .gitmodules declares [submodule \"agentmarshal\"] path = agentmarshal, url = https://github.com/AgentMarshal/agentmarshal-v1.git and pyproject.toml extend-exclude = [\"./agentmarshal\"]  # v1 archive submodule at repo root; the removed template entries were Bash(./agentmarshal/scripts/*) and Bash(./agentmarshal/bin/*); the submodule directory is empty in this snapshot, so its contents are unconfirmed"
  }
}
AGENTMARSHAL_VERDICT_END
