Проверил контракт, диф, процитированные требования спецификаций, ADR-0001/0013/0014 и код.

## Как диф закрывает критерии приёмки

**AC1 — docs/threat-model.md больше не говорит, что исполнение расширений решено, но не реализовано.** `grep "not yet implemented" docs/threat-model.md` даёт только строки 13 (определение самой пометки), 107 (adopter-required-acceptance вариант ADR-0013 d17), 198/205 (`next`, ADR-0023) и 550 (`next`) — ни одна не про исполнение стадий. Абзац «No extension can change the gate's decision» (строки 207–254) теперь говорит, что код расширений выполняется, и каждое утверждение держится: `stage run`/`complete` запускают `[[stage]]` из манифеста базы (`src/agentmarshal/cli.py:1109-1117`, тест `tests/test_complete_stages.py:155 test_both_commands_go_through_the_one_runner`), результат уходит только в process-log, который гейт не читает (`openspec/specs/process-log/spec.md:221`), код и switches берутся с базы, на рабочей станции — только под совпадающим грантом, в CI — без (`openspec/specs/extension-stages/spec.md:276`, `tests/test_stages.py`), findings-lane и sidecar не запускают ни одной стадии (`tests/test_complete_stages.py:364`, `:439`), операционная полоса пропускает pre-gate (`tests/test_complete_stages.py:276`). Абзац про изоляцию (строки 418–447) перечисляет ровно то, что ядро обеспечивает: новый user+network namespace без `network = true` (`tests/test_isolation.py:132`, `:169`), на pre-gate bind-remount кандидата read-only с сохранением заблокированных флагов монтирования и повторным `chdir` (`tests/test_isolation.py:217`, `:282`, `:354`), удержание provider-secret (`tests/test_isolation.py:879`, `:920`, `:965`), сброс capabilities перед `execve` (`src/agentmarshal/isolation.py:1-42`, `tests/test_isolation.py:509`), именование неисполнимых гарантий строкой `not enforced` (`tests/test_isolation.py:598`, `:635`), «ничего вне кандидата не делается read-only» и `writes` за пределами кандидата как не обеспеченное (`tests/test_isolation.py:461`, `:486`), и что процесс того же OS-пользователя вне стадии не изолирован (строки 338–344 и 440–442, `tests/test_isolation.py:853`). Все 30 процитированных названий требований существуют дословно.

**AC2 — README стадирует каталог одной задачи.** `README.md:128` теперь `git add .agentmarshal/journal/tasks/CR-001`, абзац `README.md:152-159` повторяет обоснование из `docs/quickstart.md:325-345` и ссылается на `templates/journal-transaction.sh`, который действительно стадирует литеральный pathspec одной задачи, коммитит на ветке `journal/<task>-<slug>`, пушит и оставляет PR провайдеру с пометкой `ADAPT`. Демонстрируют `tests/test_quickstart.py` (исполняет блоки quickstart дословно — включая этот `git add`) и `tests/test_journal_transaction.py`.

**AC3 — `complete --target` задокументирован.** `docs/self-hosting-workflow.md:56-81` описывает, что решает флаг, exit 3 и отсутствие записи при не-предке, `complete: WARNING:` после слияния, стояние паузы без `--target` или при неразрешимом ref, отличие от `--base` и сценарий wrapper'а после merge. Совпадает с `src/agentmarshal/cli.py:1118-1134` и `_candidate_merged` (`src/agentmarshal/cli.py:1004-1035`), требованием `openspec/specs/extension-stages/spec.md:1359` и тестами `tests/test_complete_stages.py:511`, `:538`, `:585`, `:614`.

**AC4 — неархивированный change удалён, OpenSpec не тронут.** `openspec/changes/` содержит только `archive/`; упоминания `extension-stages-purpose` остались лишь в самом контракте задачи. Диф меняет три документа и ничего больше; новых markdown-ссылок он не добавляет, а единственный новый путь `templates/journal-transaction.sh` существует.

## Находка

**ADV-CITE-001 (advisory, claim-accuracy)** — в `docs/threat-model.md:253` цитата `ADR-0013, decisions 5, 6 and 7` стоит без пометки *decided, not yet implemented*, хотя ADR-0013 решение 7 (`docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:113-117`) обещает в словаре result-строк ещё `addressee not found` и `not run (… dependencies do not match the lock)`, а код выдаёт только пять форм (`src/agentmarshal/stages.py:725-734`, требование `openspec/specs/extension-stages/spec.md:313`), и проверки зависимостей контракт сам относит к Non-Goals. Диф снял единственную пометку, покрывавшую решение 7 (она была в абзаце про findings-lane), и по конвенции самого документа (`docs/threat-model.md:12-16`) нецитированное без пометки читается как «то, что инструмент делает сегодня». Сам текст про пять форм точен — вопрос только в охвате цитаты; исправляется оговоркой вида «решение 7 — словарь шире реализованного».

Проверки CI я не запускал: команды `uv run …` в этой песочнице не разрешены. Опираюсь на заявление координатора, что полная последовательность прошла на 77c7b2b2.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "77c7b2b2877e51dc1e1fdad767101e5718d91def",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-CITE-001"],
  "classes": {
    "ADV-CITE-001": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'not yet implemented' docs/threat-model.md", "result": "only lines 13, 107, 198, 205, 550 — none about extension execution"},
      {"what": "grep -rn 'extension-stages-purpose' --exclude-dir=.git .", "result": "only .agentmarshal/journal/tasks/CR-226/contract.md; openspec/changes/ holds only archive/"},
      {"what": "grep -n '^### ' on extension-stages, gate-lanes, process-log, leak-scan, extension-records, review-evidence, record-schema, session-activity specs", "result": "all 30 requirement titles cited in the diff exist verbatim"},
      {"what": "grep -rn 'pause accepted by' src/", "result": "src/agentmarshal/stages.py:1003,1153 — suffix exists as documented"},
      {"what": "grep -rn 'not a declared actor' src/agentmarshal/journal/status_view.py", "result": "status_view.py:141 emits ' (not a declared actor)' — the status marking the diff claims"},
      {"what": "grep -rn 'fallback_reason' src/", "result": "records.py:521 in _FORGEABLE_TEXT_FIELDS, status_view.py:419-424 prints it — both halves of the claim hold"},
      {"what": "grep -rn 'switched off' src/agentmarshal/stages.py", "result": "stages.py:734 'switched off (<reason>)' — only five result forms exist, no 'addressee not found'"},
      {"what": "grep -n '^def test' tests/test_isolation.py tests/test_complete_stages.py", "result": "backing tests exist for every isolation and --target statement the diff makes"}
    ],
    "read": [
      "docs/threat-model.md",
      "README.md",
      "docs/self-hosting-workflow.md",
      "docs/quickstart.md (lines 310-350)",
      "templates/journal-transaction.sh",
      "openspec/specs/extension-stages/spec.md",
      "openspec/specs/gate-lanes/spec.md (requirement list)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decisions 7, 8, 15, 16, 17, 18)",
      "src/agentmarshal/isolation.py (module docstring and constants)",
      "src/agentmarshal/cli.py (complete handler, _candidate_merged, --target)",
      "src/agentmarshal/stages.py (result vocabulary, provider-secret withholding)",
      "src/agentmarshal/journal/gate.py (acceptance filtering, operational lane)",
      "src/agentmarshal/journal/status_view.py (acceptance lines, fallback_reason, declared actor)",
      "src/agentmarshal/journal/records.py (schema-7 fields, forgeable-text fields)",
      ".agentmarshal/journal/tasks/CR-226/contract.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "command execution was refused by the sandbox; relying on the coordinator's statement that the full CI sequence passed on 77c7b2b2877e51dc1e1fdad767101e5718d91def"}
    ]
  },
  "evidence": {
    "ADV-CITE-001": "docs/threat-model.md:253 cites 'ADR-0013, decisions 5, 6 and 7' with no 'decided, not yet implemented' marker; docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:113-117 lists 'addressee not found' and 'not run (changed after approval, dependencies do not match the lock)' among the result lines; src/agentmarshal/stages.py:725-734 and openspec/specs/extension-stages/spec.md:313-349 define only checked / failed (exit <n>) / did not finish (timeout) / not run (<reason>) / switched off (<reason>); the diff deleted the sole 'ADR-0013, decision 7 — decided, not yet implemented' marker from the findings-lane paragraph; the convention is stated at docs/threat-model.md:12-16"
  }
}
AGENTMARSHAL_VERDICT_END
