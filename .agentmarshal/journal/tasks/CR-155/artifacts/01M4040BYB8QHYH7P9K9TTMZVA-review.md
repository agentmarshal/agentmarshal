Review completed — read-only, static (the sandbox here has no `uv`/`python3` execution, so I verified the CI criterion by reading the code and tracing the tests by hand rather than running them; I say that plainly rather than claiming a green run).

## Что проверил

**Критерий 2 — функция экранирования.** `src/agentmarshal/journal/display.py:27` `escape_for_display` спрашивает сам предикат `forges_rendered_text` для каждого символа, а не держит собственный набор. `\n`, `\r`, `\t` через `_NAMED_ESCAPES`, остальное — `\uXXXX`/`\UXXXXXXXX` в нижнем регистре. `tests/test_display.py` прогоняет всю плоскость 0x0–0x10FFFF посимвольно и сверяет обе стороны — и экранируемые, и принимаемые. Дрейф между правилом записи и отображением ловится. Форма `\UXXXXXXXX` сегодня недостижима через реальный предикат (`Cc/Cs/Zl/Zp` + bidi — всё внутри BMP), и тест честно это называет и показывает форму через подменённый предикат, а не делает вид, что она достижима.

**Критерий 3 — status.** Список задач (`cli.py:964`) экранирует `task_id` и `contract.title`; `task.state` — производная из закрытого `_RECORD_TYPE_STATES`, не из записи. Детальный вид (`status_view.py:151`) экранирует заголовок, scope, поля acceptance-сводки и — главное — результат рендерера целиком в точке диспетчеризации, так что новый рендерер не может забыть. Усечение `[:7]` сделано до экранирования, а не после, иначе длина поехала бы. Проверил по реальному коду: `contracts.py` не пропускает `title` и `scope` через `forges_rendered_text` (только `documents`/`decisions`/`extensions`), то есть вектор через контракт достижим сегодня, и тест списка задач бьёт именно в него.

**Критерий 4 — report.** `format_report` экранирует `task_id` и оба `usage_provenance`; `state`, `decision`, счётчики — производные. Единственное реально достижимое враждебное значение здесь — `usage.method` из старой session-записи, и оно покрыто на обоих уровнях (задача и Summary).

**Критерий 5 — ничего не сломалось.** Экранирование — no-op для чистых значений, так что существующие пины не двигаются. Прошёл руками по изменённому `test_status_view.py`: последовательность записей `…completed(13) → reopened(14) → abandoned(15) → session(16)` проходит `project_status` (reopened допустим только после `done`, session — после любого терминала), итоговое состояние остаётся `abandoned`, порядок файлов лексикографический совпадает с ожидаемым, а `create_completed_record(..., None, completed_finding=…)` удовлетворяет «ровно одно из двух». Ожидаемый вывод сходится построчно с рендерерами.

**Критерий 1 — спека.** Все семь сценариев MODIFIED-требования уже покрыты тестами с называющими их docstring'ами в `test_record_text_safety.py`; четыре сценария ADDED-требования — в `test_display.py` и `test_status_view.py:81`. Заголовок MODIFIED-требования совпадает с базовым дословно; дельта применена к `openspec/specs/record-text-safety/spec.md` без потерь. `## Purpose` оставлен — это зафиксированный non-goal с поправкой к контракту.

## Прозa к находке

Advisory `stale-refusal-rationale`: docstring `_reject_control_characters` в `src/agentmarshal/journal/records.py:856` всё ещё утверждает «So the record is refused rather than the display escaped» — после ADR-0015 решения 5 и нового требования спеки это уже не «вместо», а «и то, и другое», и читатель `records.py` получает описание отвергнутой альтернативы как действующего решения. Поправить здесь нельзя: `records.py` не входит в scope контракта, так что это заметка для следующей задачи (той, что возьмёт gate/brief/prompt), а не замечание к этому диффу.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "07ec3b541992d7119e3a64f2cb260aefb6d07858", "verdict": "approved", "findings": [], "advisory_findings": ["stale-refusal-rationale"]}
AGENTMARSHAL_VERDICT_END
