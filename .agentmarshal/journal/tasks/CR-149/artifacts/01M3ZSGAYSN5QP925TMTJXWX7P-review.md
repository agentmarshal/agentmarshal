Разобрал изменение: перенос `_print_task_detail` и двух его хелперов в `src/agentmarshal/journal/status_view.py`, замена if-цепочки на реестр `_RECORD_RENDERERS`, новый pinning-тест и правка цели monkeypatch в существующем тесте.

Что проверил построчно:

- Рендереры в `status_view.py:61-134` воспроизводят прежние строки символ в символ, включая склейку f-string'ов для `abandoned`/`reopened`/`amendment` (пробел перед `reason=` сохранён), ветки `reviewed_finding`/`reviewed_commit`, `accepted_finding`/`accepted_commit`, `completed_finding`/`completed_commit`, суффикс ` artifacts=N` только при непустом списке и маркеры ` self-accepted`/` self-acceptance-unchecked`.
- `print_task_detail` (`status_view.py:148-183`) сохраняет порядок вывода: шапка → цикл по acceptance → `Scope:` (с `- (none)`) → `Records:`; generic-строка `id / record_type / created_at` выдаётся при отсутствии записи в реестре, что и требует критерий 2.
- `cli.py` оставил только вызов (`cli.py:972`) и импорт (`cli.py:71`); удаление `cast` и `TaskStatus` из импортов корректно — в файле больше нет ни одного их употребления, а `subprocess` остался нужен (`cli.py:1066`). Циклического импорта нет: `status.py` про `status_view` не знает.
- Pinning-тест покрывает все семь типов с выделенной строкой плюс `opened` и `session` через generic-строку, и опирается только на публичный `main(["status", ...])`, то есть проходит и на коде до переноса. Идентификаторы записей — валидные ULID (26 символов, первый `0`), порядок файлов совпадает с ожидаемым выводом (`read_records` сортирует по имени), последовательность lifecycle-записей даёт состояние `abandoned`, как и зафиксировано.

Ограничение этого ревью: в песочнице выполнение команд не разрешено, поэтому `uv run pytest / ruff / mypy / agentmarshal validate` я не запускал — критерий 4 проверен только статически (мёртвых импортов нет, самая длинная новая строка `status_view.py:128` ровно 88 символов при `line-length = 88`, набор правил ruff `ARG` не включает, так что неиспользуемый `_project_root` не ругается).

Два необязательных замечания:

Критерий 3 требует, чтобы все существующие status-тесты проходили без изменений, но `tests/test_acceptance.py:214,220` всё-таки пришлось поправить — monkeypatch теперь целится в `agentmarshal.journal.status_view._declared_commit_writers`. Это неизбежное следствие переноса приватного хелпера (альтернатива — реэкспорт из cli.py — не сработала бы, так как `_is_self_accepted` вызывает имя из своего модуля), утверждения теста не тронуты, но как отступление от формулировки критерия это стоило назвать в отчёте.

Ветка `completed_finding` рендерера `completed` (`status_view.py:104-110`) не зафиксирована ни новым тестом, ни остальным сьютом: в `tests/test_status_view.py` `completed` присутствует только в commit-варианте, а единственное употребление `completed_finding` в тестах (`tests/test_findings.py:398`) проверяет gate, а не вывод status. Для задачи, чья ценность — именно сетка пинов перед шестью последующими правками этого модуля, эту ветку было бы логично добрать.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "c3b3c371053d4e209ba50dd77fdc8850ab2a96d3",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-existing-status-test-edited",
    "advisory-completed-finding-line-unpinned"
  ]
}
AGENTMARSHAL_VERDICT_END
