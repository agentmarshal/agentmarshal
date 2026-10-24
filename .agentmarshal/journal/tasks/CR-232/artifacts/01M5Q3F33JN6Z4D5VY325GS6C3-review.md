Проверил снапшот по файлам: скрипт, workflow, тесты, CONTRIBUTING, а также реальные записи журнала и `scope_covers` в продукте.

## Что сошлось с критериями приёмки

**AC1 — шаг в workflow.** `.github/workflows/release.yml:53-62`: шаг `Check release audit` стоит после `Verify tag matches project version` и до `astral-sh/setup-uv@v5` / `uv build`, без `continue-on-error`, поэтому ненулевой код завершения валит job до сборки и публикации. Коды возврата, на которые опирается job, демонстрирует `test_main_reports_pass_and_refusals` (1 при отказе, 0 при проходе). `fetch-depth: 0` в checkout добавлен обоснованно — `merge-base`/`diff` по audited_commit на depth-1 не работают. Сам YAML тестом не покрыт, но тестов на workflow в репозитории и нет.

**AC2 — причины отказа.** Каждая перечисленная в контракте причина имеет свой тест, строящий отдельный репозиторий: отсутствие файла — `test_missing_audit_file_refuses`; битый TOML и нехватка ключа — `test_unparseable_audit_file_refuses`, `test_missing_required_key_refuses`; расхождение `version` с тегом — `test_version_mismatch_refuses`; не-предок — `test_audited_commit_not_ancestor_refuses` (плюс `test_audited_commit_not_a_commit_refuses`); модель вне allowlist — `test_model_not_allowlisted_refuses`; `fixed`-задача без `completed` — `test_fixed_task_without_completed_record_refuses`; путь вне объединения — `test_change_outside_allowed_paths_refuses`. `ALWAYS_ALLOWED` (`check_release_audit.py:35-43`) совпадает со списком контракта пофайлово, scope читается из контракта в tagged-дереве (`_contract_scope`, строки 85-113), а `_covered` (68-82) повторяет `src/agentmarshal/journal/contracts.py:136-145` буквально — комментарий про `scope_covers` правдив. Имя записи `<ULID>-completed.json` и поле `record_type: "completed"` сверил с настоящей записью `.agentmarshal/journal/tasks/CR-116/records/01M3TT83F306M6A2YHXZH1PVCB-completed.json`.

**AC3 — stdlib и вывод.** Импорты только `datetime, json, re, subprocess, sys, tomllib, pathlib, typing` (`tomllib` есть в python3 ранера), продукт не импортируется; `main` печатает по строке на отказ и `release audit: passed` на успехе — `test_main_reports_pass_and_refusals`. Оба прохода покрыты: `test_passes_with_zero_findings` и `test_passes_with_fixed_finding_covering_change`.

**AC4 — CONTRIBUTING.** `CONTRIBUTING.md:136-192` даёт порядок (релизная задача → фриз → аудит allowlist-моделью → фиксы обычными задачами с обычным review либо диспозиция → файл аудита → тег), прямо говорит «There is no re-audit loop: … the next audit is the next release's» и определяет блокирующую находку (сломанное опубликованное решение/обещание threat-model, security-дефект, ложное утверждение в релизной документации). Формат файла описан со всеми ключами и с оговоркой, что описание находки можно не раскрывать.

**AC5 — product code.** В дифе нет ни одного пути под `src/`; все изменённые пути лежат в scope контракта.

Противоречий с ADR-0001 (авторитет гейта только server-side — релизный гейт в CI) и ADR-0005 (гейт читает плоские записи журнала напрямую) не нашёл.

## Замечания (неблокирующие)

`reopened-task-counts-as-fixed` — `.github/scripts/check_release_audit.py:116-143`: `_has_completed_record` принимает любую запись `*-completed.json`, а `reopened` проецирует завершённую задачу обратно в `open` (`src/agentmarshal/journal/attestation.py:76-80`, `status.py:33,123-128`), так что задача, у которой фикс переоткрыли — ровно тот случай, для которого `reopened` и существует, — всё ещё считается закрывшей находку; откат плохого фикса при этом лежит в её собственном scope, а запись `reopened` — под всегда разрешённым `.agentmarshal/journal/`, поэтому релиз пройдёт гейт с нефиксированной находкой. Критерий приёмки сформулирован именно как «нет записи `completed`», так что буква контракта соблюдена — отсюда advisory, а не блок.

`refusal-branches-without-tests` — `tests/test_release_audit_check.py`: из 21 сообщения об отказе 8 не покрыты ни одним тестом — недостижимый тег (`check_release_audit.py:199-201`), нестроковые `version`/`model` (220, 240), неполный/нешестнадцатеричный `audited_commit` (229-233), некорректный `audited_at` (247-252), `finding` не массив таблиц (154-155), элемент не таблица (159), пустой `id` (163). Критерий требует тестов «for every refusal»; все причины, перечисленные в самом контракте, покрыты, непокрытыми остались ветки проверки типов внутри «malformed» — поэтому advisory.

`gate-argument-is-tag-not-version` — `.github/workflows/release.yml:62` и `check_release_audit.py:4,196`: критерий AC1 говорит о запуске `check_release_audit.py <version>`, а шаг передаёт тег (`github.ref_name`, `v0.6.0`); скрипт принимает именно тег и снимает `v` сам, бараньей версией (`0.6.0`) он бы отказал на `rev-parse`. Информационно это эквивалентно (тег = `v<version>`, и предыдущий шаг уже сверил его с pyproject), docstring и CONTRIBUTING согласованы между собой на `<tag>` — расхождение чисто в букве критерия.

Проверки CI я не запускал: в этой песочнице нет git-репозитория и запуск python/uv не разрешён — опираюсь на утверждение координатора о прохождении на этом коммите.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "21c763b4d757b43241995a8a26307c432fb177d5",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "reopened-task-counts-as-fixed",
    "refusal-branches-without-tests",
    "gate-argument-is-tag-not-version"
  ],
  "classes": {
    "reopened-task-counts-as-fixed": "correctness",
    "refusal-branches-without-tests": "test-gap",
    "gate-argument-is-tag-not-version": "contract-mismatch"
  },
  "verification": {
    "read": [
      ".github/scripts/check_release_audit.py",
      ".github/workflows/release.yml",
      "tests/test_release_audit_check.py",
      "CONTRIBUTING.md:1-192",
      "docs/adr/ADR-0001-governance-plane.md",
      "docs/adr/ADR-0005-evidence-capture-and-format.md",
      "src/agentmarshal/journal/contracts.py:136-145",
      "src/agentmarshal/journal/status.py:33-141",
      "src/agentmarshal/journal/attestation.py:70-82",
      "src/agentmarshal/journal/records.py:94-103,663-670",
      ".agentmarshal/journal/tasks/CR-116/records/01M3TT83F306M6A2YHXZH1PVCB-completed.json",
      "pyproject.toml",
      "gitflic-ci.yaml"
    ],
    "executed": [
      {
        "what": "grep -rn 'def scope_covers' -A 30 src/agentmarshal/journal/contracts.py",
        "result": "lines 136-145 identical in logic to the script's _covered"
      },
      {
        "what": "ls .agentmarshal/journal/tasks/CR-116/records/ and head of its completed record",
        "result": "01M3TT83F306M6A2YHXZH1PVCB-completed.json with \"record_type\": \"completed\" — matches the gate's filename and field checks"
      },
      {
        "what": "grep -n 'publish|pypi|uv build|tags' gitflic-ci.yaml",
        "result": "only a test stage; no second publishing path that could bypass the gate"
      },
      {
        "what": "ls -d release",
        "result": "No such file or directory — the audit file is created at release time; nothing in the contract requires it now"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "the snapshot is not a git repository and this sandbox denies running python/uv; relying on the coordinator's statement that the sequence passed at this commit"
      }
    ]
  },
  "evidence": {
    "reopened-task-counts-as-fixed": ".github/scripts/check_release_audit.py:116-143 accepts any *-completed.json with record_type 'completed'; src/agentmarshal/journal/attestation.py:76-80 defines reopened as projecting a done task to 'open' (admitted_after_terminal={'done'}), and src/agentmarshal/journal/status.py:123-128 enforces it, so a completed-then-reopened task still satisfies the gate",
    "refusal-branches-without-tests": "refusal sites in .github/scripts/check_release_audit.py at lines 199-201, 220, 229-233, 240, 247-252, 154-155, 159, 163 have no matching assertion in tests/test_release_audit_check.py (its tests assert on: missing file, invalid TOML, missing key 'model', version mismatch, allowlist, not-a-commit, not-ancestor, fixed-without-task, deferred-without-reason, unknown disposition, no completed record, unreadable scope, path outside allowed, two passes, main)",
    "gate-argument-is-tag-not-version": "contract acceptance criterion 1 says 'runs .github/scripts/check_release_audit.py <version>'; .github/workflows/release.yml:59-62 passes TAG=${{ github.ref_name }}, and .github/scripts/check_release_audit.py:196 does version = tag.removeprefix('v') with line 199 resolving that argument as a tag ref"
  }
}
AGENTMARSHAL_VERDICT_END
