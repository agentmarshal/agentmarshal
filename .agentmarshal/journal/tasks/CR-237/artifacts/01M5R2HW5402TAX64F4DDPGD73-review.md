Прочитал контракт, ADR-0007, дельту, архивированный spec и весь код трёх surface'ов. Ниже — две находки и разбор по каждому acceptance criterion.

**SA-1 (blocking, contract-mismatch).** `gate` и `report` сравнивают `accepted_by` с **разными** множествами writer'ов, поэтому на многокоммитном candidate они расходятся. `src/agentmarshal/journal/gate.py:1841` берёт identities по всему диапазону `merge_base..candidate` (`_range_writer_identities`), а `src/agentmarshal/journal/report.py:534` (`_self_accepted`) — только по самому accepted commit (`declared_commit_writers`). Конкретный отказ: диапазон `B..C2`, где `C1` написал `alice@x`, а `C2` — `bob@x`; review `C2` = changes_required F-1; `accept --commit C2 --by alice@x`; `completed C2`. Гейт напечатает `PASS: accepted over findings F-1 by alice@x (self-accepted: …)`, а `report` — `decision=accepted-over-findings` **без** `self-accepted`. Это прямо противоречит требованию, которое сама же дельта и записала — `openspec/specs/operator-acceptance/spec.md:316-323`: «Where an acceptance's `accepted_by` matches a declared writer **of the candidate** … the gate's acceptance line SHALL carry … **and** `report`'s task line a tab-separated `self-accepted` field» — и AC1 («…и `report`'s line for the task carries the same mark»), и ADR-0007 decision 4 («every surface that reports the task says so»). Case не покрыт ни одним тестом: все gate-тесты в новом файле держат ровно один коммит в диапазоне (`_gate_repo` + один `_implement`), а единственный двухкоммитный (`test_the_gate_runs_over_an_author_name_that_is_not_utf8`) подобран так, что `worker@test.invalid` — writer обоих коммитов. Чинить надо в одну сторону: либо гейт сужает сравнение до accepted commit (тогда три surface'а совпадают со status), либо требование в spec переписывается на «declared writer of the accepted commit» для `report` и `status` — но тогда AC1 и decision 4 не выполнены как написаны.

**SA-2 (advisory, claim-accuracy).** Docstring в `tests/test_self_acceptance_on_every_surface.py:255` (`test_the_gate_runs_over_an_author_name_that_is_not_utf8`) утверждает «the surviving email half of the identity still earns the mark». Тест этого не показывает: `_implement_latin1_author` ставит переписанный коммит поверх коммита от `_implement`, а тот уже написан `Worker <worker@test.invalid>` (`tests/test_gate.py:42,99`), так что `worker@test.invalid` попадает в identities из родительского коммита независимо от того, как декодировалось `%ae` latin-1-коммита. Сам тест (гейт не падает на не-UTF-8 имени автора) валиден — неверна только вторая половина утверждения.

По критериям:

- **AC1** — выполнен для гейта: `test_the_gates_acceptance_line_marks_a_self_acceptance` (+ committer-вариант) пинит строку `… by <party> (self-accepted: accepting party is a declared author or committer); not an approving review`, а `SELF_ACCEPTED_MARK` (`report.py:44`) байт-в-байт совпадает с тем, что печатал `status_view`. Для `report` выполнен только в узком случае — `test_reports_task_line_marks_a_self_acceptance` (party = автор/коммиттер самого accepted commit); случай writer'а диапазона не выполнен — SA-1.
- **AC2** — выполнен. `test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved` показывает `decision=approved` при acceptance на более раннем коммите, `test_a_commit_approved_after_its_own_acceptance_reports_approved` — приоритет последнего review на том же коммите, `test_a_commit_completed_over_findings_reports_accepted_over_findings` и `test_a_finding_completed_over_findings_reports_accepted_over_findings` — сегодняшнее поведение при закрытии над findings, `test_a_review_written_after_the_completion_does_not_change_its_decision` — срез `records[:completed_index]`, `test_a_task_with_no_completed_record_keeps_todays_decision_rule` — старое правило без `completed`.
- **AC3** — выполнен. Дельта несёт MODIFIED «Readers keep acceptance over findings…» с полным текущим текстом, заголовком и всеми шестью сценариями (сверил с `openspec/specs/operator-acceptance/spec.md:119-168` — совпадает, изменился только WHEN сценария «every output … is unchanged»), плюс два ADDED-требования; других требований с byte-for-byte output clause, которых касается метка, в capability нет (grep по `openspec/specs/` даёт только этот файл). Каждый сценарий назван в docstring теста: одиннадцать в `tests/test_self_acceptance_on_every_surface.py`, шесть прежних в `tests/test_pause_and_operational_acceptance.py:378,418,493,573,628,656,713`. Архив лежит в `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/`, `openspec/changes/` пуст.
- **AC4** — выполнен в проверяемой статически части. `test_an_acceptance_by_another_party_prints_unmarked` пинит и gate-строку, и report-строку без метки; `test_every_output_for_an_acceptance_over_findings_is_unchanged` — status record line; `tests/test_display.py::test_a_refused_character_prints_escaped_in_report` — экранирование (`_task_report(status, None)`); метка в обоих surface'ах — константа, в f-string подставляется пустая строка, так что non-self-acceptance байт-в-байт тот же. Transcript-фикстуры в `tests/fixtures/gate/` acceptance-строк не содержат, поэтому их и не трогали. Прохождение полного CI я не проверял — беру как факт координатора.

Отдельно отмечу (не находка): изменения двух существующих тестов в `test_pause_and_operational_acceptance.py` покрытие не теряют — status-метка self-acceptance для findings-формы по-прежнему закреплена в `test_status_view.py:283` и `test_acceptance.py:199`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9279604c58c939a80af405b6e24963f1456f39a2",
  "verdict": "changes_required",
  "findings": ["SA-1"],
  "advisory_findings": ["SA-2"],
  "classes": {
    "SA-1": "contract-mismatch",
    "SA-2": "claim-accuracy"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/gate.py (_run_git_bytes/_run_git 293-335, _range_writer_identities 505-551, verdict block 1790-1960, findings-lane acceptance line 198-232)",
      "src/agentmarshal/journal/report.py (SELF_ACCEPTED_MARK 37-47, TaskReport 146-160, _writers_repository 453-468, declared_commit_writers 470-495, accepting_party_is_declared_writer 497-514, _self_accepted 516-537, _task_report 539-640, format_report 900-935)",
      "src/agentmarshal/journal/status_view.py (_is_self_accepted/_is_self_acknowledged 53-90, print_task_detail 754-792)",
      "src/agentmarshal/journal/records.py (_project_root_for 2027-2041, create_completed_record 2193-2223, create_acceptance_record 2485-2525)",
      "src/agentmarshal/journal/placement.py (resolve_placement 64-98)",
      "src/agentmarshal/cli.py (_run_report 1380-1400, status print_task_detail call 1525)",
      "docs/adr/ADR-0007-operator-acceptance.md (decisions 4 and 5)",
      "openspec/specs/operator-acceptance/spec.md (full file; requirements at 72-168 and 280-404)",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/{proposal.md,design.md,tasks.md,specs/operator-acceptance/spec.md}",
      "tests/test_self_acceptance_on_every_surface.py (all 638 lines)",
      "tests/test_pause_and_operational_acceptance.py (640-760)",
      "tests/test_gate.py (_WRITER 42, _commit_all 97-101, _gate_repo 103-122, _implement 170-174, _require_changes 202-227, _accept 283-302)",
      "tests/test_journal.py (initialize_status_repo 44-60)",
      "docs/threat-model.md (95-115)"
    ],
    "executed": [
      {"what": "grep -rn 'accepted over findings|accepted-over-findings|self-accepted' over openspec/specs/, docs/, README.md, CHANGELOG.md", "result": "operator-acceptance is the only capability spec covering the acceptance line and report decision; docs/threat-model.md and ADR-0022 already state the mark, no doc update owed"},
      {"what": "grep -rn 'accepted over findings' tests/fixtures/ and ls tests/fixtures/gate", "result": "no gate transcript fixture contains an acceptance line, so none needed updating"},
      {"what": "grep -rn 'self-accepted|self_accepted' tests/*.py excluding the new file", "result": "status findings-form self-acceptance still pinned at tests/test_status_view.py:283 and tests/test_acceptance.py:199 despite the edit to test_every_output_for_an_acceptance_over_findings_is_unchanged"},
      {"what": "grep -rn '_task_report|build_report|format_report' over src/ and tests/", "result": "only tests/test_display.py:254 calls _task_report directly; signature change covered"},
      {"what": "grep -n 'subprocess' src/agentmarshal/journal/status_view.py", "result": "still used at 706 and 719, so the import is not left dangling after _declared_commit_writers moved out"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "no .venv or uv in this sandbox and the snapshot is not a git worktree, so the git-backed tests could not run; the coordinator states the sequence passed on the reviewed commit"},
      {"what": "live git log --format=%an%x00%ae%x00%cn%x00%ce%x00 to confirm NUL/field alignment empirically", "why": "shell approval for creating a scratch repo was declined; alignment verified by reading the parser against git tformat semantics (each entry emits exactly four NULs, the terminating newline attaches to the next name field and is removed by .strip()), including the empty-range and single-commit cases"}
    ]
  },
  "evidence": {
    "SA-1": "src/agentmarshal/journal/gate.py:1841 computes identities over merge_base..resolved_commit via _range_writer_identities (gate.py:505-551) and applies the mark at gate.py:1851; src/agentmarshal/journal/report.py:534 computes them with declared_commit_writers over acceptance['accepted_commit'] alone (report.py:516-537). The requirement the change added, openspec/specs/operator-acceptance/spec.md:316-323, binds BOTH surfaces to 'a declared writer of the candidate'. Failing journal: range B..C2 with C1 by alice@x and C2 by bob@x, review(C2, changes_required, F-1), accept C2 --by alice@x, completed C2 -> gate line carries ' (self-accepted: accepting party is a declared author or committer)', report line is 'CR-xxx\\tdone\\treviews=1\\ttokens=0\\tdecision=accepted-over-findings' with no mark. No test covers a multi-commit range with a party who wrote only a non-tip commit: tests/test_self_acceptance_on_every_surface.py builds every gate case from _gate_repo + a single _implement, and the one two-commit case (line 255) uses worker@test.invalid, which tests/test_gate.py:42,99 makes a writer of both commits.",
    "SA-2": "tests/test_self_acceptance_on_every_surface.py:255-273 docstring claims 'the surviving email half of the identity still earns the mark', but _implement_latin1_author (same file, 110-146) parents the rewritten commit on the _implement commit, whose author is Worker <worker@test.invalid> per _WRITER at tests/test_gate.py:42 used by _commit_all at tests/test_gate.py:99 — so worker@test.invalid is in writer_identities regardless of how the latin-1 commit's fields decode, and the assertion cannot distinguish the two."
  }
}
AGENTMARSHAL_VERDICT_END
