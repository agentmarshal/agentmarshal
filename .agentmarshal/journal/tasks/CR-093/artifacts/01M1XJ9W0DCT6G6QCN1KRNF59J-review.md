## Review: CR-093 @ c30c5c688e19134f891fb7679abdb26d9e98bdfa

Проверил реализацию, тесты и openspec-артефакты статически. **Тесты запустить не удалось** — `pytest`/`uv run pytest` в этой сессии не получили разрешения на выполнение (4 попытки, все отклонены). Поэтому критерий 3 («0.3.0 byte-for-byte и sidecar-транскрипты проходят без изменений») и `openspec validate --all` из критерия 4 я подтверждаю рассуждением, а не прогоном.

**Что проверено по существу**

Ядро правки корректно. `_changed_paths` удалён; `changed` теперь `list(dict.fromkeys(...))` над парами `_changed_with_status` — дедуп в порядке листинга, ровно как записано в design.md. Все три читателя (`gate.py:605` пустой диапазон, `gate.py:655` выбор полосы, `gate.py:796` scope) читают этот набор, и других потребителей `changed` в `run_gate` нет. Дельта поведения узкая ровно там, где надо: `--name-only` и так печатал удаления, так что единственное новое — источник rename. Транскрипт не меняется: единственная строка, печатающая пути, — `FAIL: paths outside contract scope`, а `PASS: diff within contract scope` путей не несёт.

Мутационная чувствительность из критерия 1 держится на всех трёх rename-сценариях: при откате `changed` на `git diff --name-only` первый тест получает PASS вместо FAIL, третий уходит на journal-only полосу, а второй ловит подмену через `checked_paths == ["src/original.py", "src/renamed.py"]` — вырожденный до одного пути. Монкипатч `scope_covers` там безопасен: контракт из `_gate_repo` — schema 1, значит `documents` пуст и строка named-documents не делает лишних вызовов.

Существующий `test_gate_refuses_record_rename_out_of_records` не ломается: оба конца переименования лежат внутри журнала, `journal_only` остаётся True.

Архив и спека на месте: `openspec/changes/close-rename-scope-hole/` в дереве отсутствует, `openspec/changes/archive/2026-09-07-close-rename-scope-hole/` полный, `openspec/specs/scope-enforcement/spec.md` написан с Purpose и по формату совпадает с уже валидировавшимся `review-evidence`. Противоречий с ADR-0010 нет — footprint по-прежнему входит в effective scope через ту же строку.

**Advisory-замечания (не блокируют)**

`stale-name-only-doc` — докстринг `scope_warnings` в `src/agentmarshal/journal/open_task.py:90` всё ещё говорит оператору, что гейт сравнивает scope с путями из `git diff --name-only`; после этой правки это неверно (существенное утверждение «git перечисляет файлы, не директории» остаётся истинным). Файл вне scope контракта CR-093, поэтому чинить здесь нельзя — в бэклог.

`duplicate-path-set-derivation` — в `src/agentmarshal/journal/gate.py:837` проверка named documents заново выводит множество путей из `changes_with_status`, отбрасывая статус, хотя `changed` теперь и есть ровно это множество; читателю приходится доказывать, что два вывода совпадают.

`delegating-transcript-test` — `tests/test_gate.py:309` демонстрирует сценарий вызовом другой тест-функции напрямую: он дублирует самый дорогой subprocess-тест и молча скипается вместе с ним, когда 0.3.0 не установлен, так что «демонстрация» сценария — указатель, а не самостоятельная проверка.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c30c5c688e19134f891fb7679abdb26d9e98bdfa", "verdict": "approved", "findings": [], "advisory_findings": ["stale-name-only-doc", "duplicate-path-set-derivation", "delegating-transcript-test"]}
AGENTMARSHAL_VERDICT_END
