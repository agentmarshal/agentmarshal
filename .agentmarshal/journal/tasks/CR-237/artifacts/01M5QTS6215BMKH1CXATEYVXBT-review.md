Разобрал дифф, прочитал `report.py`, `gate.py`, `status_view.py`, `status.py`, `placement.py`, `complete.py`, спеку `operator-acceptance`, ADR-0007, `docs/threat-model.md` и затронутые тесты. Исполнять ничего не мог (sandbox не даёт запускать интерпретатор), так что утверждений о падении инструментов не делаю.

**Блокирующая находка**

`BLK-report-decision-reads-records-after-the-completion` — `src/agentmarshal/journal/report.py:520-560`: решение выводится из последнего `completed`-рекорда и из **всех** review/acceptance этого binding'а, включая записанные уже после завершения. Последовательность обычных команд: `submit-review --commit C --verdict changes_required --finding F-1` → `accept --commit C` → `complete` (gate проходит по acceptance) → `reopen` → `submit-review --commit C --verdict approved`. После reopen state снова `open`, и review допускается (`status.py:175-180`, `attestation.py:79`), а `submit-review` не запрещает назвать коммит, который уже закрыт (`submit_review.py:116` проверяет только admission). Тогда `reviews[-1]["verdict"] == "approved"` и строка читается `CR-001 open reviews=2 tokens=0 decision=approved`, хотя единственное завершение этой задачи закрылось over findings; до диффа та же строка читалась `decision=accepted-over-findings`. Это прямо противоречит ADR-0007 решению 5 («An accepted-over-findings task must be distinguishable from a reviewed-and-approved one everywhere either is read»), причём регрессия внесена именно этим диффом: старая первая ветка (`any acceptance with findings`) такой журнал не теряла. Чинится узко — считать review и acceptance только по записям, предшествующим `completed`-рекорду в порядке хранения (append-only журнал тогда нельзя переписать поздней записью, ровно как `complete.py:89-110` защищает `resolved_review`), либо вообще не печатать `decision` для reopened-задачи. Тестом этот случай не покрыт ни в одну сторону.

**Advisory**

`ADV-report-cannot-say-the-mark-was-unchecked` — `report.py:494-502`: `_self_accepted` возвращает `False` и когда accepting party не writer, и когда git не смог прочитать коммит, так что строка `report` для shallow-клона, отсутствующего коммита или sidecar без хоста неотличима от честного «не self-acceptance». Именно это склеивание `status` держит раздельно и объясняет, почему (`status_view.py:71-84`), а `docs/threat-model.md:102-104` обещает «always marked as self-acceptance». Решение задокументировано в `design.md` и зафиксировано новым requirement'ом («report marks a confirmed self-acceptance only»), поэтому не блокирую — но поверхность, с которой читают отчёт, теперь молчит там, где раньше молчания не было обещано.

`ADV-gate-and-report-mark-from-different-identity-sets` — `openspec/specs/operator-acceptance/spec.md:316-326` формулирует **одно** условие («a declared writer of the candidate») сразу для двух поверхностей, но gate считает его по всему диапазону `merge-base..candidate` (`gate.py:509-527`, `1824-1828`), а `report` и `status` — по одному accepted-коммиту (`report.py:494-502`). Автор более раннего коммита диапазона получит марку у gate и не получит у `report`/`status` — сценарии требования это разводят, прозаическая часть нет. Там же разъезжается формулировка квалификации: gate печатает `(self-accepted: accepting party is a declared writer of the candidate)`, а `status` — `(self-accepted: accepting party is a declared author or committer)`, хотя критерий 1 просит «in the terms status uses»; grep по одной фразе другую не находит.

`ADV-gate-reads-the-candidate-range-twice` — `gate.py:1816-1828`: `_range_writer_identities` вызывается при любом `latest is not None`, хотя используется только в ветке `valid_acceptance is not None`, то есть к каждому прогону gate с review добавлен второй `git log` по тому же диапазону; его результат — надмножество `writer_emails`, так что одного вызова хватило бы на оба набора.

`ADV-shared-comparison-crosses-three-modules-by-private-name` — `gate.py:64` импортирует приватное `report._accepting_party_is_declared_writer`, а `report.py:496` внутри функции импортирует приватное `status_view._declared_commit_writers`, иначе цикл. Трёхстрочная общая сверка тянет зависимость gate → report и отложенный импорт обратно; отдельный маленький модуль (git-идентичности) снял бы и то и другое.

**Критерии приёмки**

1. Выполнен на обеих поверхностях: gate — `gate.py:1829-1841`, демонстрируют `tests/test_self_acceptance_on_every_surface.py::test_the_gates_acceptance_line_marks_a_self_acceptance` (три параметра: email, иной регистр, имя) и `::test_the_gates_acceptance_line_marks_a_committer_self_acceptance`; report — `report.py:884-891`, демонстрируют `::test_reports_task_line_marks_a_self_acceptance` и `::test_reports_task_line_marks_a_committer_self_acceptance`; «чужая сторона — без марки» — `::test_an_acceptance_by_another_party_prints_unmarked` (проверяет обе поверхности). Оговорка — `ADV-gate-and-report-mark-from-different-identity-sets`.
2. Для **завершённой** задачи выполнен: `report.py:528-560`, демонстрируют `::test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved`, `::test_a_commit_approved_after_its_own_acceptance_reports_approved`, `::test_a_commit_completed_over_findings_reports_accepted_over_findings`, `::test_a_finding_completed_over_findings_reports_accepted_over_findings`, `::test_an_acceptance_bound_to_another_commit_leaves_no_decision`, `::test_a_task_with_no_completed_record_keeps_todays_decision_rule`. Не выполнен для задачи, переоткрытой после завершения over findings — `BLK-report-decision-reads-records-after-the-completion`.
3. Выполнен: delta несёт MODIFIED с полным текстом требования, heading байт в байт и всеми шестью его сценариями, и два ADDED-требования с десятью сценариями; у каждого сценария есть тест, чей docstring его называет (включая изменённый сценарий MODIFIED — `tests/test_pause_and_operational_acceptance.py::test_every_output_for_an_acceptance_over_findings_is_unchanged`). Изменение приехало в `openspec/specs/operator-acceptance/spec.md:129-134` и `:316-397`, change лежит в `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/`, рабочей копии change'а не осталось — результат соответствует `openspec archive`; что это сделала именно команда, по диффу не проверить. Других требований с byte-for-byte клаузой, которых касается марка, в спеках нет (проверил grep'ом по `openspec/specs/`).
4. Выполнен: журнал без self-acceptance и без acceptance по другому коммиту печатает то же — старые пины `tests/test_report.py:437-439`, `tests/test_report_lead_time.py:170,201,335`, `tests/test_status_view.py:253+`, `tests/test_gate.py:1555`, и `tests/test_quickstart.py::test_accept_over_a_non_approving_review_prints_the_documented_line` (писатели `dev@example.com`, accepting party `operator@example.com` → марки нет, транскрипт quickstart'а цел). Escaping как раньше: gate экранирует готовую строку (`gate.py:1178-1183`), новая часть строки `report` — собственный текст инструмента (`report.py:868-875`). Два правленых теста в `test_pause_and_operational_acceptance.py` переносят byte-for-byte пин с self-accepting party на `op` — этого требует новая WHEN-клауза сценария, а пины self-accepted у `status` остались (`test_status_view.py:261`, `test_pause_and_operational_acceptance.py:642`). CI не запускал.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "10197420e17fb52a6ced52176b5256a1a379c940",
  "verdict": "changes_required",
  "findings": ["BLK-report-decision-reads-records-after-the-completion"],
  "advisory_findings": [
    "ADV-report-cannot-say-the-mark-was-unchecked",
    "ADV-gate-and-report-mark-from-different-identity-sets",
    "ADV-gate-reads-the-candidate-range-twice",
    "ADV-shared-comparison-crosses-three-modules-by-private-name"
  ],
  "classes": {
    "BLK-report-decision-reads-records-after-the-completion": "correctness",
    "ADV-report-cannot-say-the-mark-was-unchecked": "claim-accuracy",
    "ADV-gate-and-report-mark-from-different-identity-sets": "claim-accuracy",
    "ADV-gate-reads-the-candidate-range-twice": "efficiency",
    "ADV-shared-comparison-crosses-three-modules-by-private-name": "style"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/gate.py (imports, _range_emails/_range_writer_identities, findings lane, run_gate verdict block)",
      "src/agentmarshal/journal/status_view.py (_declared_commit_writers, _is_self_accepted, _render_acceptance_line, print_task_detail)",
      "src/agentmarshal/journal/status.py (project_status, load_task_for_record, record_type_is_admitted_after_terminal)",
      "src/agentmarshal/journal/attestation.py (RECORD_TYPES admitted_after_terminal)",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/complete.py (record_commit_completion)",
      "src/agentmarshal/journal/records.py (_project_root_for, _validate_binding, create_completed_record)",
      "src/agentmarshal/journal/__init__.py, src/agentmarshal/cli.py (report/status call sites)",
      "docs/adr/ADR-0007-operator-acceptance.md",
      "docs/threat-model.md:95-108, docs/quickstart.md:425-490, docs/sidecar.md:315-350, CONTRIBUTING.md:120-195, CHANGELOG.md:480-498",
      "openspec/specs/operator-acceptance/spec.md (full)",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/{proposal,design,tasks}.md and its spec delta",
      "tests/test_self_acceptance_on_every_surface.py, tests/test_pause_and_operational_acceptance.py, tests/test_report.py, tests/test_status_view.py, tests/test_quickstart.py, tests/test_gate.py helpers, tests/test_display.py"
    ],
    "executed": [
      {
        "what": "grep -rn 'decision=' openspec/specs docs tests .github templates",
        "result": "only operator-acceptance/spec.md and docs/sidecar.md:335 document the field; no script parses report output, so the new bare `self-accepted` token breaks no parser in-tree"
      },
      {
        "what": "grep -rn 'byte for byte|byte-identical' openspec/specs/",
        "result": "no requirement outside operator-acceptance pins the gate acceptance line or the report task line, so the single MODIFIED requirement is the only one the mark touches"
      },
      {
        "what": "grep -rn 'declared author or committer' tests/",
        "result": "status's self-accepted pins survive at tests/test_status_view.py:262 and tests/test_pause_and_operational_acceptance.py:642 after the party in the byte-for-byte test was changed to 'op'"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "read-only review in a sandbox that refuses to execute interpreters (python3 -V was denied); per the coordinator's note the sequence passed on this commit, and I make no claim that any tool fails"
      },
      {
        "what": "reproducing the reopen sequence of the blocking finding as a test",
        "why": "same execution restriction; the finding is derived by reading report.py:520-560 together with status.py:175-180 and attestation.py:79"
      }
    ]
  },
  "evidence": {
    "BLK-report-decision-reads-records-after-the-completion": "src/agentmarshal/journal/report.py:520-560 selects the last `completed` record and then every review/acceptance of that binding regardless of write order; src/agentmarshal/journal/status.py:175-180 with src/agentmarshal/journal/attestation.py:79 admit a `review` once a `reopened` record has returned the task to `open`, and src/agentmarshal/journal/submit_review.py:116 adds no constraint on the reviewed commit. Journal open -> review(C, changes_required, F-1) -> acceptance(C, F-1) -> completed(C) -> reopened -> review(C, approved) therefore makes reviews[-1]['verdict'] == 'approved' and prints `CR-001\\topen\\treviews=2\\ttokens=0\\tdecision=approved`, where the pre-diff code printed `decision=accepted-over-findings`; docs/adr/ADR-0007-operator-acceptance.md:151-160 forbids an accepted-over-findings task reading as approved.",
    "ADV-report-cannot-say-the-mark-was-unchecked": "src/agentmarshal/journal/report.py:494-502 returns False both for 'no match' and for 'git could not answer', against src/agentmarshal/journal/status_view.py:71-84 ('If an unanswerable git query were reported as \"not self-accepted\", the display would quietly lose exactly that') and docs/threat-model.md:102-104 ('always marked as self-acceptance'); the trade-off is recorded in the change's design.md and in openspec/specs/operator-acceptance/spec.md:322-325.",
    "ADV-gate-and-report-mark-from-different-identity-sets": "openspec/specs/operator-acceptance/spec.md:316-326 states one condition for both surfaces; src/agentmarshal/journal/gate.py:509-527 and :1824-1828 derive it from `git log --format=%an%n%ae%n%cn%n%ce merge-base..candidate` while src/agentmarshal/journal/report.py:494-502 derives it from `status_view._declared_commit_writers` on the accepted commit alone (src/agentmarshal/journal/status_view.py:48-68). Qualification texts also differ: gate.py:1832-1834 '(self-accepted: accepting party is a declared writer of the candidate)' vs status_view.py:807-809 '(self-accepted: accepting party is a declared author or committer)'.",
    "ADV-gate-reads-the-candidate-range-twice": "src/agentmarshal/journal/gate.py:1816-1828 computes both `writer_emails` and `writer_identities` whenever `latest is not None`, but `writer_identities` is read only at gate.py:1835 inside the `valid_acceptance is not None` branch; `_range_writer_identities` (gate.py:509-527) returns a case-folded superset of `_range_emails` (gate.py:502-506), so one `git log` could serve both.",
    "ADV-shared-comparison-crosses-three-modules-by-private-name": "src/agentmarshal/journal/gate.py:64 imports `report._accepting_party_is_declared_writer`; src/agentmarshal/journal/report.py:496 imports `status_view._declared_commit_writers` inside the function because src/agentmarshal/journal/status_view.py:24 imports `report` at module level."
  }
}
AGENTMARSHAL_VERDICT_END
