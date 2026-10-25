## Что проверено

Читал источники целиком (не по диффу): `report.acknowledging_party_is_declared_writer`, `accepting_party_is_declared_writer`, `declared_commit_writers`, `_range_writer_identities`, оба вызова `_acknowledgement_mark` (их ровно два — `cli.py:1827` и `gate.py:2390`, т.е. «каждая поверхность» действительно покрыта), `status_view._is_self_acknowledged` до/после, `actors._actor_git_identities`, ADR-0021 решение 5, живой `openspec/specs/leak-scan/spec.md`, фикстуры транскриптов и хелперы тестов (`test_gate._WRITER` = `worker@test.invalid`, `test_leak_scan_acknowledgements._WRITER` = `test@example.invalid` — значит ожидания новых тестов детерминированы). Циклов импорта нет: `records → capture`, `report → records`, `report → actors`, `actors → project`, так что заявление в докстринге `capture` про порядок импорта верно. Второй копии сравнения не осталось: `grep -rn isdisjoint src/` даёт только `stages.py:653`.

Полную последовательность CI я не запускал: в снапшоте нет git-репозитория и нет `.venv`, поэтому про `pytest/mypy/ruff` опираюсь на утверждение координатора для коммита 3d54e73 и ничего про их падение не заявляю.

## Находки

**CR242-R1 (блокирующая).** Диф вводит намеренное и протестированное расхождение отметки между двумя поверхностями, но живая спецификация способности это по-прежнему запрещает и дельта её не меняет. В `openspec/specs/leak-scan/spec.md:654` требование говорит «the same mark over the same naming, the one mark-builder the two surfaces share», а сценарий `openspec/specs/leak-scan/spec.md:741-745` — «the mark on the line is the mark on the command's output — same wording, same masking, same escaping»; ADR-0021 в разделе «What this revises» (`docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md:187-191`) подтверждает тот же паритет «mark included». Новый тест `tests/test_self_acknowledgement_mark.py:190-241` показывает ровно обратное: одна и та же запись и один и тот же hit `src/leak.py: github-token` печатаются гейтом как `self-acknowledged by earlier@test.invalid: …`, а командой — как `acknowledged by earlier@test.invalid: …` (строка 241 это прямо фиксирует). Дельта — только `ADDED Requirements`, ни требование на строке 654, ни сценарий на 741 не вынесены как `MODIFIED` с полным текущим текстом, хотя именно этого требует критерий приёмки 2 для изменившегося требования; в результате после архивации спецификация способности внутренне противоречива. Само поведение сомнению не подлежит — критерий 1 прямо санкционирует «the gate over the candidate range, `leak-scan` over the commit it scans», — поэтому починка спецификационная: `MODIFIED` на требование о паритете с оговоркой про разные множества писателей.

**CR242-R2 (совещательная, test-gap).** Половина сценария «a check git cannot answer marks nothing» для гейта закреплена невозможным контрактом. В `src/agentmarshal/journal/gate.py:2382-2388` единственный источник `None` на стороне гейта — ветка `except GateError`, а тест `tests/test_self_acknowledgement_mark.py:298-302` вместо отказа git подменяет `_range_writer_identities` на `lambda *args: ({"worker@test.invalid"}, None)` — значение, которое настоящая функция вернуть не может: по `src/agentmarshal/journal/gate.py:538-586` она возвращает два множества либо поднимает `GateError`. Ветка `except GateError: writer_identities = None` остаётся непокрытой, и изменение в деградации (например, если отказ перестанет перехватываться) этим тестом не поймается. На стороне команды претензий нет: там подменён `cli_module.declared_commit_writers` на `None`, а это реальное возвращаемое значение (`report.py:503-519`).

## Критерии приёмки

- **Критерий 1 — выполнен.** `leak-scan` сравнивает по писателям сканируемого коммита (`cli.py:1799`, через `declared_commit_writers`), гейт — по писателям диапазона (`gate.py:2382-2388`, через `_range_writer_identities`, с переиспользованием вычисления вердикт-блока из `gate.py:1926` — обе точки в одной области видимости `run_gate`, так что заявление о единственном чтении диапазона структурно верно). Сравнение единственное: `acknowledging_party_is_declared_writer` (`report.py:554-588`) прогоняет каждую git-идентичность через `accepting_party_is_declared_writer`, а `status_view._is_self_acknowledged` (`status_view.py:86-90`) теперь делегирует туда же — копии нет. Демонстрируют: `test_the_standalone_command_marks_a_self_acknowledgement` (команда), `test_the_gate_marks_a_self_acknowledgement_over_the_candidate_range` (гейт), плюс `test_the_commits_committer_marks_a_self_acknowledgement`, `test_a_declared_actors_resolved_identity_marks_a_self_acknowledgement`, `test_the_writer_check_folds_case`. Термин совпадает со status (`status_view.py:262`: `" self-acknowledged"`). Требование называет оба условия («the commit `leak-scan` scans — of any commit in the candidate range for the gate»).
- **Критерий 2 — выполнен частично.** Дельта на способность `leak-scan` есть, формы `ADDED`, архивирована в `openspec/changes/archive/2026-10-25-self-acknowledgement-mark/`, и текст требования в `openspec/specs/leak-scan/spec.md` совпадает с дельтой побайтово (сверил `diff` окон — различие только в сдвиге на строку заголовка `## ADDED Requirements`). Все восемь сценариев дельты закрыты восемью тестами, каждый назван в докстринге (`test_the_standalone_command_marks_a_self_acknowledgement`, `…over_the_candidate_range`, `…the_commits_committer…`, `…a_declared_actors_resolved_identity…`, `…an_earlier_range_commit_marks_at_the_gate_alone`, `…by_another_party_prints_unmarked`, `…a_check_git_cannot_answer_marks_nothing`, `…the_writer_check_folds_case`). Не выполнена часть про `MODIFIED`: изменившееся требование о паритете отметок не вынесено в дельту — это CR242-R1.
- **Критерий 3 — выполнен (в той части, которую можно проверить чтением).** Чужая сторона печатается как раньше: `test_an_acknowledgement_by_another_party_prints_unmarked` пинит обе поверхности побайтово. Вывод `status` не менялся: рефакторинг `_is_self_acknowledged` сохраняет и порядок вычислений, и три состояния — `writers is None → None`, затем те же `_actor_git_identities` + сам `recorded_by` против того же множества, а `.strip().casefold()` в `accepting_party_is_declared_writer` идемпотентен относительно уже свёрнутых идентичностей. Фикстуры транскриптов отметок не содержат вовсе (`grep -rln acknowledged tests/fixtures` — пусто), так что они не могли сдвинуться. Про прохождение самой последовательности CI — не запускал, см. выше.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "3d54e73601eacb9879828e5f8254ce69febc2202",
  "verdict": "changes_required",
  "findings": ["CR242-R1"],
  "advisory_findings": ["CR242-R2"],
  "classes": {
    "CR242-R1": "contract-mismatch",
    "CR242-R2": "test-gap"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"_acknowledgement_mark\" src tests", "result": "only two call sites: src/agentmarshal/cli.py:1827 and src/agentmarshal/journal/gate.py:2390 — both updated"},
      {"what": "grep -n \"writer_identities|writer_emails\" src/agentmarshal/journal/gate.py", "result": "1479 declaration, 1926 verdict-lane assignment, 2382-2396 advisory — all inside run_gate (next def after 1204 is the nested _task_of at 2221), so the reuse is real"},
      {"what": "grep -rn isdisjoint src/", "result": "only src/agentmarshal/stages.py:653 — the duplicated comparison in status_view is gone"},
      {"what": "grep -rln acknowledged tests/fixtures", "result": "no match — no transcript fixture carries an acknowledgement mark"},
      {"what": "diff of the 54-line tails of openspec/changes/archive/2026-10-25-self-acknowledgement-mark/specs/leak-scan/spec.md and openspec/specs/leak-scan/spec.md", "result": "single difference at the window's first line (the '## ADDED Requirements' header offset); the requirement and all eight scenarios are byte-identical"},
      {"what": "grep -n \"same mark over the same naming|Scenario: the mark is the one the standalone command prints\" openspec/specs/leak-scan/spec.md", "result": "654 and 741 — the parity requirement and scenario the diff leaves unmodified"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py (declared_commit_writers, accepting_party_is_declared_writer, acknowledging_party_is_declared_writer, _self_accepted)",
      "src/agentmarshal/journal/gate.py (run_gate head and lanes, _range_writer_identities, _run_git_bytes, advisory leak-scan block)",
      "src/agentmarshal/cli.py _run_leak_scan",
      "src/agentmarshal/journal/capture.py _acknowledgement_mark",
      "src/agentmarshal/journal/status_view.py (_is_self_acknowledged and the mark wording table)",
      "src/agentmarshal/journal/actors.py (_actor_git_identities) and src/agentmarshal/project.py (read_project_file)",
      "docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md decisions 3-5 and 'What this revises'",
      "openspec/specs/leak-scan/spec.md (acknowledgement requirements and the new requirement)",
      "tests/test_self_acknowledgement_mark.py, tests/test_gate_marks_acknowledged_hits.py, tests/test_leak_scan_acknowledgements.py and test_gate.py helpers"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the review snapshot is not a git repository and carries no virtualenv or lockfile-installed environment, so the CI sequence could not be executed here; the coordinator states it passed on the reviewed commit"}
    ]
  },
  "evidence": {
    "CR242-R1": "openspec/specs/leak-scan/spec.md:654 ('the same mark over the same naming, the one mark-builder the two surfaces share') and openspec/specs/leak-scan/spec.md:741-745 ('the mark on the line is the mark on the command's output — same wording, same masking, same escaping'), reaffirmed by docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md:187-191, versus tests/test_self_acknowledgement_mark.py:190-241, where the same hit and record print 'self-acknowledged by earlier@test.invalid' on the gate's line and 'acknowledged by earlier@test.invalid' from the command (line 241 asserts 'self-acknowledged' is absent from the command's output); the delta openspec/changes/archive/2026-10-25-self-acknowledgement-mark/specs/leak-scan/spec.md contains only '## ADDED Requirements' and no MODIFIED block for either.",
    "CR242-R2": "src/agentmarshal/journal/gate.py:2382-2388 makes 'except GateError: writer_identities = None' the gate's only unchecked leg, while src/agentmarshal/journal/gate.py:538-586 shows _range_writer_identities returns tuple[set[str], set[str]] or raises GateError; tests/test_self_acknowledgement_mark.py:298-302 pins the scenario with monkeypatch.setattr(gate_module, '_range_writer_identities', lambda *args: ({'worker@test.invalid'}, None)), a return value the function cannot produce, so the except branch stays uncovered."
  }
}
AGENTMARSHAL_VERDICT_END
