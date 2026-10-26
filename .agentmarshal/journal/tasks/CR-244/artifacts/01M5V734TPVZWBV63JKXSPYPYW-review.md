Проверил диф на коммите `8e5e62120c62c6ab683be13f000a71660f2f5b76` против контракта CR-244. Ниже сначала то, что сломано, потом — по каждому критерию.

## Блокирующие

**`F-base-only-exception-unstated`** — критерий 3 требует добавить исключение operational-линии **везде**, где docs/ утверждает, что контракт читается только с базы («and any other place»). Два места в руководствах остались без оговорки: `docs/overview.md:75-77` («reads the contract … at the base from the **base** side, never from the candidate, so a change can never widen its own scope») и `docs/quickstart.md:323-324` («The gate always reads the contract from the committed base, never from the candidate, so a task can never widen its own scope»). Особенно заметно в `overview.md`: диф правит именно этот файл строкой 133 («the one exception being an operational lane's opening contract»), но более сильное утверждение абзацем выше в том же файле оставляет нетронутым — читатель получает два противоречащих заявления. Код действительно читает контракт с кандидата: `src/agentmarshal/journal/gate.py:1006-1034` (`_operational_contract` переключает `tree_ref` на `resolved_commit`, когда у базы нет `contract.md`), тест — `tests/test_gate_operational.py:119` `test_a_task_opened_within_the_candidate_reads_the_candidate_contract`. ADR'ы (ADR-0006, ADR-0009, ADR-0010, ADR-0011, ADR-0014) я сюда не записываю: это датированные решения, их критерий 6 править запрещает.

**`F-sidecar-status-transcript-stale`** — критерий 5 требует, чтобы транскрипты `docs/sidecar.md` совпадали с тем, что печатает 0.6.0. Транскрипт `agentmarshal status CR-001` в `docs/sidecar.md:316-328` показывает `Placement: sidecar`, а сразу за ним `ID: CR-001`. В 0.6.0 `_run_status` печатает в stderr строку placement (`src/agentmarshal/cli.py:1459`) и **сразу после неё** через `print_paths` ещё три строки — `journal:`, `process log:`, `local state:` (`src/agentmarshal/cli.py:1474`, `src/agentmarshal/journal/status_view.py:852-861`). Транскрипт их не содержит, и слова `journal:` / `process log:` / `local state:` во всём `docs/sidecar.md` не встречаются ни разу; таблица на `docs/sidecar.md:412` тоже утверждает только «Print `Placement: sidecar` on stderr; stdout unchanged». Это ровно тот класс устаревшего вывода, который `docs/quickstart.md:588` уже описывает как появившийся в 0.5.0. Либо транскрипт захватывает stderr — тогда не хватает трёх строк, либо не захватывает — тогда в нём лишняя строка `Placement:`.

## Advisory

**`A-plan-file-not-shipped`** — `docs/harness-setup.md:38-41` перечисляет среди содержимого `.git/agentmarshal/` «the plan file». В 0.6.0 его никто не пишет и не читает: `plan_file` — единственное упоминание `plan.toml` в коде (`src/agentmarshal/localstate.py:70-73`, больше ни одного вхождения в `src/`), CHANGELOG в «What 0.6.0 leaves out» прямо говорит «there is no `agentmarshal next` and nothing reads `plan.toml`», а раскладка в `docs/adr/ADR-0014-where-things-live.md:158-164` его не содержит. Это тот же дефект, который критерий 2 исправляет для user-scope, только в соседнем предложении.

**`A-template-allows-journal-writes`** — `docs/templates/claude-code-settings.local.json:16` заменяет два несуществующих пути на `"Bash(agentmarshal *)"`. Шаблон предназначен для implementer-харнесса (`docs/harness-setup.md:62-66`), а правила 3 и 4 того же руководства гласят «Never let the agent write the journal» и «Give the implementer no write access to the local state». Семейство `agentmarshal *` покрывает `open`, `accept`, `complete`, `abandon`, `reopen`, `amend`, `prune`, `migrate` (`src/agentmarshal/cli.py:146-513`) — все они пишут журнал, — и команды, трогающие local state. Старые записи указывали на пути, которых в репозитории нет, то есть фактически не давали ничего; новая даёт implementer'у весь CLI. Стоит сузить до читающих подкоманд (`status`, `brief`, `validate`, `report`, `doctor`, `leak-scan`).

**`A-framework-scripts-stale`** — `docs/harness-setup.md:11` («The rails are a sequence of ordinary commands: `git`, the framework scripts, …») и `:74` («Cover every family the rails touch: … and the framework scripts») по-прежнему говорят о «framework scripts» как о чём-то, что репозиторий поставляет. Шаблон в том же дифе от этой формулировки уже ушёл к `agentmarshal *`, а скриптов в репозитории нет (каталог `agentmarshal/` пуст, из скриптов только `templates/journal-transaction.sh`). Это остаток того же AUD-whole-project-замечания, которое критерий 5 закрывает в `self-hosting-workflow.md` и `docs/templates/`.

## Что критерии выполняют

- **Критерий 1 (типы записей)** — выполнен: `docs/known-defects.md:13` теперь говорит «thirteen», и в реестре `RECORD_TYPES` ровно тринадцать типов (`src/agentmarshal/journal/attestation.py:62-114`: opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext). Теста, читающего `known-defects.md`, нет; реестр пинится тестами `tests/test_attestation.py`.
- **Критерий 2 (user scope)** — выполнен: `docs/harness-setup.md:42-47` называет `~/.config/agentmarshal/` и `~/.local/share/agentmarshal/` решёнными, но не реализованными, и это верно — в `src/` нет ни одного обращения к `XDG_CONFIG_HOME`, `%APPDATA%` или `~/.config/agentmarshal`; CHANGELOG, «What 0.6.0 leaves out», говорит то же. Теста нет (отрицательное утверждение о коде).
- **Критерий 3 (источник контракта)** — выполнен частично: `threat-model.md:20-31`, `threat-model.md:250-255`, `self-hosting-workflow.md:158-165`, `sidecar.md:49-56` и `overview.md:131-135` оговорку получили, и формулировки точны относительно `gate.py:1054-1101` (diff = `.agentmarshal/switches.toml` + подкаталог задачи, `scope` ровно `[".agentmarshal/switches.toml"]`, база читается всегда, когда contract.md там есть, в sidecar линия не предлагается — `gate.py:1383-1392`). Демонстрируют тесты `tests/test_gate_operational.py:94`, `:119`, `:164`, `:187`, `:205`. Непокрытые места — см. `F-base-only-exception-unstated`.
- **Критерий 4 (threat model)** — выполнен. Write-time: `threat-model.md:131-135` называет четыре timestamp'а и `artifacts` `ref` — правила `timestamp-text` (`src/agentmarshal/journal/records.py:618-635`, поля `created_at`, `started_at`, `ended_at`, `resets_at`) и `artifact-ref-text` (`records.py:1410-1429`), оба «bound past today's schemas», как и написано; тесты `tests/test_record_text_safety.py:321` и `:400`. Outbox: `threat-model.md:186-198` — симлинк проверяется до любой записи во всех четырёх подкомандах (`src/agentmarshal/outbox.py:164-196`, вызовы на `:368`, `:551`, `:1078`, `:1229`), а расхождение staged-байтов ловится в check и send с откатом индекса (`outbox.py:837-849`, `:1155-1180`); тесты `tests/test_outbox.py:1923`, `:1959`, `:2018`, `:2046`, `:2114`, `:2256`. Цитаты spec-требований существуют дословно (`openspec/specs/outbox/spec.md:502`, `:532`, `:181`; `openspec/specs/gate-lanes/spec.md:170`). Sidecar-абзац `threat-model.md:318-331` цитирует точные строки: `placement.py:45`, `cli.py:993`, `:1005`, `:1204`, `:1206`, `placement.py:37`, `cli.py:950`.
- **Критерий 5** — выполнен кроме транскрипта status. Пины 0.6.0 совпадают с `pyproject.toml:3`; `docs/quickstart.md` целиком исполняется тестом `tests/test_quickstart.py` (блоки «The governed loop» прогоняются дословно и транскрипт гейта сверяется с выводом), оставшиеся «0.5.0» в quickstart — датированные заметки истории, их трогать нельзя. `github-enforcement.md:95-96` цитирует закрывающую строку точно — `src/agentmarshal/cli.py:1007`, и шаблон CI действительно зовёт гейт с `--without-review` (`templates/github/agentmarshal-governance.yml:78`). Заметка про doctor (`sidecar.md:470-473`) верна: `resolve_placement` без `require_host` только резолвит путь, проверки существования / git-worktree стоят под `require_host` (`src/agentmarshal/journal/placement.py:47-98`), и в `doctor.py` слова «host» нет вовсе. Упоминания `am-merge` / `mr.sh` как файлов репозитория убраны; таких файлов в репозитории нет.
- **Критерий 6** — диф не выходит за `docs/`, новых markdown-ссылок не добавлено, датированные заметки не переписаны. CI-последовательность я не прогонял (snapshot не git-репозиторий, тулчейн недоступен) и полагаюсь на заявление координатора о зелёном прогоне на этом коммите.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8e5e62120c62c6ab683be13f000a71660f2f5b76",
  "verdict": "changes_required",
  "findings": ["F-base-only-exception-unstated", "F-sidecar-status-transcript-stale"],
  "advisory_findings": ["A-plan-file-not-shipped", "A-template-allows-journal-writes", "A-framework-scripts-stale"],
  "classes": {
    "F-base-only-exception-unstated": "contract-mismatch",
    "F-sidecar-status-transcript-stale": "claim-accuracy",
    "A-plan-file-not-shipped": "claim-accuracy",
    "A-template-allows-journal-writes": "security",
    "A-framework-scripts-stale": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn RECORD_TYPES src/ and read src/agentmarshal/journal/attestation.py:62-114", "result": "thirteen record types declared; matches known-defects.md"},
      {"what": "grep -rn 'XDG_CONFIG_HOME|APPDATA|.config/agentmarshal|expanduser|Path.home()' src/", "result": "no user-scope directory is read or written; only placement host expanduser"},
      {"what": "grep -rn 'plan.toml|plan_file' src/", "result": "only src/agentmarshal/localstate.py:70,73 — nothing reads or writes it"},
      {"what": "read src/agentmarshal/journal/gate.py:1006-1101 and 1383-1392", "result": "candidate-side contract read confirmed, bounded by the lane predicate; lane not offered in a sidecar"},
      {"what": "grep -rn 'never from the candidate|widen its own scope|from the committed base' docs/", "result": "docs/overview.md:75-77 and docs/quickstart.md:323-324 still unqualified"},
      {"what": "read src/agentmarshal/cli.py:1453-1476 and src/agentmarshal/journal/status_view.py:834-861", "result": "status prints Placement then journal:/process log:/local state: on stderr"},
      {"what": "grep -n 'process log|local state|journal:' docs/sidecar.md", "result": "no match — the three 0.6.0 status lines appear nowhere in sidecar.md"},
      {"what": "read src/agentmarshal/journal/records.py:618-635 and 1410-1429", "result": "timestamp-text covers created_at/started_at/ended_at/resets_at; artifact-ref-text covers artifacts ref"},
      {"what": "read src/agentmarshal/outbox.py:164-196, 837-849, 1155-1180; grep _locate callers", "result": "symlink refusal before any write in new/check/send/status; staged-byte verification with index restore"},
      {"what": "grep -rn quoted sidecar/gate output strings in src/", "result": "every line quoted by threat-model.md and github-enforcement.md found verbatim in cli.py and placement.py"},
      {"what": "grep -n '^### Requirement' openspec/specs/outbox/spec.md; grep -rn 'an operational change takes its own gate lane' openspec/", "result": "all four cited requirement titles exist exactly"},
      {"what": "grep -n 'def test_' tests/test_gate_operational.py, tests/test_outbox.py, tests/test_record_text_safety.py; read tests/test_quickstart.py:1-60", "result": "supporting tests exist; test_quickstart.py executes the quickstart loop and compares the gate transcript"},
      {"what": "grep -rln 'am-merge|mr.sh' over the tree", "result": "only docs/ prose; no such files ship in the repository"},
      {"what": "grep -n 'add_parser(' src/agentmarshal/cli.py", "result": "agentmarshal * covers open/accept/complete/abandon/reopen/amend/prune/migrate, all journal writers"}
    ],
    "read": [
      "docs/harness-setup.md",
      "docs/sidecar.md",
      "docs/threat-model.md",
      "docs/overview.md",
      "docs/quickstart.md",
      "docs/self-hosting-workflow.md",
      "docs/github-enforcement.md",
      "docs/known-defects.md",
      "docs/templates/claude-code-settings.local.json",
      "docs/adr/ADR-0014-where-things-live.md",
      "CHANGELOG.md (What 0.6.0 leaves out)",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/attestation.py",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/doctor.py",
      "templates/github/agentmarshal-governance.yml",
      "openspec/specs/outbox/spec.md",
      "pyproject.toml"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the snapshot is not a git repository and the toolchain is unavailable; the coordinator states the sequence passed on this commit"},
      {"what": "a live sidecar gate/status run to diff the sidecar.md transcripts byte for byte", "why": "requires a host/sidecar repository pair and a runnable install; compared against the printing code instead"},
      {"what": "markdown link resolution script", "why": "script execution was not approved; the diff adds no new markdown links, so resolution is unchanged"}
    ]
  },
  "evidence": {
    "F-base-only-exception-unstated": "docs/overview.md:75-77 'reads the contract ... at the base from the **base** side, never from the candidate' and docs/quickstart.md:323-324 'The gate always reads the contract from the committed base, never from the candidate' — both lack the operational-lane exception the diff adds at docs/overview.md:133, docs/threat-model.md:23, docs/self-hosting-workflow.md:161 and docs/sidecar.md:52; the exception is real at src/agentmarshal/journal/gate.py:1024-1030 and tests/test_gate_operational.py:119",
    "F-sidecar-status-transcript-stale": "docs/sidecar.md:316-328 shows 'Placement: sidecar' immediately followed by 'ID: CR-001'; src/agentmarshal/cli.py:1459 then :1474 print the placement line and print_paths' three lines (src/agentmarshal/journal/status_view.py:852-861 'journal:', 'process log:', 'local state:') back to back on stderr; `grep -n 'process log|local state|journal:' docs/sidecar.md` returns nothing, and docs/sidecar.md:412 claims only the placement line is added",
    "A-plan-file-not-shipped": "docs/harness-setup.md:38-41 'That one place holds ... and the plan file'; `grep -rn 'plan.toml' src/` returns only src/agentmarshal/localstate.py:70,73; CHANGELOG.md 'What 0.6.0 leaves out' — 'there is no `agentmarshal next` and nothing reads `plan.toml`'; docs/adr/ADR-0014-where-things-live.md:158-164 lists log/, extensions/, deps/, trust.toml, switches.toml only",
    "A-template-allows-journal-writes": "docs/templates/claude-code-settings.local.json:16 '\"Bash(agentmarshal *)\"' against docs/harness-setup.md:31-32 'Never let the agent write the journal' and :34 'Give the implementer no write access to the local state'; journal-writing subcommands at src/agentmarshal/cli.py:146 (open), :204 (accept), :348 (complete), :393 (abandon), :398 (reopen), :401 (amend), :491 (prune), :502 (migrate)",
    "A-framework-scripts-stale": "docs/harness-setup.md:11 and :74 still name 'the framework scripts'; `ls agentmarshal` is empty and the only shipped script is templates/journal-transaction.sh, while the template in this same diff moved from './agentmarshal/scripts/*' to the 'agentmarshal' CLI"
  }
}
AGENTMARSHAL_VERDICT_END
