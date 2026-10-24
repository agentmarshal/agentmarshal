Разобрал диффы, прогнал заявления из документов по коду и спекам. Код не менялся — изменены только три документа, как требует scope.

## Что проверял по коду

**Критерий 1 — `docs/threat-model.md`.** Выполнен. Строки 207–271 теперь говорят, что extension code исполняется: `stage run --phase pre-gate|post-gate` и `complete` запускают `[[stage]]` записи shared-манифестов (`src/agentmarshal/stages.py:758`, `cli.py:1109` и `cli.py:1200`), код и switches берутся с base (`stages.py:860`, `stages.py:890`), на workstation — только под grant с per-file хешами base-материализованной директории, в CI — без (`stages.py:944`, `stages.py:447`–`456`); operational lane не запускает ни одного `pre-gate` stage (`stages.py:820`-`859`), а accepted pause снимается суффиксом `pause accepted by <party> (<reason>)` (`stages.py:1152`). Перечень result-линий (`checked`, `failed (exit <n>)`, `did not finish (timeout)`, `not run (<reason>)`, `switched off (<task>, <reason>)`) совпадает с `_result_text` (`stages.py:723`). Isolation-параграф (строки 437–465) сходится с `isolation.py`: новый user+network namespace, если манифест не объявил `network = true` (`stages.py:576`), на `pre-gate` bind поверх себя с remount read-only и сохранением locked-флагов (`nosuid/nodev/noexec/atime`) из `statvfs` плюс повторный `chdir` (`isolation.py:_bind_read_only`, `_LOCKED_FLAG_MAP`), withholding provider-secret имён даже при `isolation.env` (`stages.py:502`), drop всех capabilities перед `execve` (`isolation.py:_drop_capabilities`); что не удалось — на отдельной строке `not enforced` (`stages.py:1162`), вне кандидата read-only не делается, и процесс того же OS-пользователя вне stage не изолирован (строки 358–361). Ни одно из цитируемых требований не выдумано — все имена requirement'ов существуют в `openspec/specs/{extension-stages,gate-lanes,process-log,extension-records,leak-scan,review-evidence,session-activity,record-schema}/spec.md`, и то, что осталось «decided, not yet implemented» (`addressee not found` как stage-линия и `not run` по lock'у зависимостей, строка 261–266), в коде действительно отсутствует: `grep` по `stages.py` даёт только `changed after approval`, а `addressee not found` живёт в `journal/validate.py:190`. Демонстрируют: `tests/test_isolation.py::test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces`, `::test_the_read_only_remount_keeps_the_flags_the_candidate_s_mount_locks`, `::test_the_child_re_enters_the_candidate_after_the_read_only_remount`, `::test_a_provider_secret_named_in_isolation_env_is_withheld_at_pre_gate`, `::test_drop_capabilities_clears_every_capability_set`, `::test_each_guarantee_not_enforced_is_named_on_one_note_line_for_the_stage`, `tests/test_stages.py::test_every_stage_gets_exactly_one_result_line`, `tests/test_switches.py::test_a_malformed_trust_file_still_reports_the_switched_off_line` и `::test_a_malformed_switches_file_and_trust_file_still_report_the_named_stages` (последние два подтверждают «один случай оставляет stage без линии»).

**Критерий 2 — `README.md`.** Выполнен: рецепт на строке 128 ставит `git add .agentmarshal/journal/tasks/CR-001`, единственный `git add .agentmarshal` исчез, формулировка совпадает с `docs/quickstart.md:332`; шаблон `templates/journal-transaction.sh` действительно ставит ровно эту директорию литеральным pathspec, коммитит на ветке с id таска, пушит и оставляет PR провайдеру (ADAPT-строка в конце файла). Демонстрируют: `tests/test_journal_transaction.py::test_the_transaction_takes_only_its_own_tasks_journal_directory` и `::test_the_push_goes_to_the_remote_am_remote_names`.

**Критерий 3 — `docs/self-hosting-workflow.md`.** Выполнен: строки 56–80 описывают именно то, что делает код — отказ с exit 3 и одной строкой с паузами, пока кандидат не ancestor разрешённого `--target` (`cli.py:1119`-`1136`), по одной `complete: WARNING:` на паузу после мерджа (`cli.py:1123`-`1129`), «пауза стоит» при отсутствующем или неразрешимом target (`_candidate_merged` возвращает `False` на `GateError`/`OSError`, `cli.py:1034`), `--base` остаётся merge base (`cli.py:1106`-`1114`), post-gate — уведомление после записи `completed`, не меняющее ни запись, ни exit status (`cli.py:1193`-`1209`). Демонстрируют: `tests/test_complete_stages.py::test_a_pause_while_the_candidate_is_not_an_ancestor_refuses_the_completion`, `::test_the_pause_line_names_every_paused_stage`, `::test_a_pause_on_an_already_merged_candidate_is_a_warning`, `::test_an_accepted_pause_stands_down_in_complete_as_in_stage_run`, `::test_a_post_gate_result_changes_neither_the_record_nor_the_exit_status`.

**Критерий 4.** Выполнен частично-проверяемо: `openspec/changes/` содержит только `archive/`, `extension-stages-purpose/` отсутствует и в архив не попал (нет записи `*purpose*` в `openspec/changes/archive/`), ни один файл под `openspec/` не изменён, диффом затронуты только три документа, новых markdown-ссылок не добавлено (упоминание шаблона — inline code, не ссылка), `templates/journal-transaction.sh` на месте. Отдельного теста на этот критерий нет и быть не должно. Полную CI-последовательность я не запускал — в снапшоте нет `.git` и venv, `uv sync --locked` требует сети; опираюсь на заявление координатора о прохождении CI на 127cfab.

## Findings (оба не блокирующие)

ADV-STYLE-001 — в `docs/threat-model.md` правки оставили рваную ручную перевёрстку абзацев: строка 182 это одинокое `(extension-manifest`, строки 292–293 разрывают список ссылок как `reason. (ADR-0006, decision 2;` / `ADR-0008,`, строка 488 — `declares"). The`; остальной документ свёрстан ровными ~72 колонками, так что это след редактирования, а не стиль файла.

ADV-DOC-002 — новый абзац `README.md:154`-`156` называет housekeeping только `.agentmarshal/project.json`, тогда как `init` создаёт ещё и `.agentmarshal/upstream/` с README (`src/agentmarshal/project.py:446`, `_scaffold_outbox`), и параллельное место в `docs/quickstart.md:326`-`328` называет оба («`.agentmarshal/project.json` и outbox»); утверждение не ложное, но читатель, идущий только по README, не узнаёт, что после `init` остаётся несмерженным ещё и outbox.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "127cfab49f6b8a23a104f4e677c09a06e16160eb",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-STYLE-001", "ADV-DOC-002"],
  "classes": {
    "ADV-STYLE-001": "style",
    "ADV-DOC-002": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n '^### Requirement' over openspec/specs/{extension-stages,gate-lanes,process-log,extension-records,leak-scan,review-evidence,session-activity,record-schema}/spec.md", "result": "every requirement name the three documents cite exists verbatim; none invented"},
      {"what": "ls openspec/changes/ and ls openspec/changes/archive/ | grep -i purpose", "result": "only archive/ remains; no extension-stages-purpose entry, archived or not"},
      {"what": "grep -rn 'decided, not yet implemented' docs/*.md README.md CONTRIBUTING.md SECURITY.md", "result": "only docs/threat-model.md, at the legend (13), next (198, 205, 569), ADR-0013 d7 leftovers (264) and the operational-acceptance variant (107)"},
      {"what": "grep -rn 'changed after approval|lock|dependenc' src/agentmarshal/stages.py; grep -rn 'addressee not found' src/", "result": "no dependency-lock not-run reason and no addressee-not-found stage line in the runner; the phrase lives in journal/validate.py:190"},
      {"what": "grep -rn 'git add' README.md docs/*.md", "result": "README.md:128 and quickstart.md:332/356/511/564 all stage .agentmarshal/journal/tasks/CR-001; no git add .agentmarshal left"},
      {"what": "grep -n 'def test' tests/test_isolation.py tests/test_stages.py tests/test_switches.py tests/test_complete_stages.py tests/test_journal_transaction.py", "result": "named tests exist for each documented behaviour"}
    ],
    "read": [
      "docs/threat-model.md (1-45, 80-110, 160-210, 276-300, 300-370, 425-495, 540-575)",
      "README.md (100-180)",
      "docs/self-hosting-workflow.md (1-110)",
      "src/agentmarshal/isolation.py (whole file)",
      "src/agentmarshal/stages.py (380-760, 756-1219)",
      "src/agentmarshal/cli.py (340-370, 1000-1210)",
      "src/agentmarshal/journal/records.py (195-220, 510-545, 830-850)",
      "src/agentmarshal/journal/gate.py (190-215, 1745-1775, 2150-2170)",
      "src/agentmarshal/journal/status_view.py (136-142, 183-191, 419-424, 765-775)",
      "src/agentmarshal/project.py (230-250, 290-330, 393-447)",
      "templates/journal-transaction.sh",
      "openspec/specs/extension-stages/spec.md (276-355, 1273-1360)",
      "openspec/specs/record-schema/spec.md (165-205)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (82-135, 245-290)",
      "docs/adr/ADR-0014-where-things-live.md (165-185)",
      "docs/quickstart.md (300-360)",
      "tests/test_stages.py (1129-1150)",
      "tests/test_complete_stages.py (test list)",
      "tests/test_isolation.py (test list)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the review snapshot has no .git and no virtualenv, and uv sync --locked needs network; relying on the coordinator's statement that the full sequence passed on 127cfab49f6b8a23a104f4e677c09a06e16160eb"}
    ]
  },
  "evidence": {
    "ADV-STYLE-001": "docs/threat-model.md:182 ('(extension-manifest' alone), docs/threat-model.md:292-293 ('reason. (ADR-0006, decision 2;' / 'ADR-0008,'), docs/threat-model.md:488 ('declares\"). The') against the file's otherwise even ~72-column wrap",
    "ADV-DOC-002": "README.md:154-156 names only project.json; src/agentmarshal/project.py:446 calls _scaffold_outbox (project.py:298-330) which creates .agentmarshal/upstream/README.md; docs/quickstart.md:326-328 names '.agentmarshal/project.json and the outbox'"
  }
}
AGENTMARSHAL_VERDICT_END
