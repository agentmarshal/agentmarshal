Проверил весь diff построчно против кода, спеков и ADR. Ниже — что сошлось, и одна необязательная придирка.

## Advisory

**ADV-RESULT-LINE-001** — `docs/threat-model.md:239` утверждает безусловно «Every extension stage gets exactly one result line», но в `src/agentmarshal/stages.py:1097-1103` ветка `elif grants_unreadable: … continue` не печатает result line ни для одной stage, которая подлежала бы grant-проверке, когда `trust.toml` клона не читается — строку получают только switched-off stages и те, что назвал нечитаемый switches-файл. Формулировка дословно повторяет заголовок требования спека (`openspec/specs/extension-stages/spec.md:313`), а оговорку держит соседнее требование (`:286`, сценарий на `:311` — «no stage is planned»), так что расхождение унаследовано из спека; по критерию «each statement checked against the code» хватило бы одной уточняющей клаузы в threat model, править спек этот контракт не разрешает. Не блокирует.

## Как критерии закрыты

**AC1 — threat model говорит, что реально выполняется.** Маркер «decided, not yet implemented» снят ровно там, где extension execution уже есть: `docs/threat-model.md:177-181` (stage runner существует), `:207-254` (`stage run`/`complete` гоняют `[[stage]]`-записи — ключ действительно `stage`, `journal/extensions.py:220`; argv `[sys.executable, command]`, `stages.py:564`; база — `_base_extensions(project_root, merge_base)`, `:860`; grant на workstation и ничего в CI — `:944`, `_prepare_extension` `:447-465`; operational lane не гоняет pre-gate — `:820-859`; findings lane и sidecar не вызывают ни одной stage — `cli.py:1068` плюс `stages.py:806`), `:418-446` (изоляция). Все восемь пунктов про изоляцию сверены с `isolation.py`: user+net namespace при отсутствии `network = true` (`stage_setup`/`_setup:396-404`, `_run_stage:576`), pre-gate read-only bind с сохранением locked-флагов и повторным `chdir` (`_bind_read_only:293-312`, `_LOCKED_FLAG_MAP:273`), withholding provider-secrets (`_stage_env:502`, `_is_provider_secret:171`), сброс capabilities до `execve` (`_drop_capabilities:203`), `not enforced`-нота на незаэнфорсенное (`stages.py:1157-1170`), «nothing outside the candidate is made read-only» (bind только на `snapshot`), «процесс того же OS-пользователя вне stage не защищён» (`:339-346`). Каждая цитата спека резолвится в реальный заголовок требования (проверил все 20+). Демонстрируют: `tests/test_isolation.py::test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces`, `::test_a_pre_gate_stage_s_candidate_directory_is_bound_read_only_over_itself`, `::test_the_read_only_remount_keeps_the_flags_the_candidate_s_mount_locks`, `::test_the_child_re_enters_the_candidate_after_the_read_only_remount`, `::test_a_provider_secret_named_in_isolation_env_is_withheld_at_pre_gate`, `::test_drop_capabilities_clears_every_capability_set`, `::test_each_guarantee_not_enforced_is_named_on_one_note_line_for_the_stage`, `::test_a_declared_writes_beyond_the_candidate_is_reported_as_not_enforced`, `::test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate`; плюс `tests/test_stages.py`, `tests/test_gate_operational.py`, `tests/test_pause_and_operational_acceptance.py`. Ничего не заявлено как enforced сверх кода; `accepted_pause` и `operational` правда не доходят до gate — оба фильтра требуют `"findings" in record` (`journal/gate.py:206`, `:1753`).

**AC2 — README стейджит один task-каталог.** `README.md:128` теперь `git add .agentmarshal/journal/tasks/CR-001`, проза на `:152-159` совпадает с `docs/quickstart.md:324-344` (в т.ч. про `project.json` как housekeeping), и `git add .agentmarshal` в README больше нигде нет. Утверждения о шаблоне верны: `templates/journal-transaction.sh:66-71` берёт ровно `.agentmarshal/journal/tasks/$task`, `:116-122` — ветка по task id и `git push`, `:128` — помеченная строка `ADAPT` для pull request. Демонстрирует `tests/test_quickstart.py` (прогоняет governed loop дословно, та же транзакция `docs/quickstart.md:332`) и `tests/test_journal_transaction.py` для шаблона; сам fenced-блок README ни одним тестом не исполняется — консистентность с quickstart тут и есть вся проверка.

**AC3 — `complete --target` задокументирован.** `docs/self-hosting-workflow.md:56-80` описывает всё, что делает код: pre-gate до gate-check и post-gate после записи `completed`, не меняющий ни запись, ни exit status (`cli.py:1109-1118`, `:1193-1209`); пауза при `pre-gate-stop` и роль `--target` (`:1119-1136`), одна строка со всеми паузами и exit 3 без записи, `complete: WARNING:` на уже влитом кандидате; «без `--target` или при нерезолвящемся target пауза стоит» — ровно `_candidate_merged` `:1034-1035`; `--base` остаётся merge base, `--target` — ветка влития (`:1012-1014`). Демонстрируют `tests/test_complete_stages.py::test_a_pause_while_the_candidate_is_not_an_ancestor_refuses_the_completion`, `::test_the_pause_line_names_every_paused_stage`, `::test_a_pause_on_an_already_merged_candidate_is_a_warning`, `::test_an_accepted_pause_stands_down_in_complete_as_in_stage_run`, `::test_the_post_gate_stages_run_after_the_completed_record_is_written`, `::test_a_post_gate_result_changes_neither_the_record_nor_the_exit_status`.

**AC4 — change удалён, OpenSpec не тронут, ссылки живые.** `openspec/changes/` содержит только `archive/`, `extension-stages-purpose/` отсутствует и в архив не положен (в `archive/` его нет); diff меняет ровно три документа из scope; все относительные ссылки README резолвятся (`docs/adr/ADR-0004-…`, `ADR-0005-…`, `docs/overview.md`, `docs/README.md`, `docs/quickstart.md`, `docs/self-hosting-workflow.md`, `docs/github-enforcement.md`, `docs/sidecar.md`, `docs/migration-v1-to-v2.md`), в threat-model и self-hosting новых ссылок нет вовсе. Поправка контракта (снятие Purpose-критерия) согласуется с тем, что в diff нет ни одного изменения под `openspec/`. Полную CI-последовательность в этой песочнице запустить не дали (pytest требует approval) — опираюсь на заявление координатора о 77c7b2b.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "77c7b2b2877e51dc1e1fdad767101e5718d91def",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-RESULT-LINE-001"],
  "classes": {
    "ADV-RESULT-LINE-001": "claim-accuracy"
  },
  "verification": {
    "read": [
      "docs/threat-model.md (whole)",
      "docs/self-hosting-workflow.md (whole)",
      "README.md:100-180",
      "docs/quickstart.md:250-370",
      "src/agentmarshal/isolation.py (whole)",
      "src/agentmarshal/stages.py (whole)",
      "src/agentmarshal/journal/complete.py (whole)",
      "src/agentmarshal/cli.py:1000-1230",
      "src/agentmarshal/journal/gate.py:190-215, 1745-1800",
      "src/agentmarshal/journal/status_view.py:125-150, 410-430",
      "src/agentmarshal/journal/records.py:195-225, 510-530, 830-850",
      "openspec/specs/extension-stages/spec.md:164-200, 276-350, 879-1113, 1273-1433",
      "openspec/specs/gate-lanes/spec.md (requirement index)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:82-135, 269-300",
      "templates/journal-transaction.sh:1-130"
    ],
    "executed": [
      {
        "what": "grep -n '### Requirement' over extension-stages, gate-lanes, leak-scan, extension-records, process-log, record-schema, review-evidence, session-activity specs",
        "result": "every requirement title the diff quotes resolves verbatim, including 'a stage with no declared network runs in a new user and network namespace', 'a pre-gate stage's candidate is bound read-only over itself', 'a guarantee the core cannot enforce is named, never silently weakened', 'a pre-gate-stop pause refuses complete only while the candidate is not merged', 'pre-gate stages do not run on an operational change', 'record-check writes a check record for a resolved commit', 'A session record can say what it produced and with what', 'Shared field validators apply from schema 7'"
      },
      {
        "what": "ls openspec/changes; ls openspec/changes/archive; ls -d openspec/changes/extension-stages-purpose",
        "result": "openspec/changes holds only archive/; extension-stages-purpose is absent (ls: No such file or directory) and does not appear under archive/"
      },
      {
        "what": "grep -n 'git add' README.md docs/quickstart.md",
        "result": "README.md:128 'git add .agentmarshal/journal/tasks/CR-001'; no 'git add .agentmarshal' remains; quickstart.md:332/356/511/564 use the same per-task form"
      },
      {
        "what": "grep -n 'fallback_reason' src/; grep -rn 'not a declared actor' src/",
        "result": "records.py:522 registers ('session','fallback_reason') in _FORGEABLE_TEXT_FIELDS; status_view.py:419-424 prints it; status_view.py:141 appends ' (not a declared actor)'"
      },
      {
        "what": "grep -n 'acceptance' src/agentmarshal/journal/gate.py",
        "result": "both acceptance filters (gate.py:206 and gate.py:1753) require \"findings\" in record, so accepted_pause and operational records reach no gate check"
      },
      {
        "what": "grep -n 'stages\\|\"stage\"' src/agentmarshal/journal/extensions.py",
        "result": "extensions.py:220 reads data.get('stage') as an array of tables, so the threat model's '[[stage]]' names the real key"
      },
      {
        "what": "grep -o on relative markdown links in the three changed files",
        "result": "only README.md carries relative links; all nine targets exist on disk; threat-model.md and self-hosting-workflow.md add none"
      }
    ],
    "not_run": [
      {
        "what": "python -m pytest (test_complete_stages.py, test_isolation.py, test_quickstart.py)",
        "why": "the sandbox refused the command without approval; the coordinator states the full CI sequence passed on 77c7b2b, and the named tests were read rather than executed"
      },
      {
        "what": "uv run agentmarshal validate / ruff / mypy",
        "why": "same approval refusal; no git repository in the snapshot either"
      }
    ]
  },
  "evidence": {
    "ADV-RESULT-LINE-001": "docs/threat-model.md:239 'Every extension stage gets exactly one result line' vs src/agentmarshal/stages.py:1097-1103 ('elif grants_unreadable: ... continue' — no result line for a stage that would have been grant-checked); the spec's own carve-out is openspec/specs/extension-stages/spec.md:286 ('A trust.toml the grants reader refuses SHALL fail the command naming the file') with the scenario at :311 ('the command fails naming the file and no stage is planned'), while the restated requirement title is at :313"
  }
}
AGENTMARSHAL_VERDICT_END
