Я прошёл по контракту, по всем трём документам и сверил каждое новое утверждение с кодом и со спецификациями.

**Что проверено по acceptance criteria**

**AC1 (threat-model говорит, что реально работает)** — выполнено. `docs/threat-model.md:207-273` больше не утверждает, что extension execution «decided, not yet implemented»: там названы `stage run --phase <pre-gate|post-gate>` (регистрация и choices — `src/agentmarshal/stages.py:236-242`), вызов того же раннера из `complete` до gate-check и после записи `completed` (`src/agentmarshal/cli.py:1113-1146` и `1193-1209`), argv-процесс под интерпретатором ядра без shell и без `PATH` (`stages.py:564`), код и switches из base (`stages.py:860,889`), grant на workstation и его отсутствие в CI (`stages.py:945-958`, `_prepare_extension` на `stages.py:447-463`); демонстрируют это `tests/test_stages.py:1035,1063,1083,1113,1129` и `tests/test_complete_stages.py:155,192,637,662`. Список result-lines в документе (`checked`, `failed (exit <n>)`, `did not finish (timeout)`, `not run (<reason>)`, `switched off (<task>, <reason>)`) совпадает байт в байт с `_result_text` (`stages.py:723-735`) — тесты `tests/test_stages.py:1164,1181,1207,1253` и `tests/test_switches.py:186`; суффикс `pause accepted by <party> (<reason>)` — `stages.py:1151-1156`, тест `tests/test_stages.py:1528`. Изоляция описана ровно тем, что ядро действительно делает: user+network namespace без `network = true`, read-only bind с сохранением locked-флагов `nosuid/nodev/noexec` и atime-семейства, повторный `chdir` после remount, withholding provider-secret имён на pre-gate, сброс capabilities перед `execve` (`src/agentmarshal/isolation.py:1-41,393-430`, `stages.py:499-504,566-590`) — тесты `tests/test_isolation.py:132,217,282,354,598,802,879`; «не enforced — названо» (`tests/test_isolation.py:486,598,802`), «ничего вне candidate не делается read-only» и «процесс того же OS-пользователя вне stage не изолирован» — согласуется с `isolation.py` (всё применяется в самом child перед `execve`) и с ADR-0013 D8/ADR-0001. Остальные `decided, not yet implemented` в файле (строки 198, 205, 264, 390, 462, 559) я проверил поштучно: `next` в CLI отсутствует, lock-проверки зависимостей в раннере нет, `addressee not found` как stage-line нет — зато есть у `validate` (`src/agentmarshal/journal/validate.py:190`, тест `tests/test_validate_addressee.py:84`).

**AC2 (README)** — выполнено: `README.md:128` стажит `.agentmarshal/journal/tasks/CR-001`, абзац `README.md:152-159` совпадает по смыслу с `docs/quickstart.md:325-341`, упомянутый `templates/journal-transaction.sh` существует и делает именно заявленное (ветка по task id, литеральный pathspec, push, PR оставлен провайдеру, маркер `ADAPT` в конце) — тесты `tests/test_journal_transaction.py:114,153,188`. Рецепт остаётся рабочим без коммита `project.json`: отсутствие `project.json` в base-дереве даёт «нет маркеров», а не отказ (`src/agentmarshal/journal/gate.py:663-693`).

**AC3 (`complete --target`)** — выполнено: `docs/self-hosting-workflow.md:56-82` описывает решение (отказ с exit 3 и ничем не записанным, пока candidate не ancestor; иначе одна `complete: WARNING:` строка на каждую паузу), что `--base` остаётся merge base, и что wrapper после мержа передаёт target-ветку. Код совпадает: `src/agentmarshal/cli.py:1004-1034` (нерешаемый `--target` читается как «не смержено», пауза стоит) и `1119-1141`; тесты `tests/test_complete_stages.py:511,538,585,614`.

**AC4** — `openspec/changes/` содержит только `archive/`, каталога `extension-stages-purpose/` нет, ссылок на него вне контракта нет; diff трогает ровно три документа, ни одного OpenSpec-файла, новых markdown-ссылок не добавлено (упоминание шаблона — code span, путь существует).

**Advisory-находки**

ADV-STAGE-NO-LINE-001 — в `docs/threat-model.md:252` фраза «One case gives a stage no line» сказана как исчерпывающая, но это не единственный случай: manifest в base, который не парсится, тоже завершает run на exit 1 вообще без stage-строк (`src/agentmarshal/stages.py:858-863`; тест `tests/test_stages.py:292` прямо проверяет `"checked" not in captured.out`), как и невалидный task id, нерешаемый ref и sidecar (`stages.py:798-811`); особенность trust-file-случая не в том, что строки нет, а в том, что run продолжается и часть строк всё ещё причитается.

ADV-REFLOW-002 — правка на месте оставила в `docs/threat-model.md` висящие обрывки строк, выбивающиеся из ~72-колоночной верстки файла: `:182` «(extension-manifest», `:293` «ADR-0008,», `:488` «declares"). The», а `:479` вышла на 80 колонок; на содержание не влияет, но абзацы читаются рвано (автоматической проверки на это в CI нет — ruff и `agentmarshal validate` документы не форматируют).

Блокирующих находок нет: ни одного утверждения о enforcement, которого нет в коде, я не нашёл, границы scope соблюдены.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "127cfab49f6b8a23a104f4e677c09a06e16160eb",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-STAGE-NO-LINE-001", "ADV-REFLOW-002"],
  "classes": {
    "ADV-STAGE-NO-LINE-001": "claim-accuracy",
    "ADV-REFLOW-002": "style"
  },
  "verification": {
    "read": [
      ".agentmarshal/journal/tasks/CR-226/contract.md",
      "docs/threat-model.md",
      "README.md",
      "docs/self-hosting-workflow.md",
      "docs/quickstart.md:300-341",
      "templates/journal-transaction.sh",
      "openspec/specs/extension-stages/spec.md (requirement index; 313-350, 879-1113, 1273-1434)",
      "openspec/specs/gate-lanes/spec.md (requirement index; 170, 344)",
      "openspec/specs/process-log/spec.md (requirement index)",
      "openspec/specs/extension-records/spec.md (requirement index)",
      "openspec/specs/leak-scan/spec.md (requirement index)",
      "openspec/specs/review-evidence/spec.md (requirement index)",
      "openspec/specs/session-activity/spec.md:58-105",
      "openspec/specs/record-schema/spec.md (requirement index)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:82-135, 251-300",
      "src/agentmarshal/stages.py:160-200, 380-470, 490-740, 760-1218",
      "src/agentmarshal/isolation.py:1-120, 330-430",
      "src/agentmarshal/cli.py:340-370, 995-1210",
      "src/agentmarshal/journal/gate.py:190-210, 647-700, 968-1010, 1750-1770, 2127-2180",
      "src/agentmarshal/journal/status_view.py:136-145, 180-195, 415-425, 760-790",
      "src/agentmarshal/journal/records.py:480-540",
      "src/agentmarshal/journal/validate.py:150-192",
      "tests/test_stages.py (test index; 292-322, 1035-1260, 1528)",
      "tests/test_isolation.py (test index)",
      "tests/test_complete_stages.py (test index)",
      "tests/test_switches.py:186-300, 413-468",
      "tests/test_journal_transaction.py (test index)",
      "tests/test_validate_addressee.py (test index)"
    ],
    "executed": [
      {
        "what": "ls openspec/changes/ and openspec/changes/archive/",
        "result": "openspec/changes/ holds only archive/; no extension-stages-purpose/ directory exists"
      },
      {
        "what": "grep -rn \"extension-stages-purpose\" over *.md/*.json/*.toml",
        "result": "only .agentmarshal/journal/tasks/CR-226/contract.md matches — no dangling document reference"
      },
      {
        "what": "grep -n \"not yet implemented|no extension code\" docs/threat-model.md",
        "result": "remaining hits are lines 13, 107, 198, 205, 264, 390, 462, 559, 569 — each checked against the code (next absent from the CLI, no dependency-lock check and no addressee stage line in stages.py)"
      },
      {
        "what": "grep -n \"git add|.agentmarshal\" README.md",
        "result": "no wide `git add .agentmarshal` remains; line 128 stages .agentmarshal/journal/tasks/CR-001"
      },
      {
        "what": "grep -n result-line spellings in src/agentmarshal/stages.py",
        "result": "_result_text at 723-735 yields exactly checked / failed (<reason>) / did not finish (<reason>) / switched off (<reason>) / not run (<reason>), matching the document's list"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "this non-interactive session cannot get approval to run them; the coordinator states the full sequence passed on 127cfab49f6b8a23a104f4e677c09a06e16160eb, and the diff touches only Markdown"
      },
      {
        "what": "git history of the task (to see the deletion of openspec/changes/extension-stages-purpose/ as a diff)",
        "why": "the review snapshot is not a git repository; the criterion was checked against the tree state instead"
      }
    ]
  },
  "evidence": {
    "ADV-STAGE-NO-LINE-001": "claim at docs/threat-model.md:252 (\"One case gives a stage no line\"); counter-case at src/agentmarshal/stages.py:858-863 (_base_extensions failure -> print + return StageRunResult(1), before any plan or stage line) with tests/test_stages.py:292-322 asserting `assert \"checked\" not in captured.out` for a base manifest that cannot be parsed; further cases at src/agentmarshal/stages.py:798-811 (unknown phase, invalid task id, sidecar). The trust-file case itself is stages.py:945-958 plus 1097-1101 and tests/test_switches.py:413.",
    "ADV-REFLOW-002": "docs/threat-model.md:182 is the single token \"(extension-manifest\"; :293 is \"ADR-0008,\"; :488 is \"declares\\\"). The\"; :479 runs to 80 columns while the surrounding file wraps near 72. No tool enforces Markdown width here (ruff covers Python only; `agentmarshal validate` reads the journal)."
  }
}
AGENTMARSHAL_VERDICT_END
