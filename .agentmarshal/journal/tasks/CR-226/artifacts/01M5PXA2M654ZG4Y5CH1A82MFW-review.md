Проверил diff против кода, спеков, ADR и соседних документов (`git` в снапшоте недоступен, так что сверялся с состоянием файлов на ревьюируемом коммите).

## Что по критериям приёмки

**AC1 — threat-model описывает то, что реально выполняется.** Выполнен. Абзац «No extension can change the gate's decision» (`docs/threat-model.md:207-242`) больше не говорит «no extension code runs today»: он называет `stage run --phase pre-gate|post-gate` и запуск того же runner'а из `complete` — это ровно `src/agentmarshal/stages.py:229-247` и `src/agentmarshal/cli.py:1109-1118`, `cli.py:1200-1209`; демонстрируют `tests/test_stages.py::test_pre_gate_invokes_the_pre_gate_warn_and_pre_gate_stop_stages` и `tests/test_complete_stages.py::test_both_commands_go_through_the_one_runner`. Код и switches с базы — `stages.py:336-370` (`_materialize_directory` от `merge_base`), тест `tests/test_stages.py::test_the_base_commits_code_runs_not_the_candidates_or_the_working_trees`; grant на workstation и его отсутствие в CI — `stages.py:447-465`, тесты `::test_no_grant_on_a_workstation_is_not_run` и `::test_in_ci_no_grant_is_needed`. Изоляция описана ровно так, как её делает код: user+net namespace, если не объявлен `network = true` (`isolation.py:396-404`, тест `tests/test_isolation.py::test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces`); read-only bind с сохранением locked-флагов и повторным входом в каталог (`isolation.py:273-312`, тесты `::test_the_read_only_remount_keeps_the_flags_the_candidate_s_mount_locks`, `::test_the_child_re_enters_the_candidate_after_the_read_only_remount`); withholding provider-secret на `pre-gate` (`stages.py:497-514`, тест `::test_a_provider_secret_named_in_isolation_env_is_withheld_at_pre_gate`); drop capabilities до `execve` (`isolation.py:203-257`, тест `::test_drop_capabilities_clears_every_capability_set`); note-строка «not enforced» (`stages.py:1157-1170`, тест `::test_each_guarantee_not_enforced_is_named_on_one_note_line_for_the_stage`); «ничего вне candidate не делается read-only» и неконтейнеризованный процесс того же OS-пользователя (`docs/threat-model.md:431-437`, тест `::test_a_declared_writes_beyond_the_candidate_is_reported_as_not_enforced`). Все 25+ цитируемых имён требований существуют буквально — проверил grep'ом по `openspec/specs/*/spec.md` (включая спорное на вид `gate-lanes` → `pre-gate stages do not run on an operational change`, оно действительно в `gate-lanes/spec.md:344`). Переформулировки «decided, not yet implemented» тоже честные: `next` в CLI нет, adopter-kit implementer-launch шаблона в `templates/` нет.

**AC2 — README стейджит журнал одной задачи.** Выполнен: `README.md:126-127` и прозаический абзац `README.md:152-160`; формулировка совпадает с `docs/quickstart.md:322-334`, `open` пишет только под `tasks/<id>` (`src/agentmarshal/journal/open_task.py:383-403`), так что узкий `git add` достаточен; поведение шаблона демонстрирует `tests/test_journal_transaction.py::test_the_transaction_takes_only_its_own_tasks_journal_directory`, а наличие ADAPT-строки, ветки по задаче и push'а — сам `templates/journal-transaction.sh`.

**AC3 — `complete --target` документирован.** Выполнен: `docs/self-hosting-workflow.md:56-82` описывает refuse/exit 3 до записи, переход в `complete: WARNING:` после merge, «pause стоит» без `--target` или при неразрешимом ref — это `cli.py:1004-1036` и `cli.py:1119-1136`; демонстрируют `tests/test_complete_stages.py::test_a_pause_while_the_candidate_is_not_an_ancestor_refuses_the_completion`, `::test_a_pause_on_an_already_merged_candidate_is_a_warning`, `::test_an_accepted_pause_stands_down_in_complete_as_in_stage_run`; разграничение `--base`/`--target` совпадает с docstring'ом `_candidate_merged` и help'ом парсера (`cli.py:352-356`).

**AC4 — удаление change'а, никаких OpenSpec-правок, ссылки, CI.** Выполнен по состоянию: `openspec/changes/` содержит только `archive`, то есть `extension-stages-purpose/` отсутствует (в присланном diff самого удаления не видно — проверил по снапшоту, не по истории). Diff трогает только три документа, OpenSpec-файлы не меняются, новых markdown-ссылок нет (`templates/journal-transaction.sh` упомянут в backticks и существует). Полную CI-последовательность я не запускал — опираюсь на твою справку о коммите 2cffdc0.

## Замечания (все неблокирующие)

ADV-RESULT-LINE-LANE: в `docs/threat-model.md:257-272` строка результата стадии («checked / failed (exit n) / …») вставлена в абзац про вывод гейта, сразу после предложения о findings-lane, хотя печатает её `stage run`/`complete` (`stages.py:1148-1156`), а не гейт — рядом стоящее утверждение «nothing extension-defined runs inside the gate» читается с ней как противоречие; стоит явно назвать, чья это строка.

ADV-WRITES-NOTE-CONDITION: `docs/threat-model.md:431-434` описывает note «writes beyond the candidate» как следствие объявленного `writes` (так же, как сценарий спеки `extension-stages/spec.md:1023`), но код добавляет этот note при любом манифесте с таблицей `isolation`, даже без ключа `writes` (`stages.py:584-590`) — расхождение в коде/спеке, но текст документа лучше сформулировать по факту.

ADV-NO-CITATION-TEST: ни один тест не фиксирует цитаты документов — `tests/` ссылается на openspec только в docstring'ах, `agentmarshal validate` проверяет журнал, а не документы (в отличие от `docs/quickstart.md`, чьи блоки исполняет `tests/test_quickstart.py`), так что переименование требования в спеке молча сделает ~25 новых ссылок в threat-model недействительными.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "2cffdc090e9ffa5158c308d8db9331ad6ace8b20",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-RESULT-LINE-LANE", "ADV-WRITES-NOTE-CONDITION", "ADV-NO-CITATION-TEST"],
  "classes": {
    "ADV-RESULT-LINE-LANE": "claim-accuracy",
    "ADV-WRITES-NOTE-CONDITION": "claim-accuracy",
    "ADV-NO-CITATION-TEST": "test-gap"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn '^### Requirement' over openspec/specs/{extension-stages,gate-lanes,leak-scan,process-log,extension-records,record-schema,review-evidence,session-activity}/spec.md, matched against every requirement name quoted in the diff", "result": "every quoted name exists verbatim, including gate-lanes:344 'pre-gate stages do not run on an operational change' and extension-stages:313/476 for the result-line vocabulary"},
      {"what": "grep for the behaviours the new text asserts: 'not a declared actor', 'addressee not found', fallback_reason, operational acceptance, writes-note", "result": "status_view.py:141, validate.py:190, status_view.py:419-424, status_view.py:772-773, stages.py:584-590 — all present"},
      {"what": "ls openspec/changes/ and ls templates/", "result": "openspec/changes/ holds only archive/ (extension-stages-purpose removed); templates/journal-transaction.sh present with the ADAPT marker"},
      {"what": "grep -rn 'not yet implemented|no extension code' over README.md, SECURITY.md, docs/overview.md, docs/quickstart.md, docs/README.md, docs/known-defects.md, docs/self-hosting-workflow.md", "result": "no hits — no stale companion claim left behind"}
    ],
    "read": [
      "docs/threat-model.md (whole)",
      "README.md:100-175",
      "docs/self-hosting-workflow.md:1-110",
      "docs/quickstart.md:300-350",
      "src/agentmarshal/isolation.py (whole)",
      "src/agentmarshal/stages.py:225-740, 1025-1219",
      "src/agentmarshal/cli.py:340-360, 995-1210",
      "src/agentmarshal/journal/gate.py:185-215, 645-700",
      "src/agentmarshal/journal/open_task.py:377-403",
      "openspec/specs/extension-stages/spec.md (requirement index, 313-350, 1018-1040)",
      "openspec/specs/gate-lanes/spec.md:170-245",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:113-133, 243-290",
      "templates/journal-transaction.sh",
      "tests/test_isolation.py, tests/test_stages.py, tests/test_complete_stages.py, tests/test_journal_transaction.py, tests/test_quickstart.py (test name inventories)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; the coordinator states the full sequence passed on the reviewed commit"},
      {"what": "end-to-end execution of the README recipe in a scratch git repository", "why": "running a script in the sandbox required an approval that was declined; verified statically instead (open writes only under tasks/<id>, markers_from_tree treats an absent project.json as no markers)"},
      {"what": "git-level confirmation that this commit is the one that deleted openspec/changes/extension-stages-purpose/", "why": "the snapshot is not a git repository and the supplied diff shows no deletion; only the end state could be checked"}
    ]
  },
  "evidence": {
    "ADV-RESULT-LINE-LANE": "docs/threat-model.md:257-272 places the stage result-line vocabulary in the gate-output paragraph; the lines are printed by the stage runner at src/agentmarshal/stages.py:1148-1156, and the same document states at docs/threat-model.md:207-209 that nothing extension-defined runs inside the gate",
    "ADV-WRITES-NOTE-CONDITION": "docs/threat-model.md:431-434 ties the note to a declared writes, as does openspec/specs/extension-stages/spec.md:1023 ('WHEN a stage runs whose manifest declares isolation.writes'); src/agentmarshal/stages.py:584-590 appends ('writes beyond the candidate', ...) whenever manifest.isolation is not None",
    "ADV-NO-CITATION-TEST": "grep -rln openspec tests/ returns only docstring references (tests/test_stages.py, tests/test_isolation.py, …); no test reads docs/threat-model.md or docs/self-hosting-workflow.md, while tests/test_quickstart.py:18-28 does execute docs/quickstart.md's blocks"
  }
}
AGENTMARSHAL_VERDICT_END
