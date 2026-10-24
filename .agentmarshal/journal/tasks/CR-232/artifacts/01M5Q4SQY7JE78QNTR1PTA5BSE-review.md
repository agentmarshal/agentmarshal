Проверил диф по файлам снапшота, сверил скрипт с настоящим журналом, с `scope_covers`/`project_status` и с ADR-0001/ADR-0005.

## Где контракт выполнен

**AC1** — шаг `Check release audit` стоит в `.github/workflows/release.yml:53-62`, то есть после единственного шага с проверками тега и dev-версии (`:32-52`) и до `uv build` (`:64-65`); ненулевой выход `run` валит job, поэтому ни сборки, ни публикации не происходит. Тестом это не показано — в репозитории вообще нет тестов на YAML воркфлоу, и AC3 их не требует; критерий проверен чтением файла. `fetch-depth: 0` добавлен обоснованно: при depth-1 ни `merge-base --is-ancestor`, ни диф от audited-коммита невозможны.

**AC2** — `audit_release` (`.github/scripts/check_release_audit.py:203-339`) читает `release/audit-<version>.toml` из дерева тега через `git show` (`:219`), и каждый перечисленный отказ закрыт тестом: нерезолвимый тег — `test_unresolvable_tag_refuses`, отсутствие файла — `test_missing_audit_file_refuses`, битый TOML — `test_unparseable_audit_file_refuses`, отсутствующий ключ — `test_missing_required_key_refuses`, расхождение версии с тегом — `test_version_mismatch_refuses` (плюс `test_non_string_version_refuses`), `audited_commit` не полный sha / не коммит / не предок — `test_short_audited_commit_refuses`, `test_non_hex_audited_commit_refuses`, `test_audited_commit_not_a_commit_refuses`, `test_audited_commit_not_ancestor_refuses`, модель вне allowlist — `test_model_not_allowlisted_refuses`, форма `[[finding]]` — `test_finding_not_an_array_refuses`, `test_finding_element_not_a_table_refuses`, `test_finding_without_id_refuses`, `test_unknown_disposition_refuses`, `test_fixed_finding_without_task_refuses`, `test_deferred_finding_without_reason_refuses`, задача `fixed` без `completed` — `test_fixed_task_without_completed_record_refuses` и `test_reopened_fix_task_refuses`, нечитаемый scope — `test_fixed_task_without_contract_refuses`, путь вне объединения — `test_change_outside_allowed_paths_refuses`, сбой самого дифа — `test_diff_failure_refuses`. Правило покрытия путей (`_covered`, `:73-87`) посимвольно совпадает с `agentmarshal.journal.contracts.scope_covers` (`src/agentmarshal/journal/contracts.py:136-145`), и оговорка в докстринге про footprint'ы расширений верна — их добавляет только merge-гейт (`src/agentmarshal/journal/gate.py:1589-1598`). `_LIFECYCLE_RECORD_TYPES` (`:54`) действительно равен набору типов с непустым `projects_to` в `src/agentmarshal/journal/attestation.py:62-114`, а `record_type` в настоящих записях журнала есть (`.agentmarshal/journal/tasks/CR-231/records/01M5Q3B2SG0CHYEQ8V4V5W5167-completed.json`), так что гейт читает журнал тем же ключом, что и продукт.

**AC3** — импорты только stdlib (`datetime`, `json`, `re`, `subprocess`, `sys`, `tomllib`, `pathlib`, `typing`) плюс вызовы `git`; `tomllib` уже требуется соседним шагом воркфлоу, так что runner'ского `python3` достаточно. Печать одной строки на отказ и `release audit: passed` — `main` (`:342-353`), показано `test_main_reports_pass_and_refusals` и `test_main_usage_exits_2`; оба прохода из критерия есть — `test_passes_with_zero_findings` (ноль findings) и `test_passes_with_fixed_finding_covering_change` (правка внутри scope задачи-фикса), плюс `test_recompleted_after_reopen_passes`.

**AC4** — `CONTRIBUTING.md:137-194` даёт ровно тот порядок (release-задача → фриз → аудит allowlisted-моделью → фикс обычной задачей с обычным ревью или disposition → файл аудита → тег), фразу про отсутствие re-audit-петли, определение блокирующего finding'а (сломанное опубликованное решение или обещание threat-model, security-дефект, ложное утверждение в release-документации) и формат файла; перечисленные там причины отказа и список всегда разрешённых путей совпадают с `ALWAYS_ALLOWED` (`:35-43`) и с кодом.

**AC5** — диф трогает только `.github/scripts/`, `.github/workflows/release.yml`, `tests/` и `CONTRIBUTING.md`; продуктовый код не менялся, всё внутри scope контракта. Полную последовательность CI я не запускал — в этой read-only среде запуск `python3`/`git` не разрешён, так что опираюсь на факт координатора.

## Замечания (не блокирующие)

**audit-gate-ignores-unreadable-journal-records** — `_last_lifecycle_record` (`.github/scripts/check_release_audit.py:143-157`) молча пропускает запись, которую не удалось прочитать, распарсить или которая не объект, и докстринг (`:125-127`) оправдывает это тем, что «так проекция обходится с записями без lifecycle `record_type`». Это утверждение о коде неверно: `project_status` на незарегистрированном `record_type` поднимает `TaskStatusError` (`src/agentmarshal/journal/status.py:112`), а `read_records` падает на невалидном JSON и на не-объекте (`src/agentmarshal/journal/records.py:2703-2705`) — продукт тут fail-closed, а гейт fail-open. Практический эффект: при записях `…-completed.json` (валидной) и более поздней `…-reopened.json` с битым JSON гейт увидит `completed` и пропустит релиз, хотя журнал в таком состоянии `agentmarshal validate` отвергает.

**abandoned-fix-task-refusal-untested** — ветка `cause = "was abandoned"` (`.github/scripts/check_release_audit.py:278-279`) не покрыта ни одним тестом: в `tests/test_release_audit_check.py` слова `abandoned` нет вообще, проверены только `opened` и `reopened`. AC3 требует тестов «для каждого отказа», и это отдельная формулировка отказа — опечатка в её тексте или условии пройдёт незамеченной.

**audited-at-accepts-any-nonempty-string** — проверка `audited_at` (`.github/scripts/check_release_audit.py:262-267`) принимает любую непустую строку, так что `audited_at = "как-нибудь"` проходит, хотя сообщение об отказе утверждает `'audited_at' must be a timestamp`, а `CONTRIBUTING.md:170` документирует TOML-datetime. Отказ сработает только на нестроковом не-дате (`test_invalid_audited_at_refuses` подаёт `5`).

Отдельно, не как finding: гейт пулит scope всех задач, перечисленных как `fixed`, не проверяя, что задача завершилась после `audited_commit` — назвав любую давно закрытую задачу, оператор расширяет множество разрешённых путей. Это буквально то, что требует контракт («scopes of the tasks the file lists as `fixed`»), так что дефектом реализации не считаю, но как усиление гейта стоит иметь в виду.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b188aaa52286764617949935e0f803d90fed042e",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "audit-gate-ignores-unreadable-journal-records",
    "abandoned-fix-task-refusal-untested",
    "audited-at-accepts-any-nonempty-string"
  ],
  "classes": {
    "audit-gate-ignores-unreadable-journal-records": "claim-accuracy",
    "abandoned-fix-task-refusal-untested": "test-gap",
    "audited-at-accepts-any-nonempty-string": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -o '\"record_type\"[^,]*' .agentmarshal/journal/tasks/CR-231/records/01M5Q3B2SG0CHYEQ8V4V5W5167-completed.json", "result": "\"record_type\": \"completed\" — real journal records carry the key the script reads"},
      {"what": "grep -rn 'abandoned' tests/test_release_audit_check.py .github/scripts/check_release_audit.py", "result": "only script hits (:54, :278, :279); no test mentions abandoned"},
      {"what": "grep -n 'record has no status projection' src/agentmarshal/journal/status.py; grep -n 'invalid JSON record|record must contain a JSON object' src/agentmarshal/journal/records.py", "result": "status.py:112 raises TaskStatusError; records.py:2703,2705 raise JournalRecordError — the product fails closed where the gate skips"},
      {"what": "grep -rn 'effective_scope|scope_covers' src/agentmarshal", "result": "gate.py:1589-1598 adds extension footprints; contracts.py:136-145 is the matcher the script mirrors"},
      {"what": "wc -l on the four changed files", "result": "357 / 663 / 199 / 69 lines — snapshot matches the supplied diff"},
      {"what": "cat .gitignore", "result": "no pattern ignores release/, so the audit file can be committed"}
    ],
    "read": [
      ".github/scripts/check_release_audit.py",
      ".github/workflows/release.yml",
      "CONTRIBUTING.md",
      "tests/test_release_audit_check.py",
      "src/agentmarshal/journal/contracts.py",
      "src/agentmarshal/journal/status.py",
      "src/agentmarshal/journal/records.py (read_records)",
      "src/agentmarshal/journal/attestation.py (RECORD_TYPES)",
      "src/agentmarshal/journal/gate.py (effective scope)",
      "docs/adr/ADR-0001-governance-plane.md",
      "docs/adr/ADR-0005-evidence-capture-and-format.md",
      "pyproject.toml",
      ".gitignore"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the review sandbox denies running python3/uv/git commands; the coordinator states the sequence passed on b188aaa"},
      {"what": "git-based verification that the diff is the whole change", "why": "the snapshot is not a git repository, so the supplied diff was taken as given"}
    ]
  },
  "evidence": {
    "audit-gate-ignores-unreadable-journal-records": ".github/scripts/check_release_audit.py:125-127,143-157 vs src/agentmarshal/journal/status.py:112 and src/agentmarshal/journal/records.py:2703-2705",
    "abandoned-fix-task-refusal-untested": ".github/scripts/check_release_audit.py:278-279; grep -rn 'abandoned' tests/test_release_audit_check.py → no match",
    "audited-at-accepts-any-nonempty-string": ".github/scripts/check_release_audit.py:262-267 (isinstance(audited_at, str) and audited_at) vs CONTRIBUTING.md:170 and tests/test_release_audit_check.py:test_invalid_audited_at_refuses"
  }
}
AGENTMARSHAL_VERDICT_END
