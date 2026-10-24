Разобрал контракт, дифф и код вокруг него (исполнять python/pytest в этой сессии не дали — всё ниже получено чтением исходников, не прогоном).

## Что сделано по критериям

**AC1 — метка self-acceptance на гейте и в `report`.** Выполнен. Гейт поднимает набор writer-emails до блока вердикта (`src/agentmarshal/journal/gate.py:1791`) и дописывает ` (self-accepted: accepting party is a declared writer of the candidate)` (`gate.py:1802-1811`); демонстрируют `tests/test_self_acceptance_on_every_surface.py::test_the_gates_acceptance_line_marks_a_self_acceptance` (включая параметр с другим регистром) и `::test_the_gates_acceptance_line_marks_a_committer_self_acceptance`. `report` несёт ту же метку через `TaskReport.self_accepted` и `format_report` (`report.py:866-875`), демонстрируют `::test_reports_task_line_marks_a_self_acceptance` и `::test_reports_task_line_marks_a_committer_self_acceptance`; «немаркированный» случай — `::test_an_acceptance_by_another_party_prints_unmarked`, «непроверяемый» — `::test_reports_task_line_says_when_the_check_cannot_run`. Делегирование в `status_view._is_self_accepted` сделано локальным импортом из-за цикла (`report.py:478-484`) — обосновано и верно.

**AC2 — decision по завершающей записи.** Выполнен для случая, который называет первая половина критерия: `report.py:510-551` читает ревью и acceptance ровно по `completed_commit`/`completed_finding`; демонстрируют `::test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved`, `::test_a_commit_completed_over_findings_reports_accepted_over_findings`, `::test_a_finding_completed_over_findings_reports_accepted_over_findings`, `::test_an_acceptance_bound_to_another_commit_leaves_no_decision`, `::test_a_task_with_no_completed_record_keeps_todays_decision_rule`. Вторая половина критерия («задача, завершённая над findings на завершающем коммите, отчитывается как accepted-over-findings») не выполняется в одном достижимом случае — см. блокирующую находку ниже.

**AC3 — дельта и архив.** Выполнен: `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/specs/operator-acceptance/spec.md` несёт ADDED (пять сценариев нового поведения плюс четыре по decision) и MODIFIED с полным текстом требования и всеми шестью его сценариями, и этот текст лёг в `openspec/specs/operator-acceptance/spec.md:119-168, 316-387`. Каждый сценарий дельты назван в docstring теста: новые — в `tests/test_self_acceptance_on_every_surface.py`, шесть сценариев MODIFIED — в `tests/test_pause_and_operational_acceptance.py:378, 418, 493, 573, 628, 656, 713`.

**AC4 — сегодняшний вывод без self-acceptance.** В основном выполнен: фикстуры гейта и транскрипты дифф не трогает, значения печатаются экранированными как прежде (обе новые метки — литералы). Оговорка — третья находка.

## Находки

**CR237-report-approval-overrides-same-commit-acceptance (блокирующая).** В `src/agentmarshal/journal/report.py:530` одобряющее последнее ревью завершающего коммита побеждает безусловно, и только в `else` смотрится acceptance, привязанный к тому же коммиту (`report.py:533-542`). Поэтому журнал `review(X, changes_required, F-1)` → `acceptance(X, F-1)` → (гейт прошёл по acceptance, merge) → `review(X, approved)` → `completed(X)` печатает `decision=approved` без метки, хотя задача закрылась над findings на этом самом коммите. Последовательность допустима: `project_status` запрещает записи только после терминальной (`src/agentmarshal/journal/status.py:120-125`), а здесь `completed` идёт последней. Это противоречит ADR-0007, решение 5 («Accepted is never displayed as approved», `docs/adr/ADR-0007-operator-acceptance.md:151-161`), утверждению `docs/threat-model.md:102`, и второй половине AC2. До диффа такой журнал печатался как `accepted-over-findings`. Контракт просил перевернуть только случай «принят был более ранний коммит»; перестановка приоритета (acceptance с `findings`, привязанный к завершающей записи, выигрывает; иначе одобряющее последнее ревью) удовлетворяет обе половины AC2 и не ломает ни одного сценария дельты — в сценарии «a commit approved after an earlier commit's acceptance» acceptance привязан к другому коммиту.

**CR237-gate-mark-identity-set-differs (совещательная).** Гейт сравнивает `accepted_by` с набором, который строит `_range_emails` — только адреса (`--format=%ae%n%ce`, `gate.py:501-505`, сравнение на `gate.py:1805`), а `report` и `status` сравнивают с именами и адресами автора и коммиттера принятого коммита (`status_view.py:57`). Значит `accepted_by`, равный имени писателя, помечается в `report` и `status`, но не на гейте: собственный тест диффа `tests/test_self_acceptance_on_every_surface.py:263` параметризован партией `"Committer"` именно для `report`, а гейтового теста с именем нет и метка там не появилась бы. Обратный перекос тоже есть: адрес автора более раннего коммита диапазона пометит гейт, но не `report`. AC1 прямо разрешает гейту брать «identities the gate's independence check already reads», поэтому не блокирую, но «every surface» из ADR-0007 решение 4 для партии-имени пока не выполнено.

**CR237-unchecked-mark-changes-unrelated-report-lines (совещательная).** Метка `self-acceptance-unchecked` печатается не только для self-acceptance: любой acceptance над findings, чей коммит недоступен git в месте запуска `report` (sidecar-журнал без хоста, shallow-клон, выпавший коммит), получает новое последнее поле (`report.py:474-484`, `report.py:871-875`). Конкретно `tests/test_report.py:437` — acceptance на `"a" * 40` — теперь печатает строку с этим полем, и существующий тест этого не видит только потому, что сверяет подстрокой через `in`. Это расходится с формулировкой AC4 («существующие report-тесты демонстрируют вывод неизменным») и с собственной MODIFIED-формулировкой дельты «byte for byte for an acceptance that is not a self-acceptance» (`openspec/specs/operator-acceptance/spec.md:128-133, 164-168`), которую перекрывает ADDED-сценарий про непроверяемый случай (`spec.md:344-351`). Поведение осознанное и согласовано со `status`, поэтому только к сведению — но стоит либо признать его в MODIFIED-тексте, либо закрепить строку точным сравнением в `tests/test_report.py`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4bf45b5982cad1bfda0fea77acc97fc254df5cf6",
  "verdict": "changes_required",
  "findings": ["CR237-report-approval-overrides-same-commit-acceptance"],
  "advisory_findings": [
    "CR237-gate-mark-identity-set-differs",
    "CR237-unchecked-mark-changes-unrelated-report-lines"
  ],
  "classes": {
    "CR237-report-approval-overrides-same-commit-acceptance": "correctness",
    "CR237-gate-mark-identity-set-differs": "contract-mismatch",
    "CR237-unchecked-mark-changes-unrelated-report-lines": "contract-mismatch"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/gate.py (lines 180-230, 289-520, 1690-1960)",
      "src/agentmarshal/journal/status_view.py (lines 1-200, 740-870)",
      "src/agentmarshal/journal/status.py",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/records.py (_project_root_for, create_completed_record)",
      "src/agentmarshal/cli.py (status and report command paths)",
      "src/agentmarshal/stages.py (pause-acceptance line)",
      "docs/adr/ADR-0007-operator-acceptance.md",
      "docs/threat-model.md (lines 95-115)",
      "openspec/specs/operator-acceptance/spec.md",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/ (proposal.md, design.md, tasks.md, specs/operator-acceptance/spec.md)",
      "tests/test_self_acceptance_on_every_surface.py",
      "tests/test_pause_and_operational_acceptance.py",
      "tests/test_report.py",
      "tests/test_gate.py (acceptance-line assertions)",
      "tests/test_display.py"
    ],
    "executed": [
      {"what": "grep for other specs documenting report's decision field (openspec/specs)", "result": "only operator-acceptance documents decision=; no contradicting capability spec"},
      {"what": "grep for byte-for-byte output clauses across openspec/specs", "result": "gate-lanes pins transcripts by fixture; no fixture in the diff changed"},
      {"what": "grep for docstrings naming every delta scenario in tests/", "result": "each ADDED and MODIFIED scenario has a test whose docstring names it"}
    ],
    "not_run": [
      {"what": "the CI sequence (uv sync/validate/pytest/ruff/mypy) and a python reproduction of the finding", "why": "running python or pytest was not permitted in this read-only session; the finding is derived from the code paths cited, not from execution"}
    ]
  },
  "evidence": {
    "CR237-report-approval-overrides-same-commit-acceptance": "src/agentmarshal/journal/report.py:530 (`if reviews and reviews[-1][\"verdict\"] == \"approved\": decision = \"approved\"`) runs before the acceptance branch at report.py:533-542; src/agentmarshal/journal/status.py:120-125 admits a review recorded before the terminal record, so review(X,changes_required) -> acceptance(X) -> review(X,approved) -> completed(X) is a loadable journal; contradicts docs/adr/ADR-0007-operator-acceptance.md:151-161 and docs/threat-model.md:102, and the second clause of contract acceptance criterion 2",
    "CR237-gate-mark-identity-set-differs": "src/agentmarshal/journal/gate.py:501-505 builds the set from `git log --format=%ae%n%ce` (emails only) and gate.py:1805 compares accepted_by against it, while src/agentmarshal/journal/status_view.py:57 uses `git show -s --format=%an%n%ae%n%cn%n%ce` (names and emails); tests/test_self_acceptance_on_every_surface.py:263 parametrizes report with the name \"Committer\" and no gate test uses a name-valued party",
    "CR237-unchecked-mark-changes-unrelated-report-lines": "src/agentmarshal/journal/report.py:474-484 returns None for an unreadable commit and report.py:871-875 appends `\\tself-acceptance-unchecked`; tests/test_report.py:432-437 accepts commit \"a\"*40 in a real repo and asserts with `in`, so the added field is invisible to it; openspec/specs/operator-acceptance/spec.md:128-133 and 164-168 still promise a byte-identical report line for a non-self-acceptance"
  }
}
AGENTMARSHAL_VERDICT_END
