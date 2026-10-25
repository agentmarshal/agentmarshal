Разобрал контракт, диффы и окружающий код. Ниже — прозой: по каждому acceptance criterion и по двум advisory-находкам.

**Что проверял по acceptance criteria**

AC-1 (gate отказывает любому added-пути под `tasks/<id>/records/`, остаток которого содержит `/`, одной FAIL-строкой с именем пути, одинаково для судимой и для любой другой задачи) — выполнен. Шейп-проверка живёт в `_record_path_task` (`src/agentmarshal/journal/gate.py:403`): путь считается record-путём только при ровно трёх непустых сегментах после `.agentmarshal/journal/tasks/` со средним `records`, то есть именно та форма, которую принимает `read_records` (`src/agentmarshal/journal/records.py:2745-2756`). Вызывается она в added-records-чеке до `git show` (`gate.py:2148-2155`), поэтому вложенный путь отклоняется по имени, не по байтам. Проверено, что `_is_record_path` остался шире (`gate.py:389`), так что вложенный файл по-прежнему попадает под append-only через `_is_append_only_evidence_path` (`gate.py:421-426`) — комментарий в docstring это утверждает и это правда. Демонстрируют: `test_gate_refuses_a_record_nested_below_another_tasks_records` (journal-only, чужая задача), `test_gate_refuses_a_nested_record_on_the_implementation_lane` (implementation, чужая задача), `test_gate_refuses_the_judged_tasks_nested_record_on_the_implementation_lane` (implementation, судимая задача). Вычисление задачи для flat-пути не изменилось: `parts[0]` даёт ровно то же, что прежний `removeprefix(...).split("/", 1)[0]`, поэтому happy-path и pinned-транскрипты не сдвигаются.

AC-2 (вложенный путь под records/ самой судимой задачи даёт ту же FAIL-строку, а не безымянную ошибку или traceback) — выполнен. `load_task_status` теперь не бросает сразу, а откладывается (`gate.py:1260-1266`), и ветка `if task is None:` (`gate.py:1343-1368`) печатает `NOT EXAMINED` с настоящей причиной и FAIL со списком путей. Проверил, что это безопасно: `JournalRecordError` — подкласс `ValueError` (`records.py:327`), так что `read_records`' «record path is not a file» ловится; между try и guard'ом `task` нигде не разыменовывается (все обращения к `task.` начинаются с `gate.py:1419`); при пустом диапазоне и в sidecar старое поведение сохранено явными `raise` (`gate.py:1287`, `gate.py:1368`); `escape_for_display` трогает только control/format/bidi-категории (`display.py:27-43`, `records.py:1898-1909`), поэтому угловые скобки в `<id>`/`<file>` в транскрипт попадают как есть. Демонстрирует `test_gate_fails_a_record_nested_below_the_judged_tasks_records`: он гоняет CLI на checkout'е кандидата, ждёт код 1, FAIL-строку в stdout, отсутствие `Traceback` и отсутствие голой ошибки reader'а в stderr. Отложенный `raise` не ломает существующие пины — `test_gate_refuses_reopening_only_append_to_abandoned_task` и `test_gate_refuses_review_only_append_to_closed_task` проходят через новую ветку и получают то же сообщение, потому что их added-записи имеют валидный шейп.

AC-3 (тесты на настоящих временных git-репозиториях, четыре комбинации лейн × задача, байт-идентичные фикстуры, зелёный CI) — выполнен в той части, что я могу проверить чтением. Все четыре новых теста строятся на `_gate_repo`/`_candidate_head`/`_commit_all`/`_gate_arguments`, то есть на реальных `git init`/`commit`/`switch`; четыре комбинации покрыты (чужая задача journal-only и implementation, судимая задача journal-only через CLI и implementation). Фикстуры `tests/fixtures/gate/*` диффом не тронуты, а `test_default_run_transcript_matches_the_committed_fixture` их пинит. Прогнать сам CI-набор я не смог — snapshot не git-репозиторий и запуск команд в этой песочнице не разрешён, так что опираюсь на заявление координатора о зелёном CI на 4f42123.

**ADV-1 — комментарий обещает больше, чем проверяет условие** (`src/agentmarshal/journal/gate.py:1344-1349`). Комментарий говорит: ветка срабатывает, «когда added-пути самого кандидата объясняют» нечитаемость судимой задачи. Условие на `gate.py:1350-1352` слабее — оно берёт любой added-путь с неподходящим шейпом, включая путь под *другой* задачей. Достижимый сценарий ровно из non-goals контракта: журнал уже содержит `tasks/CR-001/records/sub/` от прежнего плохого merge, и новый journal-only кандидат добавляет `tasks/CR-002/records/sub/<ULID>-session.json`. Тогда `gate --task CR-001` печатает FAIL с именем пути CR-002, хотя нечитаемость CR-001 кандидат не вызывал; настоящая причина остаётся только внутри `NOT EXAMINED`-строки. Отказ по существу верный и причина из транскрипта не исчезает, поэтому это advisory, а не блокер — но утверждение в комментарии стоит сузить до того, что код действительно делает.

**ADV-2 — шейп record-пути задублирован в gate.py без пина к reader'у** (`src/agentmarshal/journal/gate.py:403-419` против `src/agentmarshal/journal/records.py:2745-2756`). `_record_path_task` заново кодирует то, что принимает `read_records`, и ни один тест не связывает две стороны: новые тесты пинят только вложенный случай. Если reader однажды изменит набор принимаемых записей, gate об этом не узнает — то есть снова откроется ровно тот класс расхождения, который закрывает эта задача. ADR-0004 decision 6 кладёт знание о чтении/проекции журнала за loader-шов, и в этом файле проект уже держит такую же мысль явно (ср. `display.py:30-32`: «the same predicate the writer consults, so the two sides cannot drift»). Советую либо один общий предикат, либо тест, который утверждает совпадение принимаемых форм.

Блокирующих находок нет: ни один путь изменения не делает gate мягче — при `task is None` код либо возвращает `passed=False`, либо бросает, а при успешной загрузке поведение прежнее.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4f42123d08d85838af8aa11064ffc3c014a91b84",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1", "ADV-2"],
  "classes": {
    "ADV-1": "claim-accuracy",
    "ADV-2": "test-gap"
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/journal/gate.py:1344-1349 comment claims the branch fires only when 'the candidate's own added paths explain why'; the condition at src/agentmarshal/journal/gate.py:1350-1352 is `sorted(path for path in added_records if _record_path_task(path) is None)` over all added records, including paths under another task, so a nested path under tasks/CR-002/records/ triggers the FAIL-and-return even when CR-001's unreadability is pre-existing (the contract's own non-goal case)",
    "ADV-2": "src/agentmarshal/journal/gate.py:403-419 (_record_path_task) re-encodes the accepted shape that src/agentmarshal/journal/records.py:2745-2756 (read_records: is_file / filename pattern) enforces; grep of tests/test_gate.py for the four new tests shows they pin only the nested case, no test ties the two shapes together; ADR-0004 decision 6 (docs/adr/ADR-0004-journal-data-model.md, 'All journal I/O goes through the recorder (write) and loader (read/projection) APIs') places that knowledge behind the loader seam"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/gate.py:83-200 (constants, GateError, GateReport, run_findings_gate)",
      "src/agentmarshal/journal/gate.py:380-430 (_is_record_path, _record_type_from_record_path, _record_path_task, _is_append_only_evidence_path)",
      "src/agentmarshal/journal/gate.py:1197-1470 (run_gate preamble, deferred load, empty-range raise, base_tree, record_changes, the new task-is-None branch, lane selection)",
      "src/agentmarshal/journal/gate.py:1640-1700 (contract-from-base-tree raises)",
      "src/agentmarshal/journal/gate.py:2135-2290 (added-records check, collisions, cross-task lifecycle loop)",
      "src/agentmarshal/journal/gate.py:2410-2425 (final GateReport)",
      "src/agentmarshal/journal/records.py:327-330, 2700-2778 (JournalRecordError, validate_record_content, read_records)",
      "src/agentmarshal/journal/records.py:1898-1930 (forges_rendered_text, _reject_control_characters)",
      "src/agentmarshal/journal/records.py:2330-2360 (create_session_record signature)",
      "src/agentmarshal/journal/status.py:65-180 (TaskStatusError, load_task_status, load_task_for_record)",
      "src/agentmarshal/journal/display.py:27-43 (escape_for_display)",
      "src/agentmarshal/journal/gate_context.py:1-125 (derive_gate_context)",
      "src/agentmarshal/journal/artifacts.py:1-78 (artifact path shape)",
      "src/agentmarshal/journal/complete.py:50-110 (run_gate caller)",
      "src/agentmarshal/cli.py:955-1010, 1075-1120 (gate CLI transcript printing and exit codes)",
      "tests/test_gate.py:1-45, 87-200, 300-430, 1857-1900 (imports and real-git helpers)",
      "tests/test_gate.py:2057-2200 (the four new tests and _add_nested_record)",
      "tests/test_gate.py:2295-2325, 2495-2565 (existing GateError pins through the deferred load)",
      "tests/fixtures/gate/ (listing: fixtures untouched by the diff)",
      "docs/adr/ADR-0004-journal-data-model.md:1-90",
      "pyproject.toml:47-69 (ruff and mypy configuration)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "command execution is not permitted in this review sandbox (every attempt, including `uv --version` and `python3 -c`, was refused as requiring approval); the CI result is taken from the coordinator's note on 4f42123d08d85838af8aa11064ffc3c014a91b84"},
      {"what": "git inspection of the reviewed commit", "why": "the supplied snapshot at /tmp/agentmarshal-review-k6dhzza5/snapshot is not a git repository, so only the file contents and the supplied diff could be read"}
    ]
  }
}
AGENTMARSHAL_VERDICT_END
