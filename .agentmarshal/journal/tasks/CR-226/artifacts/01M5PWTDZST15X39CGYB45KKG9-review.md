## Что проверил

Прочитал `openspec/specs/extension-stages/spec.md` целиком, `isolation.py`, `stages.py`, `cli.py` (`complete`, `stage`), `gate.py` (чем судит acceptance), `status_view.py`, `records.py`, ADR‑0013 (решения 5, 6, 7, 8, 17), `templates/journal-transaction.sh`, `docs/quickstart.md` и проверил каждый цитируемый заголовок requirement в specs — все цитаты в диффе существуют дословно (включая `gate-lanes`: «an operational change takes its own gate lane» spec.md:170 и «pre-gate stages do not run on an operational change» spec.md:344, которые дифф цитирует именно как gate‑lanes).

**ADV-FINDINGS-LANE-STAGE-LINE** (advisory, claim-accuracy): в `docs/threat-model.md:259-266` обещание «ровно одна result line на stage» пришито сочинительной связью к предложению про findings lane («The findings lane prints each check it cannot run as not examined with the reason, and every extension stage gets exactly one result line …»), а findings lane вообще не запускает ни одного stage — `openspec/specs/extension-stages/spec.md:1293-1294` («The findings lane (`complete --findings`, which takes no candidate) and the sidecar placement SHALL invoke no stage at all»), подтверждено `tests/test_complete_stages.py:364`. Утверждение само по себе не ложное (второе предложение не приписывает печать этих строк findings lane), но на одном дыхании читается так, будто это её вывод; просится разрыв предложения. Это единственное, что я нашёл — блокирующего нет.

## Как дифф закрывает критерии

**AC1 (threat-model).** Снято и «extension execution decided but not implemented», и «no extension code runs»: `docs/threat-model.md:207-241` теперь говорит, что код расширений исполняется вне gate — `stage run --phase <pre-gate|post-gate>` и тот же прогон внутри `complete` до gate‑проверки и после записи `completed` (код: `cli.py:1109` и `cli.py:1200`), argv‑процесс под интерпретатором ядра в snapshot кандидата, манифесты/switches/код берутся из base, на рабочей станции — только под грантом, в CI — без него, operational lane не запускает `pre-gate` вовсе, а `accepted_pause` снимает pause. Демонстрируют `tests/test_complete_stages.py:155` (`both_commands_go_through_the_one_runner`), `:192`, `:276`, `tests/test_stages.py`. Изоляция описана ровно тем, что ядро реально делает: новый user+network namespace, если не объявлено `network = true` (`isolation.py:396-404`, тест `tests/test_isolation.py:132`); на `pre-gate` bind кандидата сам на себя с `MS_BIND|MS_REMOUNT|MS_RDONLY` плюс залоченные `nosuid`/`nodev`/`noexec`/atime‑флаги из `statvfs` и повторный `chdir` после remount (`isolation.py:283-312`, тесты `:217`, `:282`, `:325`, `:354`); provider‑secret имена не передаются на `pre-gate` даже при `isolation.env` (`stages.py:502`, тесты `:879`, `:920`, `:965`); capabilities сбрасываются перед `execve` (`isolation.py:203-257`, тест `:509`). Что не удалось обеспечить — именуется на отдельной `not enforced` note‑строке, stage всё равно исполняется (`stages.py:575-590`, тесты `:598`, `:635`, `:655`, `:802`); «за пределами кандидата read-only не делается», объявленный `writes` ничем не обеспечен и помечается not enforced (тест `:486`); процесс того же OS‑пользователя вне stage не изолирован — изоляция ставится в собственном ребёнке до `execve` (`docs/threat-model.md:329-337`). Ничего не заявлено как enforced сверх кода; каждое утверждение опирается на названный requirement. Параллельно поправлена запись про record model: `accepted_pause` читает только stage runner (в `gate.py` этого поля нет вовсе), `operational` ничего не допускает — gate судит только acceptance с `findings` (`gate.py:1749-1755`), а вариант «adopter требует operator acceptance для operational CR» (ADR‑0013 решение 17) честно оставлен как decided, not yet implemented.

**AC2 (README).** `README.md:127-128` стало `git add .agentmarshal/journal/tasks/CR-001`, и добавленный абзац `:151-158` объясняет почему и указывает на `templates/journal-transaction.sh` — совпадает с `docs/quickstart.md:322-345` слово в слово по смыслу (включая «`project.json` — housekeeping, не journal evidence»). Поведение шаблона, которое абзац описывает (ровно один каталог задачи, ветка по имени задачи, push, PR оставлен провайдеру, строка `ADAPT`), демонстрирует `tests/test_journal_transaction.py:114` и `:153`.

**AC3 (self-hosting-workflow).** `docs/self-hosting-workflow.md:56-81` документирует `complete --target <ref>` именно так, как работает `cli.py:1004-1035` и `:1118-1135`: пока кандидат не ancestor разрешённого `--target` — отказ, все paused stages одной строкой, exit 3, ничего не записано; когда ancestor — по одной строке `complete: WARNING:` на pause и завершение продолжается; без `--target` или при нерешаемом ref pause остаётся; `--base` остаётся merge base для диффа gate, `--target` — ветка слияния, поэтому wrapper, завершающий после merge, передаёт target. Демонстрируют `tests/test_complete_stages.py:511`, `:538`, `:585`, `:614`.

**AC4.** `openspec/changes/` содержит только `archive/`, каталога `extension-stages-purpose/` нет и в архиве он не появился; дифф не трогает ни одного файла OpenSpec и ни одного документа кроме трёх в scope. Новых ссылок дифф не добавляет; все относительные ссылки в изменённых файлах (`README.md`) резолвятся — проверил существование каждой цели. Полную последовательность CI я не запускал: сессия read‑only, запуск `uv run pytest` не был разрешён; опираюсь на заявление координатора о прохождении на 2cffdc0 — отдельных doc‑тестов в `tests/` нет, поэтому текст документов тестами не покрыт by design.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "2cffdc090e9ffa5158c308d8db9331ad6ace8b20",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-FINDINGS-LANE-STAGE-LINE"],
  "classes": {"ADV-FINDINGS-LANE-STAGE-LINE": "claim-accuracy"},
  "verification": {
    "executed": [
      {"what": "ls openspec/changes openspec/changes/archive", "result": "only archive/ present; no extension-stages-purpose anywhere — AC4 removal holds"},
      {"what": "grep -rn '^### Requirement' over gate-lanes, process-log, leak-scan, review-evidence, extension-records, session-activity, record-schema specs", "result": "every requirement title the diff quotes exists verbatim, including gate-lanes:170 and gate-lanes:344"},
      {"what": "grep -rn 'accepted_pause' src/", "result": "present in stages.py, status_view.py, records.py, cli.py; absent from journal/gate.py — 'read by the stage runner, never by the gate' holds"},
      {"what": "grep -n '\"operational\"' src/agentmarshal/journal/gate.py", "result": "no match; gate.py:1749-1755 filters acceptances by 'findings' in record — neither pause nor operational reaches the verdict checks"},
      {"what": "grep -n 'target' src/agentmarshal/cli.py; read cli.py:1004-1135, 1194-1208", "result": "--target on complete, _candidate_merged via git merge-base --is-ancestor, refusal with joined pauses + exit 3, WARNING per pause when merged, post-gate run after the completed record"},
      {"what": "grep -n 'is_symlink|does not exist' src/agentmarshal/stages.py", "result": "stages.py:551-554 — not run for a symlinked or missing command, as the threat model now states"},
      {"what": "grep -n 'fallback_reason' src/", "result": "records.py:522 registers ('session','fallback_reason') under _FORGEABLE_TEXT_FIELDS; status_view.py:419-424 prints it"},
      {"what": "grep -o '](...)' over the three changed docs and existence check of each target", "result": "all relative link targets exist; the diff adds no new link"},
      {"what": "grep -rn 'not yet implemented' README.md docs/overview.md docs/quickstart.md docs/known-defects.md SECURITY.md", "result": "no stale extension-execution claim left outside the threat model"}
    ],
    "read": [
      "openspec/specs/extension-stages/spec.md (full)",
      "src/agentmarshal/isolation.py (full)",
      "src/agentmarshal/stages.py (480-600, register)",
      "src/agentmarshal/cli.py (340-365, 1000-1210)",
      "src/agentmarshal/journal/gate.py (1740-1790)",
      "src/agentmarshal/journal/status_view.py (130-200, 760-780)",
      "src/agentmarshal/journal/records.py (490-540)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decisions 5, 6, 7, 8, 17)",
      "docs/threat-model.md (80-112, 174-280, 320-345, 396-470, 515-545)",
      "docs/self-hosting-workflow.md (30-90)",
      "README.md (110-175)",
      "docs/quickstart.md (310-345)",
      "templates/journal-transaction.sh",
      "openspec/specs/session-activity/spec.md (58-100)",
      "openspec/specs/operator-acceptance/spec.md (48-130)",
      "tests/test_isolation.py, tests/test_complete_stages.py, tests/test_journal_transaction.py (test names)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review and the sandbox refused the uv invocation; relying on the coordinator's statement that the sequence passed on 2cffdc0"}
    ]
  },
  "evidence": {
    "ADV-FINDINGS-LANE-STAGE-LINE": "docs/threat-model.md:259-266 joins the stage result-line vocabulary to the findings-lane clause, while openspec/specs/extension-stages/spec.md:1293-1294 says the findings lane and the sidecar invoke no stage at all (tests/test_complete_stages.py:364 test_the_findings_lane_invokes_no_stage)"
  }
}
AGENTMARSHAL_VERDICT_END
