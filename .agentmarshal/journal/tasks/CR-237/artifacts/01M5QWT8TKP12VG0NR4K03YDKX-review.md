Разобрался с диффом: прочитал `report.py`, `gate.py`, `status_view.py`, текущий `openspec/specs/operator-acceptance/spec.md`, ADR-0007 (решения 4 и 5), новый тест-файл и два изменённых теста. Запустить `pytest`/`mypy`/`ruff` здесь не вышло — песочница не даёт исполнять python; опираюсь на заметку координатора о зелёном CI на 6f1c96c и на статическое чтение.

**Как критерии закрыты**

- **AC1 (метка self-acceptance на гейте и в report).** Гейт считает идентичности диапазона в `src/agentmarshal/journal/gate.py:505-529` и клеит `SELF_ACCEPTED_MARK` к PASS-строке в `gate.py:1825-1841`; демонстрируют `test_the_gates_acceptance_line_marks_a_self_acceptance` (`tests/test_self_acceptance_on_every_surface.py:163`) и его committer-вариант (`:190`), а «чужая» сторона — `test_an_acceptance_by_another_party_prints_unmarked` (`:216`). В report метка выводится в `report.py:922-929` из `_self_accepted` (`report.py:516-535`); демонстрируют `test_reports_task_line_marks_a_self_acceptance` (`:248`), committer-вариант (`:274`) и непроверяемый случай `test_reports_task_line_prints_unmarked_when_the_check_cannot_run` (`:306`). Критерий выполнен, но с двумя оговорками ниже (CR-237-A1, CR-237-A2).
- **AC2 (decision по завершённому коммиту).** Деривация переписана в `report.py:551-612`: индекс последнего `completed`, только записи до него, привязка по `completed_commit`/`completed_finding`, приоритет последнего review. Демонстрируют `test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved` (`:338`), `test_a_commit_completed_over_findings_reports_accepted_over_findings` (`:372`), `test_a_finding_completed_over_findings_...` (`:402`), `test_a_commit_approved_after_its_own_acceptance_reports_approved` (`:461`), `test_an_acceptance_bound_to_another_commit_leaves_no_decision` (`:499`), `test_a_review_written_after_the_completion_does_not_change_its_decision` (`:520`), `test_a_task_with_no_completed_record_keeps_todays_decision_rule` (`:553`). Выполнен.
- **AC3 (дельта и архив).** MODIFIED-блок в архивной дельте воспроизводит заголовок и все шесть сценариев требования «Readers keep acceptance over findings…» в том виде, в каком оно стояло до изменения (сверил с диффом `openspec/specs/operator-acceptance/spec.md:128-168`), ADDED даёт два требования и 11 сценариев, у каждого есть тест с докстрингом, называющим сценарий; сценарии MODIFIED-требования по-прежнему покрыты докстрингами в `tests/test_pause_and_operational_acceptance.py:378,493,573,628,656,713`. Спека обновлена так, как это делает `openspec archive`, каталог лежит под `openspec/changes/archive/2026-10-25-...`. Выполнен (сам факт запуска именно 1.15.0 проверить из снапшота нельзя — только по tasks.md 4.2).
- **AC4 (вывод без self-acceptance не изменился).** Фикстуры транскриптов гейта в диффе не тронуты; из существующих тестов изменены только два — `tests/test_display.py:254` под новую сигнатуру `_task_report` и `test_every_output_for_an_acceptance_over_findings_is_unchanged`, где партия заменена на не-писателя ровно по новой формулировке сценария; покрытие метки в `status` остаётся в `tests/test_status_view.py:259-283` и `tests/test_acceptance.py:185-229`, так что снятые там ассерты не образуют дыры. Экранирование не ослаблено: метка — собственный текст инструмента, значения по-прежнему идут через `escape_for_display` (`report.py:911-929`). Выполнен по чтению; прогон CI — по заметке координатора.

**Находки**

CR-237-F1 (блокирующая): докстринги в `src/agentmarshal/journal/report.py:470-479` и `:497-509`, а также комментарий у константы (`:40-48`) и тексты изменения (`design.md` «Decisions», `proposal.md` «Impact», `tasks.md` 2.3) утверждают, что поиск писателей и сравнение — те же, что делает `status_view`, «через `status_view._declared_commit_writers`», что модуль импортируется каждой поверхностью и что «поверхности читают один набор писателей, а не каждая свой git-вызов». По файлам это не так: `report.py` не импортирует `status_view` вовсе, а `status_view.py:48-68` держит свой байт-в-байт такой же `subprocess.run(["git","show",...])`, `status_view.py:71-84` — своё инлайн-сравнение, `status_view.py:807-810` — заново набранную ту же фразу вместо `SELF_ACCEPTED_MARK`. Поведение сейчас совпадает, но заявлено разделение кода, которого нет: правка `report.declared_commit_writers` не дойдёт до `status`, и обе копии разъедутся молча. `status_view.py` вне скоупа контракта — его и не надо было менять; неверны именно утверждения (AGENTS.md: каждое утверждение о коде проверяется по файлу), и их надо либо переписать на «та же проверка, продублированная, потому что `status_view` вне скоупа», либо назвать расхождение departure'ом в отчёте.

CR-237-A1 (advisory): в `report.py:596-612` метка берётся только с «решающей» acceptance, поэтому self-acceptance, не определившая decision, в report не видна вовсе — например, журнал `review(changes_required) → self-acceptance(X) → review(X, approved) → completed(X)` даёт строку `decision=approved` без метки (это ровно `test_a_commit_approved_after_its_own_acceptance_reports_approved`, `tests/test_self_acceptance_on_every_surface.py:461`), и то же для self-acceptance, привязанной к более раннему коммиту. Критерий 1 и ADR-0007 решение 4 формулируют условие как «есть acceptance, чья партия — заявленный писатель кандидата → каждая поверхность, которая докладывает задачу, говорит об этом»; здесь об этом говорит только `status`. Дельта этот выбор проговаривает явно, так что это несоответствие намеренное — но оно шире того, что критерий разрешает, и стоит либо отметки, либо явной записи в требовании.

CR-237-A2 (advisory): гейт выводит метку из идентичностей всего диапазона `merge-base..candidate` (`gate.py:1826`), а `report` и `status` — только из писателей принятого коммита (`report.py:529-535`). На кандидате из нескольких коммитов с разными авторами это расходится: партия, написавшая первый коммит диапазона, но не голову, получает ` (self-accepted: ...)` в транскрипте гейта и пустую строку в `report`, хотя критерий 1 требует «ту же метку» и выводит условие из идентичностей, которые уже читает проверка независимости. Сценарии дельты это расхождение закрепляют («candidate range» против «accepted commit»), поэтому — advisory, а не блок.

CR-237-A3 (advisory, unconfirmed): формат git log в `gate.py:519-522` расширен с `%ae%n%ce` до `%an%n%ae%n%cn%n%ce`, а результат декодируется строго (`_run_git`, `gate.py:311-318`). Значит кандидат, у которого имя автора или коммиттера хранится не в UTF-8 (коммит без заголовка `encoding`, сделанный в однобайтовой локали), теперь валит весь прогон гейта через `GateError: git produced non-UTF-8 output`, тогда как раньше декодировались только адреса, почти всегда ASCII. Воспроизвести не смог — песочница не дала создать репозиторий с таким ident'ом, поэтому помечаю unconfirmed; если риск признан, лечится декодированием этого вызова через `_run_git_lossy`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "6f1c96ca00573001113aa3f62a900c280fa800a2",
  "verdict": "changes_required",
  "findings": ["CR-237-F1"],
  "advisory_findings": ["CR-237-A1", "CR-237-A2", "CR-237-A3"],
  "classes": {
    "CR-237-F1": "claim-accuracy",
    "CR-237-A1": "contract-mismatch",
    "CR-237-A2": "contract-mismatch",
    "CR-237-A3": "correctness"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"self-accepted|_declared_commit_writers|SELF_ACCEPTED\" src/", "result": "status_view.py:48,71,809 keep their own lookup, comparison and literal; report.py:46,470,497 add new ones; gate.py:65,1834 import the constant"},
      {"what": "grep -rn \"_range_emails|_range_writer_identities\" src/ tests/", "result": "only gate.py:505 and gate.py:1826 — no direct test of the emails/identities split"},
      {"what": "grep -rn \"_task_report|build_report(\" src/ tests/", "result": "build_report signature unchanged; the one private call-site updated at tests/test_display.py:254"},
      {"what": "grep -rn \"accepted-over-findings|decision=\" openspec/specs/ docs/", "result": "no other capability spec pins report's decision field or the gate acceptance line; docs/quickstart.md:485 example uses a non-writer party"},
      {"what": "grep -n '\\\"\\\"\\\"Scenario' tests/test_pause_and_operational_acceptance.py", "result": "all six scenarios of the MODIFIED requirement still have tests naming them"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/gate.py:293-530,1700-1960",
      "src/agentmarshal/journal/status_view.py:1-200,772-818",
      "src/agentmarshal/journal/placement.py:64-98",
      "src/agentmarshal/journal/records.py:2027-2041,2193-2236",
      "openspec/specs/operator-acceptance/spec.md",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/{proposal,design,tasks}.md and its operator-acceptance delta",
      "docs/adr/ADR-0007-operator-acceptance.md:100-190",
      "tests/test_self_acceptance_on_every_surface.py",
      "tests/test_pause_and_operational_acceptance.py:640-742",
      "tests/test_gate.py:42-312,1530-1570,3600-3635"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the sandbox refuses to execute python/uv in this snapshot; relying on the coordinator's note that the sequence passed on 6f1c96c"},
      {"what": "git reproduction of a non-UTF-8 author name through git log --format=%an", "why": "creating a repository with that ident was refused by the sandbox — CR-237-A3 stays unconfirmed"}
    ]
  },
  "evidence": {
    "CR-237-F1": "src/agentmarshal/journal/report.py:470-479 and :497-509 claim the lookup and the comparison are status_view's and shared (\"the surfaces read one writer set rather than each keeping its own git call\"), report.py:40-48 claims the mark lives in \"the one module every surface already imports\"; but report.py has no status_view import and src/agentmarshal/journal/status_view.py:48-68, :71-84 and :807-810 still hold their own git call, their own comparison and the retyped literal. Same claim in the archived change: .../tasks.md 2.3 (\"looked up through status_view._declared_commit_writers, imported where it runs\"), design.md Decisions, proposal.md Impact.",
    "CR-237-A1": "src/agentmarshal/journal/report.py:596-612 sets self_accepted only from decisive_acceptance; tests/test_self_acceptance_on_every_surface.py:461-497 asserts the approved-after-its-own-self-acceptance journal prints \"CR-001\\tdone\\treviews=2\\ttokens=0\\tdecision=approved\" with no mark, against contract criterion 1 and ADR-0007 decision 4 (docs/adr/ADR-0007-operator-acceptance.md:117-120).",
    "CR-237-A2": "src/agentmarshal/journal/gate.py:1826 derives the mark from _range_writer_identities(project_root, merge_base, resolved_commit) — every commit of the range — while src/agentmarshal/journal/report.py:529-535 derives it from declared_commit_writers(repository, acceptance[\"accepted_commit\"]) alone; the delta's scenarios encode the same asymmetry (openspec/specs/operator-acceptance/spec.md:326-338).",
    "CR-237-A3": "src/agentmarshal/journal/gate.py:519-522 widened the format to %an%n%ae%n%cn%n%ce and src/agentmarshal/journal/gate.py:311-318 decodes it strictly, raising GateError(\"git produced non-UTF-8 output\"); before the change only %ae/%ce had to decode. Reproduction attempt blocked by the sandbox — unconfirmed."
  }
}
AGENTMARSHAL_VERDICT_END
