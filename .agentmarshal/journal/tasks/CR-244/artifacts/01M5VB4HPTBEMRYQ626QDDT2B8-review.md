Проверил diff против контракта и против кода на `0796691`.

## Acceptance criteria — где diff их выполняет и чем это подтверждено

**AC1 (типы записей).** `docs/known-defects.md:13` теперь говорит «thirteen». Реестр `src/agentmarshal/journal/attestation.py:62` объявляет ровно 13 типов (`opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext`); пинится тестом `tests/test_attestation.py:82 test_the_three_modules_read_the_one_registry`, который перечисляет все тринадцать литералом.

**AC2 (user scope).** `docs/harness-setup.md:35-50` больше не отдаёт trust/switches/extension code в `~/.config`: `src/agentmarshal/localstate.py` держит под `.git/agentmarshal/` именно `log`, `extensions`, `deps`, `trust.toml`, `switches.toml`, `plan.toml`, а grep по `src/` на `XDG_CONFIG|\.config/agentmarshal|local/share|APPDATA` не даёт ни одного попадания — то есть «nothing in the tool reads or writes them» верно. Оговорка про `plan.toml` тоже верна: он только объявлен (`localstate.py:70`), читателей нет. Ссылки на ADR-0014 (`docs/adr/ADR-0014-where-things-live.md:167-168`) и CHANGELOG (`CHANGELOG.md:256`, «What 0.6.0 leaves out») резолвятся. Тесты: `tests/test_localstate.py:115` (набор локаций, включая `plan_file`), `tests/test_doctor_steps_paths.py:318 test_in_a_sidecar_the_paths_are_the_journal_repositorys` (пути — только journal-репозитория, host не упоминается).

**AC3 (исключение operational lane).** Оговорка добавлена во все места, где docs утверждали «never from the candidate»: `threat-model.md:23`, `overview.md:74` и `:135`, `quickstart.md:323`, `sidecar.md:51`, `self-hosting-workflow.md:166`, `CONTRIBUTING.md:85`. Код совпадает: `gate.py:1006 _operational_contract` читает contract с merge-base, а при отсутствии `contract.md` там — с кандидата, и только внутри предиката `gate.py:1054 operational_candidate` (diff = `.agentmarshal/switches.toml` + собственное поддерево задачи; `contract.scope` ровно `(".agentmarshal/switches.toml",)`; в sidecar lane не предлагается). Совпадает и со spec `openspec/specs/gate-lanes/spec.md:171-215`. Journal-only lane контракт вообще не читает (ветка `gate.py:1480` не присваивает `contract`), так что «one exception» — точно. Тесты: `tests/test_gate_operational.py:119 test_a_task_opened_within_the_candidate_reads_the_candidate_contract`, `:94` (база, когда задача там есть), `:205` (в sidecar lane не предлагается).

**AC4 (write-time + outbox + цитаты sidecar).** `threat-model.md:131-137` описывает ровно то, что делает код: `records.py:618 _check_timestamp_text` (`created_at`, и для `session` — `started_at`, `ended_at`, `resets_at`) и `records.py:1410 _check_artifact_ref_text` (`artifacts[].ref`), оба зарегистрированы в `_RULE_FROM_SCHEMA` как `8` (`records.py:1598-1599`) и применяются только на записи (`records.py:1632`) — отсюда «bound past today's schemas so they reach no record a read can load». Тесты: `tests/test_record_text_safety.py:321` и `:400`. Outbox-часть (`threat-model.md:186-199`) соответствует `outbox.py:176-195` (отказ по symlink в `_locate`, который вызывают все четыре подкоманды — `:368, :551, :1078, :1229`), `outbox.py:837-930` (отказ, когда staged-байты расходятся с прочитанными: clean filter / eol / `core.autocrlf`) и `outbox.py:981-1049` (сверка staged-blob'ов с проверенными и возврат индекса). Формулировки совпадают с `openspec/specs/outbox/spec.md:502` и `:532`. Тесты: `tests/test_outbox.py:1923, 1959, 2018, 2046, 2114, 2256`. Все цитаты в sidecar-абзаце (`threat-model.md:322-332`) существуют дословно: `placement.py:45`, `cli.py:993, 1005, 1204, 1206`, `cli.py:950` + `placement.py:37`; пинится `tests/test_placement.py:388-394`.

**AC5 (версии, транскрипты, closing line, operator tooling).** Пины `0.6.0` в `quickstart.md:6,26,250,259,456` и `sidecar.md:77,127` (версия пакета в `pyproject.toml:3` — `0.6.0`); исторические пометки «new in 0.3.0 / Since 0.5.0» не тронуты, как требует AC6. Gate-транскрипт в `sidecar.md:227-240` байт-в-байт совпадает с золотым фикстуром `tests/fixtures/gate/sidecar-implementation.stdout`, который пинится тестом `tests/test_gate.py:527 test_default_run_transcript_matches_the_committed_fixture[sidecar-implementation]`. Новые строки `status` (`journal:`, `process log:`, `local state:`) печатаются именно после `Placement:` (`cli.py:1460` → `cli.py:1474` → `status_view.py:852-861`), тест `tests/test_status_view.py:312`; строки `Cost sessions_without_cost=1` и `Checks rejected_commits=0` + дисклеймер идут в том порядке, что в документе (`report.py:963, 970-972`, `format_report` `:1008-1020`), тесты `tests/test_report.py:202`, `tests/test_unmeasured_session_usage.py:382`. Заметка про `doctor` верна: `doctor.py:884` зовёт `resolve_placement` без `require_host`, а проверки существования/worktree живут только под `require_host` (`placement.py:86-97`). Closing line в `github-enforcement.md:95-96` дословно равна `cli.py:1007`. `am-merge`/`mr.sh` больше нигде не описаны как файлы репозитория (`self-hosting-workflow.md:16,44,97-105,139`), а шаблон `docs/templates/claude-code-settings.local.json` потерял `./agentmarshal/scripts/*` и `./agentmarshal/bin/*`; `.gitmodules` действительно указывает submodule `agentmarshal` на `agentmarshal-v1.git`, и `templates/journal-transaction.sh` — единственный `*.sh` в репозитории (`find . -name "*.sh"`).

**AC6.** Diff трогает только `docs/` и `CONTRIBUTING.md`, причём CONTRIBUTING — ровно одно предложение про base-only contract, как разрешила поправка контракта. Новых markdown-ссылок хунки не добавляют, так что набор ссылок не изменился. Полную CI-последовательность я не запускал (read-only review); по заявлению координатора она прошла на этом коммите.

## Advisory findings

**DOC-244-A (unconfirmed).** `docs/quickstart.md:5-8` теперь утверждает, что каждая команда «The governed loop» была прогнана на wheel `agentmarshal` 0.6.0, собранном до публикации релиза, и `:26` ставит `pip install agentmarshal==0.6.0`, тогда как `CHANGELOG.md:11` говорит «0.6.0 — unreleased»: пин контрактом предписан и станет верным в момент релиза, но утверждение о состоявшемся прогоне на wheel ничем в дереве не подтверждается, а проверить его извне я не могу. Смягчает это `tests/test_quickstart.py` — он прогоняет те же блоки против текущего source tree в CI и сверяет gate-транскрипт шага 5.

**DOC-244-B.** `docs/self-hosting-workflow.md:37` осталось единственным местом в `docs/`, где про contract сказано «the diff is within the contract scope read from the base tree» без оговорки про operational lane; предложение перечисляет условия review-bound lane (включая approved review), поэтому ложным не становится, но AC3 просит оговорку «and any other place», и читатель, встретивший шаг 4 раньше строки 166, уносит безусловную формулировку.

**DOC-244-C.** `docs/harness-setup.md:78-80` относит `init` и `outbox` к «journal writers»: `init` пишет `.agentmarshal/project.json` (`cli.py:136`), а `outbox` — черновики под `.agentmarshal/upstream/` и batch-commit (`outbox.py:22-31`), записей журнала ни тот, ни другой не пишет. Вывод («остаётся у оператора») верен, неточна только классификация — в файле, который в остальном очень аккуратен к тому, что где лежит.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "079669130130e1fa8fb763bbe42af245092259e8",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["DOC-244-A", "DOC-244-B", "DOC-244-C"],
  "classes": {
    "DOC-244-A": "claim-accuracy",
    "DOC-244-B": "contract-mismatch",
    "DOC-244-C": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn RECORD_TYPES src/ and read src/agentmarshal/journal/attestation.py:62-114", "result": "thirteen registered record types; docs/known-defects.md:13 'thirteen' correct"},
      {"what": "grep -rn 'XDG_CONFIG|\\.config/agentmarshal|local/share|APPDATA|user_config' src/", "result": "no matches — the user scope is unimplemented, as harness-setup.md now says"},
      {"what": "grep -rn 'plan_file|plan.toml' src/ tests/", "result": "only localstate.py:70 definition and tests/test_localstate.py:115,175 — nothing reads or writes it"},
      {"what": "read src/agentmarshal/journal/gate.py:1006-1105 and openspec/specs/gate-lanes/spec.md:171-215", "result": "operational contract read from base when present, from candidate when the candidate opens the task, bounded by the switches-only predicate and absent in a sidecar"},
      {"what": "grep -n 'timestamp-text|artifact-ref-text' src/agentmarshal/journal/records.py and read _RULE_FROM_SCHEMA:1596-1600 plus validate loop:1631-1636", "result": "both rules bound at schema 8 and applied only for_write"},
      {"what": "grep -n 'symlink|staged|autocrlf|restore' src/agentmarshal/outbox.py and read :165-200, :837-930, :981-1049", "result": "symlink refusal in _locate used by new/check/send/status; transform refusal; staged-blob verification and index restore"},
      {"what": "grep -rn 'advisory checks passed|advisory checks refused|Sidecar checks are advisory|completed after advisory checks|findings passed|completed through findings|passed what it examined' src/", "result": "every quoted line exists verbatim in cli.py:950,993,1005,1007,1204,1206 and placement.py:45"},
      {"what": "cat tests/fixtures/gate/sidecar-implementation.stdout vs docs/sidecar.md:227-240", "result": "identical line for line (SHA placeholder aside)"},
      {"what": "read src/agentmarshal/journal/report.py:936-1020 and status_view.py:834-861, cli.py:1453-1476", "result": "Placement line then journal/process log/local state; Round, then Cost, then Checks + declaration — the order sidecar.md prints"},
      {"what": "grep -n host src/agentmarshal/doctor.py and src/agentmarshal/journal/placement.py; read doctor.py:880-902", "result": "doctor resolves the placement without require_host, so existence/worktree/reachability are never checked"},
      {"what": "grep -rn 'am-merge|mr.sh|agentmarshal/scripts|agentmarshal/bin|framework script' docs/ CONTRIBUTING.md README.md", "result": "no remaining place describes them as files this repository ships"},
      {"what": "find . -name '*.sh' -not -path './.git/*' and cat .gitmodules", "result": "templates/journal-transaction.sh is the only script; submodule agentmarshal -> agentmarshal-v1.git"},
      {"what": "grep -rn '0\\.5\\.0|0\\.4\\.1' docs/*.md", "result": "only dated history notes remain ('new in 0.3.0', 'Since 0.5.0'), which AC6 asks to leave alone"},
      {"what": "grep -rn 'never from the candidate|from the base side|base-only' docs/ CONTRIBUTING.md README.md UPGRADING.md", "result": "all unqualified occurrences carry the exception except docs/self-hosting-workflow.md:37 (DOC-244-B); README/UPGRADING make no such claim, so no out-of-scope departure was owed"}
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-244/contract.md",
      "docs/harness-setup.md",
      "docs/known-defects.md",
      "docs/sidecar.md",
      "docs/quickstart.md",
      "docs/self-hosting-workflow.md",
      "docs/threat-model.md",
      "docs/overview.md",
      "docs/github-enforcement.md",
      "docs/templates/claude-code-settings.local.json",
      "CONTRIBUTING.md",
      "CHANGELOG.md (0.6.0 section and 'What 0.6.0 leaves out')",
      "docs/adr/ADR-0014-where-things-live.md",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/cli.py",
      "openspec/specs/outbox/spec.md",
      "openspec/specs/gate-lanes/spec.md",
      "tests/test_attestation.py",
      "tests/test_gate.py",
      "tests/test_gate_operational.py",
      "tests/test_quickstart.py",
      "tests/test_doctor_steps_paths.py",
      "tests/fixtures/gate/sidecar-implementation.stdout"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; the coordinator states the sequence passed on this commit"},
      {"what": "pip install agentmarshal==0.6.0 and the quickstart wheel run", "why": "no network and 0.6.0 is unreleased per CHANGELOG.md:11 — basis for marking DOC-244-A unconfirmed"}
    ]
  },
  "evidence": {
    "DOC-244-A": "docs/quickstart.md:5-8 and :26 claim a 0.6.0 wheel run and pin pip install agentmarshal==0.6.0, while CHANGELOG.md:11 reads '## 0.6.0 — unreleased'; tests/test_quickstart.py replays the loop against the source tree only",
    "DOC-244-B": "docs/self-hosting-workflow.md:37 'the diff is within the contract scope read from the base tree' — no operational-lane exception, unlike the same file's docs/self-hosting-workflow.md:166-171",
    "DOC-244-C": "docs/harness-setup.md:78-80 lists 'init' and 'outbox' among 'journal writers'; src/agentmarshal/cli.py:136 (init writes .agentmarshal/project.json) and src/agentmarshal/outbox.py:22-31 (outbox writes .agentmarshal/upstream and a batch commit) write no journal record"
  }
}
AGENTMARSHAL_VERDICT_END
