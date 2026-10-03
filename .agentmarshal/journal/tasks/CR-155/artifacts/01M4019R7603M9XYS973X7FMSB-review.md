Я прошёл по диффу, по контракту и по названному документу `openspec/specs/record-text-safety/`. Запустить проверки (`uv`, `pytest`, `ruff`, `mypy`) в этой песочнице не вышло — команды требуют одобрения, поэтому пины и новые тесты я сверял вручную по коду, а не прогоном.

Что сошлось:

- `escape_for_display` (`src/agentmarshal/journal/display.py:28`) спрашивает сам `forges_rendered_text`, а не держит свой набор символов, и `tests/test_display.py:34` выводит кейсы из того же предиката по всему диапазону `0x110000` — разойтись они не могут. Замечу, что ветка `\UXXXXXXXX` недостижима (все отказываемые категории `Cc`/`Cs`/`Zl`/`Zp` и bidi-контролы лежат ниже `0xFFFF`), но это задел, а не дефект.
- `status`: в списке задач экранируются `task_id` и `contract.title` (`src/agentmarshal/cli.py:964`), в подробном виде — заголовок, `scope`, строки `Acceptance:` и результат любого рендерера целиком (`status_view.py:155-199`). Диспетчер экранирует возвращённую строку, так что новый рендерер не сможет забыть — это ровно то, что обещает design.md. Табы не трогаются, потому что в `report` и в списке задач они литералы вне экранируемых значений.
- Обрезка до 7 символов сделана до экранирования (`status_view.py:175`), а не после — иначе бы резало escape пополам.
- Пин `tests/test_status_view.py` действительно получил `completed`-строку с привязкой к finding: я прогнал последовательность записей 1..16 через `project_status` вручную — `completed(10) → reopened(11) → finding(12) → completed(13) → reopened(14) → abandoned(15) → session(16)` допустима, итоговое состояние `abandoned` совпадает с ожидаемым. `advisory_findings` не входит в `_SCHEMA_4_FIELDS`, поэтому правило `finding-binding-target` на ревью-записи 2 не срабатывает, а к записи 13 finding 12 уже существует.
- Все 7 сценариев MODIFIED-требования по-прежнему покрыты докстрингами в `tests/test_record_text_safety.py`, 4 новых ADDED-сценария — в `tests/test_display.py` и в пине `tests/test_status_view.py:81`.
- Текст delta и применённый спек совпадают дословно, заголовок MODIFIED-требования не изменён, change заархивирован, `openspec/changes/escape-on-display/` не осталось.

Теперь то, что мешает.

**spec-purpose-contradicts-escaping-on-display** — `openspec/specs/record-text-safety/spec.md:6-7`: раздел `## Purpose` остался нетронутым и до сих пор утверждает, что значение «is refused at the boundary rather than escaped at the edge». В том же файле ниже (строки 66-78) новое требование предписывает именно escaping at the edge. Capability, которую контракт просил перевести «from refusal only to refusal at write and escaping on display», теперь противоречит себе в первом же абзаце: читатель спека получает два взаимоисключающих утверждения о том, что делает инструмент. По AGENTS.md:21-22 Purpose пишется в delta change-а, и архивная команда его оттуда переносит — в `openspec/changes/archive/2026-10-03-escape-on-display/specs/record-text-safety/spec.md` секции `## Purpose` нет (предыдущий change `2026-09-24-narrow-the-forgeable-text-rule` её нёс), поэтому старая формулировка и уцелела. Править `openspec/specs/` руками нельзя — нужна секция `## Purpose` в delta и повторный архив.

**report-escapes-derived-labels-not-record-text** (advisory) — `src/agentmarshal/journal/report.py:148` и `:156` экранируют `task.state` и `task.decision`, хотя оба значения приходят из закрытых наборов: `state` — только из таблицы `_RECORD_TYPE_STATES` (`status.py:33`), `decision` — из литералов `"approved"` / `"accepted-over-findings"`. Это текст самого инструмента, а спек прямо говорит «never to the tool's own fixed text». Два следствия: `tests/test_display.py:223` вынужден подсунуть невозможное `state="open\u202estate"`, то есть пинит поведение для значения, которое на диске возникнуть не может; и `status_view.py:159` печатает тот же самый `task.state` без экранирования — одна из двух сторон лишняя. Ничего не ломается (экранирование здесь no-op), но стоит выбрать одну трактовку.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b7684935e01132bcdac1af188d491b8c153b09fa",
  "verdict": "changes_required",
  "findings": ["spec-purpose-contradicts-escaping-on-display"],
  "advisory_findings": ["report-escapes-derived-labels-not-record-text"]
}
AGENTMARSHAL_VERDICT_END
