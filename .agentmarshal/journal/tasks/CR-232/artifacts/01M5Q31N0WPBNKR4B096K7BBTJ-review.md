Прочитал контракт, диff, оба ADR, `CONTRIBUTING.md`, продуктовый `scope_covers`/`gate.py` и конфиг проверок. Выполнить CI сам не смог — запуск `python3`/`git`/`pytest` в этой сессии блокируется approval'ом, так что про прохождение CI опираюсь на факт координатора и помечаю это как `not_run`.

**По критериям приёмки — где диff их выполняет и чем это показано**

1. **Гейт в workflow после проверок тега и до сборки.** `.github/workflows/release.yml:53-62`: шаг `Check release audit` стоит между `Verify tag matches project version` и `astral-sh/setup-uv@v5` / `uv build`, без `continue-on-error`, поэтому ненулевой выход останавливает job до сборки и публикации. `fetch-depth: 0` на checkout добавлен верно — при дефолтной глубине 1 ни предок, ни diff недоступны. Сам YAML тестами не покрывается (и не может быть), но код выхода, на который опирается шаг, демонстрирует `test_main_reports_pass_and_refusals` (1 при отказе, 0 при проходе).
2. **Чтение `release/audit-<version>.toml` и отказ с названной причиной по каждой причине.** Формат задокументирован в `CONTRIBUTING.md:164-192`. Каждая перечисленная причина показана тестом: отсутствие файла — `test_missing_audit_file_refuses`; malformed — `test_unparseable_audit_file_refuses` и `test_missing_required_key_refuses`; несовпадение `version` с тегом — `test_version_mismatch_refuses`; `audited_commit` не предок — `test_audited_commit_not_ancestor_refuses` (плюс `test_audited_commit_not_a_commit_refuses`); модель вне allowlist — `test_model_not_allowlisted_refuses`; `fixed`-задача без `completed`-записи — `test_fixed_task_without_completed_record_refuses`; путь вне объединения — `test_change_outside_allowed_paths_refuses`. Объединение путей в `ALWAYS_ALLOWED` (`check_release_audit.py:35-43`) совпадает со списком критерия по составу, а scope `fixed`-задач читается из контрактов именно помеченного дерева (`_contract_scope`, строки 85-113).
3. **Только stdlib и git, один шаг до `uv sync`, по строке на отказ и `release audit: passed`.** Импорты `check_release_audit.py:19-26` — `datetime`, `json`, `re`, `subprocess`, `sys`, `tomllib`, `pathlib`, `typing`, ничего из продукта; `requires-python = ">=3.12"`, а предыдущий шаг workflow уже использует `tomllib` через тот же `python3`, так что `tomllib` на runner'е есть. Вывод и коды возврата демонстрирует `test_main_reports_pass_and_refusals`; оба требуемых прохода — `test_passes_with_zero_findings` (ноль findings) и `test_passes_with_fixed_finding_covering_change` (fix внутри scope задачи CR-7 плюс `deferred` с reason).
4. **Раздел релизов в `CONTRIBUTING.md`.** `CONTRIBUTING.md:137-192`: порядок 1-6 (релизная задача → freeze → аудит allowlisted-моделью → фикс обычной задачей с обычным review либо disposition → файл аудита → тег), «нет re-audit loop, следующий аудит — следующего релиза» в строках 159-162, определение blocking-finding (сломанное опубликованное решение или обещание threat model, security-дефект, ложное утверждение в релизной документации) в строках 152-155. Документация, тестом не демонстрируется.
5. **Продуктовый код не менялся.** Диff трогает `.github/workflows/release.yml`, `.github/scripts/check_release_audit.py`, `tests/test_release_audit_check.py`, `CONTRIBUTING.md` — всё внутри scope, `src/` не задет; `release/` в scope остался неиспользованным, что допустимо. Прохождение полного CI сам не проверял.

Противоречий с ADR-0001 и ADR-0005 не нашёл: гейт живёт в CI, то есть на server-side стороне, которой ADR-0001 отдаёт authority, а файл аудита лежит в `release/`, несёт только dispositions и явно разрешает скрыть описание finding'а — это согласуется с private-by-default из ADR-0005 и не нарушает запрет AGENTS.md писать под `.agentmarshal/journal/`.

**Замечания (все advisory, ни одно не блокирует)**

ADV-1 — `check_release_audit.py:291-309`: решающая проверка «что изменилось после аудита» читает `diff.stdout`, не проверяя `diff.returncode`. Если `git diff` завершится ошибкой, stdout пуст, ни одного отказа не добавится, и при прочем корректном файле гейт напечатает `release audit: passed`, фактически не сравнив деревья, — fail-open в гейте. Все остальные вызовы git в скрипте код возврата проверяют (`_git_show` 64-65, `_has_completed_record` 129-130, `cat-file`/`merge-base` 275-283), так что это внутренняя несогласованность. Конкретного входа, который ломает `git diff` на этом этапе, я назвать не могу, поэтому advisory, а не blocking.

ADV-2 — `check_release_audit.py:68-74`: docstring `_covered` утверждает, что гейт «reads a task's scope the way the scope was granted». Правило сопоставления действительно идентично `scope_covers` (`src/agentmarshal/journal/contracts.py:136-145`), но merge-гейт выдаёт задаче effective scope = `contract.scope` **плюс** footprint'ы названных контрактом extensions (`src/agentmarshal/journal/gate.py:1589-1598`). Для задачи-фикса с `extensions` релизный гейт прочитает меньше, чем было выдано, и откажет легитимному релизу сообщением, которое оператор сможет починить только расширением контракта. Сейчас латентно: ни один контракт в журнале не объявляет `extensions`. Поведение соответствует буквальной формулировке критерия («read from their contracts»), дефект — в переобещающей фразе docstring.

ADV-3 — `tests/test_release_audit_check.py`: все причины отказа, перечисленные в критерии, покрыты, но часть ветвей отказа скрипта тестами не задета — неразрешимый тег (`check_release_audit.py:201`), `finding` не массив (155), элемент не таблица (159), пустой или отсутствующий `id` (163), нестроковый `version` (220), неполный/неверный `audited_commit` (231), нестроковый `model` (240), негодный `audited_at` (252) и usage-выход 2 в `main` (317-318). Из них практически заметен отказ на сокращённом SHA в `audited_commit` — очень естественная ошибка оператора, чьё сообщение никем не проверяется.

ADV-4 — `pyproject.toml:66`: `files = ["src", "tests"]`, поэтому `uv run mypy` новый `.github/scripts/check_release_audit.py` не проверяет, хотя весь остальной Python в репозитории идёт под strict (ruff его, наоборот, покрывает — `extend-exclude` содержит только `./agentmarshal`). Это ровно тот файл, который решает, выйдет ли релиз. Починить в рамках задачи нельзя: `pyproject.toml` вне scope контракта, так что это материал для departure, а не для правки здесь.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "21c763b4d757b43241995a8a26307c432fb177d5",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1", "ADV-2", "ADV-3", "ADV-4"],
  "classes": {
    "ADV-1": "correctness",
    "ADV-2": "claim-accuracy",
    "ADV-3": "test-gap",
    "ADV-4": "test-gap"
  },
  "verification": {
    "read": [
      ".github/scripts/check_release_audit.py",
      ".github/workflows/release.yml",
      "tests/test_release_audit_check.py (as supplied in the diff; on-disk line count confirmed 397)",
      "CONTRIBUTING.md",
      "pyproject.toml",
      "docs/adr/ADR-0001-governance-plane.md",
      "docs/adr/ADR-0005-evidence-capture-and-format.md",
      "src/agentmarshal/journal/contracts.py:1-240",
      "src/agentmarshal/journal/gate.py:1560-1610",
      "gitflic-ci.yaml",
      "CHANGELOG.md:1-40",
      "AGENTS.md"
    ],
    "executed": [
      {
        "what": "grep -rn 'def scope_covers' -A 30 src/",
        "result": "src/agentmarshal/journal/contracts.py:136-145 — identical matching rule to the script's _covered"
      },
      {
        "what": "grep -n 'effective_scope = list(contract.scope)|effective_scope.extend(named_manifest.footprint)|outside = [path for path in changed' src/agentmarshal/journal/gate.py",
        "result": "1589, 1594, 1598 — effective scope is contract.scope plus named extensions' footprints"
      },
      {
        "what": "grep -rl '^extensions = ' .agentmarshal/journal/tasks/*/contract.md | wc -l",
        "result": "0 — no contract in the journal names extensions, so ADV-2 is latent"
      },
      {
        "what": "grep -n 'pypi|publish|twine|uv build|tags' gitflic-ci.yaml",
        "result": "only a 'tags:' docker runner key — the second CI provider does not publish, so the gate has no sibling bypass"
      },
      {
        "what": "grep -rn 'release.yml|release workflow|audit' docs/*.md README.md SECURITY.md CHANGELOG.md",
        "result": "no document outside the contract's scope describes release.yml's steps, so no statement elsewhere is falsified"
      },
      {
        "what": "grep -c '' .github/scripts/check_release_audit.py tests/test_release_audit_check.py",
        "result": "329 and 397 — on-disk files match the diff exactly"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "command execution (python3, git, uv) is refused by the sandbox in this session; the coordinator's note that the sequence passed on 21c763b4 is taken as given and no tool-failure claim is made"
      },
      {
        "what": "executing audit_release against purpose-built git repositories to probe the diff-returncode fail-open of ADV-1",
        "why": "same execution restriction; ADV-1 rests on reading check_release_audit.py:291-309 against the script's own returncode-checking calls"
      }
    ]
  },
  "evidence": {
    "ADV-1": ".github/scripts/check_release_audit.py:293-302 — `diff = _git(repo, \"diff\", ...)` then `for path in diff.stdout.split(\"\\0\")`, with no `diff.returncode` test, unlike :64-65, :129-130 and :275-283",
    "ADV-2": ".github/scripts/check_release_audit.py:68-74 (docstring: \"the way the scope was granted\") versus src/agentmarshal/journal/gate.py:1589-1598 (`effective_scope = list(contract.scope)` then `effective_scope.extend(named_manifest.footprint)`); grep for '^extensions = ' over .agentmarshal/journal/tasks/*/contract.md returns 0 matches, so the divergence is currently latent",
    "ADV-3": "refusal branches with no test in tests/test_release_audit_check.py: check_release_audit.py:201, :155, :159, :163, :220, :231, :240, :252, :317-318",
    "ADV-4": "pyproject.toml:66 `files = [\"src\", \"tests\"]` — `.github/scripts/check_release_audit.py` is outside mypy's targets, while pyproject.toml:50 `extend-exclude = [\"./agentmarshal\"]` leaves it inside ruff's"
  }
}
AGENTMARSHAL_VERDICT_END
