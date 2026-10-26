Проверил diff против кода на `12c59c49b836f280217d2d32ea73278225f35b96`. Ниже — прозa по каждому finding и по каждому acceptance criterion.

## Findings

**DOC-MIGRATE-COMMAND-NAME** (blocking, claim-accuracy) — `docs/harness-setup.md:80` и `_comment` в `docs/templates/claude-code-settings.local.json:3` перечисляют среди journal writers команду `migrate`, которой в CLI нет: парсер регистрирует `migrate-journal` (`src/agentmarshal/cli.py:502`, диспетчер — `src/agentmarshal/cli.py:1898`), и `grep -rn '"migrate"' src/` не даёт ни одного алиаса. Все остальные имена в этом перечислении — точные имена subcommand'ов (`submit-review`, `record-*`, `prune --delete`), так что `migrate` читается как имя команды, а оператор, который построит по этому списку свой allowlist или решит, что `Bash(agentmarshal migrate)` что-то покрывает, получит промах. Это ровно тот класс ошибки, который AC6 требует исключить («every statement is checked against the code at master»), и он внесён самим этим diff'ом в двух файлах.

**DOC-TEMPLATE-READONLY-LIST** (advisory, claim-accuracy) — `docs/harness-setup.md:84-87` велит разрешать read-only subcommand'ы по одному — `status`, `brief`, `validate`, `report`, `doctor`, `gate`, `leak-scan` — «as the shipped template does», но шаблон разрешает ещё и `Bash(agentmarshal prune)` (`docs/templates/claude-code-settings.local.json:25`), которого в прозе нет. Сам `prune` без `--delete` действительно read-only (`src/agentmarshal/cli.py:491-501`), так что шаблон корректен — расходится с ним перечисление, на которое он сослан.

**DOC-CONTRIBUTING-BASE-ONLY** (advisory, scope) — `CONTRIBUTING.md:85` по-прежнему утверждает, что «the contract and prior task state are read from the base side, so a change cannot widen its own scope», без исключения для operational lane, которое diff добавил во все пять мест под `docs/`. Файл лежит вне scope контракта (`docs/`), поэтому править его здесь было бы нарушением границ — отмечаю как departure для отдельной задачи, а не как дефект этого diff'а.

## Acceptance criteria

- **AC1 (thirteen record types)** — выполнен: `docs/known-defects.md:13` говорит «thirteen», и `RECORD_TYPES` в `src/agentmarshal/journal/attestation.py:62-114` содержит ровно 13 записей (opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext). Демонстрирует `tests/test_attestation.py::test_the_three_modules_read_the_one_registry`, который пинит реестр точным dict'ом из тринадцати ключей.
- **AC2 (user scope)** — выполнен: `docs/harness-setup.md:35-50` переносит trust/switches/extension code под `.git/agentmarshal/` и прямо говорит, что user-scope каталоги решены, но не реализованы. Код подтверждает: `src/agentmarshal/localstate.py:38-73` даёт `log`, `extensions`, `deps`, `trust.toml`, `switches.toml`, `plan.toml` под git common dir, а `grep` по `XDG|.config/agentmarshal|APPDATA|Path.home` в `src/` не находит ни одного чтения user-scope. Утверждение про `plan.toml` («nothing in 0.6.0 reads or writes one») подтверждает `tests/test_localstate.py:115`, где файл только именуется, и CHANGELOG «What 0.6.0 leaves out» (строка 269-272).
- **AC3 (исключение operational lane)** — выполнен: исключение названо в `docs/threat-model.md:23-31`, `docs/overview.md:76-80` и `:135-137`, `docs/quickstart.md:323-327`, `docs/self-hosting-workflow.md:160-165`, `docs/sidecar.md:51-54`. Код совпадает дословно: `_operational_contract` читает contract из candidate'а только когда его нет в merge-base (`src/agentmarshal/journal/gate.py:1023-1027`), `operational_candidate` требует diff = switches-файл плюс подкаталог своей задачи и `scope == (".agentmarshal/switches.toml",)` (`:1083-1093`), а в sidecar lane не предлагается (`:1387-1393`). Демонстрируют `tests/test_gate_operational.py::test_a_task_opened_within_the_candidate_reads_the_candidate_contract`, `::test_the_contract_is_read_from_the_base_when_the_task_exists_there`, `::test_a_contract_declaring_another_scope_does_not_take_the_lane` и `::test_in_a_sidecar_the_operational_lane_is_not_offered`. Остальные места с «from the base side» в `docs/` — это `docs/adr/*` (датированные решения, AC6 их не переписывает) и `docs/proposals/*` (non-goal, CR-243).
- **AC4 (write-time и outbox)** — выполнен: `docs/threat-model.md:128-138` перечисляет четыре timestamp'а и `artifacts` `ref`, что соответствует правилам `timestamp-text` и `artifact-ref-text` (`src/agentmarshal/journal/records.py:618-637` и `:1410-1428`), привязанным к schema 8 при максимуме 7 (`:1598-1600`). Демонстрируют `tests/test_record_text_safety.py::test_a_timestamp_carrying_a_refused_character_is_refused` и `::test_an_artifact_ref_carrying_a_refused_character_is_refused_at_write`. Outbox-абзац (`:186-199`) совпадает с `src/agentmarshal/outbox.py:176-194` (lstat по `.agentmarshal` и `upstream` до любой записи, во всех четырёх subcommand'ах через `_locate`), `:832-851` (`_pinned_blob`: staged-байты против проверенных) и `:1154-1170` (`_batch_mismatch` плюс откат индекса) — демонстрируют `tests/test_outbox.py::test_a_linked_outbox_refuses_a_command_before_it_writes`, `::test_a_linked_agentmarshal_component_refuses_the_command`, `::test_a_sidecars_linked_outbox_never_writes_the_host`, `::test_check_refuses_a_draft_a_clean_filter_would_transform`, `::test_send_refuses_a_draft_a_clean_filter_would_transform`. Все четыре цитаты из outbox-спеки существуют дословно (`openspec/specs/outbox/spec.md:91,181,502,532`), как и `gate-lanes` requirement (`openspec/specs/gate-lanes/spec.md:170`). Sidecar-абзац (`:319-332`) цитирует строки, которые тул действительно печатает: `src/agentmarshal/journal/placement.py:45`, `src/agentmarshal/cli.py:993,1005,1206,950,1204`.
- **AC5 (версии, транскрипты, closing line, operator tooling)** — выполнен: `docs/quickstart.md` и `docs/sidecar.md` переведены на 0.6.0, что совпадает с `pyproject.toml:3` и `tests/test_smoke.py:48`; «acts on `reviews` alone» остаётся верным — единственный потребитель capture-политики это `review_capture_level_from_journal` (`src/agentmarshal/journal/review.py:36`), а «no private store yet» подтверждает Consequences ADR-0014. Новые три stderr-строки в транскрипте `status` печатает `print_paths` сразу после `evidence_line` (`src/agentmarshal/cli.py:1460-1474`, `src/agentmarshal/journal/status_view.py:852-861`), и только `status` — демонстрирует `tests/test_status_steps.py:133`. Заметка про `doctor` верна: он вызывает `resolve_placement` без `require_host` (`src/agentmarshal/doctor.py:883`), так что host только резолвится в путь, а проверки existence / git worktree живут под `require_host` (`src/agentmarshal/journal/placement.py:86-96`). `docs/github-enforcement.md:95-96` цитирует закрывающую строку посимвольно — `src/agentmarshal/cli.py:1007`, демонстрирует `tests/test_gate.py:973`; шаблон CI действительно зовёт `gate --without-review` (`templates/github/agentmarshal-governance.yml:78`). `am-merge`, `mr.sh`, `merge-policy.sh`, `task-lifecycle.sh` и agmake больше нигде в `docs/self-hosting-workflow.md` и `docs/templates/` не описаны как файлы этого репозитория; единственный shell-скрипт в репозитории — `templates/journal-transaction.sh`, так что фраза «the one script this repository ships» точна. «The governed loop» прогоняется дословно в `tests/test_quickstart.py`.
- **AC6 (проверка по коду, ссылки, границы, CI)** — выполнен частично: все 12 относительных ссылок и anchor `#research-findings-loop` в изменённых файлах разрешаются, датированные исторические заметки не переписаны, ни один файл вне `docs/` не изменён. Не выполнен в части «every statement is checked against the code» — см. **DOC-MIGRATE-COMMAND-NAME**. Полную последовательность CI я не запускал (read-only review, запуск команд в этой сессии не разрешён); опираюсь на утверждение координатора о её прохождении на этом коммите и ни одного падения инструмента не заявляю.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "12c59c49b836f280217d2d32ea73278225f35b96",
  "verdict": "changes_required",
  "findings": ["DOC-MIGRATE-COMMAND-NAME"],
  "advisory_findings": ["DOC-TEMPLATE-READONLY-LIST", "DOC-CONTRIBUTING-BASE-ONLY"],
  "classes": {
    "DOC-MIGRATE-COMMAND-NAME": "claim-accuracy",
    "DOC-TEMPLATE-READONLY-LIST": "claim-accuracy",
    "DOC-CONTRIBUTING-BASE-ONLY": "scope"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn RECORD_TYPES src/ and read src/agentmarshal/journal/attestation.py:62-114", "result": "thirteen record types registered: opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext"},
      {"what": "grep -rn 'XDG|\\.config/agentmarshal|\\.local/share|APPDATA|Path.home' src/", "result": "no hit; only project.py:440 and placement.py:53 expanduser for the sidecar host"},
      {"what": "grep -rn 'plan_file|plan.toml' src/ tests/", "result": "defined in localstate.py:70-73, asserted in tests/test_localstate.py:115 only; no reader or writer"},
      {"what": "read src/agentmarshal/journal/gate.py:1006-1104 and 1375-1393", "result": "_operational_contract falls back to the candidate tree only when the base has no contract.md; the lane requires scope == ('.agentmarshal/switches.toml',) and is skipped when sidecar or journal_only"},
      {"what": "read src/agentmarshal/journal/records.py:618-637, 1410-1428, 1590-1600", "result": "timestamp-text covers created_at/started_at/ended_at/resets_at, artifact-ref-text covers artifacts ref; both bound to schema 8 while the max record schema is 7"},
      {"what": "read src/agentmarshal/outbox.py:152-194, 832-851, 1020-1046, 1150-1170", "result": "all four subcommands go through _locate, which lstats .agentmarshal and .agentmarshal/upstream before any write; _pinned_blob compares filtered and unfiltered hash-object; _batch_mismatch plus _restore_outbox_index"},
      {"what": "grep for each quoted sidecar/gate line in src/", "result": "placement.py:45, cli.py:950, 993, 1005, 1007, 1204, 1206 all match the quoted text exactly"},
      {"what": "grep -n '^### Requirement' openspec/specs/outbox/spec.md; grep -rn 'an operational change takes its own gate lane' openspec/", "result": "all four quoted outbox headings and the gate-lanes heading exist verbatim"},
      {"what": "grep -rn -A2 'add_parser(' src/agentmarshal/ for subcommand names; grep -rn '\"migrate\"' src/", "result": "the command is registered as 'migrate-journal' (cli.py:502, dispatch cli.py:1898); no 'migrate' alias exists"},
      {"what": "resolve every relative markdown link and anchor in the eight changed docs", "result": "all targets exist (docs/adr/*, docs/*.md, ../UPGRADING.md); #research-findings-loop matches docs/sidecar.md:424"},
      {"what": "find . -name '*.sh' -not -path './.git/*'", "result": "only templates/journal-transaction.sh"},
      {"what": "grep -rn 'never from the candidate|from the base side|widen its own scope' docs/ README.md CONTRIBUTING.md", "result": "every non-ADR, non-proposal place under docs/ now carries the exception; CONTRIBUTING.md:85 does not (outside the contract's scope)"}
    ],
    "read": [
      "docs/harness-setup.md",
      "docs/sidecar.md",
      "docs/threat-model.md (lines 20-50, 119-210, 236-335)",
      "docs/quickstart.md (changed hunks)",
      "docs/self-hosting-workflow.md",
      "docs/overview.md (lines 70-140)",
      "docs/github-enforcement.md (changed hunks)",
      "docs/known-defects.md (lines 1-20)",
      "docs/templates/claude-code-settings.local.json",
      "docs/adr/ADR-0014-where-things-live.md (decisions 12 and 13)",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/attestation.py",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/journal/review.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/steps.py",
      "CHANGELOG.md (0.6.0 section)",
      "CONTRIBUTING.md",
      "templates/github/agentmarshal-governance.yml",
      "tests/test_attestation.py",
      "tests/test_quickstart.py",
      "tests/test_gate_operational.py (test names)",
      "tests/test_outbox.py (test names)",
      "tests/test_record_text_safety.py (test names)",
      "tests/test_status_steps.py (path assertions)",
      "openspec/specs/outbox/spec.md (requirement headings)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "read-only review in a non-interactive session; command execution beyond read-only inspection was not permitted, so the coordinator's statement that the sequence passed on this commit stands unchallenged and no tool failure is claimed"}
    ]
  },
  "evidence": {
    "DOC-MIGRATE-COMMAND-NAME": "docs/harness-setup.md:80 and docs/templates/claude-code-settings.local.json:3 name `migrate`; `grep -n 'add_parser' src/agentmarshal/cli.py` -> 502: subparsers.add_parser(\"migrate-journal\", help=\"convert a v1 journal into a new v2 journal\"); `grep -n 'args.command ==' src/agentmarshal/cli.py | grep migrate` -> 1898: if args.command == \"migrate-journal\"; `grep -rn '\"migrate\"' src/` -> no output (no alias)",
    "DOC-TEMPLATE-READONLY-LIST": "docs/harness-setup.md:84-87 lists seven read-only subcommands and says \"as the shipped template does\"; docs/templates/claude-code-settings.local.json:25 also allowlists \"Bash(agentmarshal prune)\", which is read-only per src/agentmarshal/cli.py:491-501 (--delete is the writing form) but is absent from the prose list",
    "DOC-CONTRIBUTING-BASE-ONLY": "CONTRIBUTING.md:85 — \"read from the base side, so a change cannot widen its own scope\" with no operational-lane exception, while gate.py:1023-1027 reads the opening contract from the candidate; the file is outside the contract's scope [\"docs/\"], so this is a follow-up departure, not a defect of this diff"
  }
}
AGENTMARSHAL_VERDICT_END
