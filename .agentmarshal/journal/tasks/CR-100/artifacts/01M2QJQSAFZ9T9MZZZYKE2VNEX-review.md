Проверил diff статически — выполнить тесты в этой песочнице нельзя (запуск Python не разрешён), так что ниже разбор по коду, спекам и существующим тестам.

**Что сходится с контрактом**

- Все сценарии из `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/` имеют тест, чей docstring называет сценарий (8 в leak-scan, 2 в reviewer-adapter).
- Отступление от формулировки threat model про «sole occurrence» записано в `design.md` явным пунктом — acceptance #1 это разрешает.
- Рендерер один (`render_leak_hits`), и `tests/test_gate.py:1775` пинит обе строки — gate и standalone — в одном тесте, так что разъехаться они не могут.
- `PROJECT_CONFIG_RELPATH` действительно единственное написание: `_PROJECT_FILE` из `gate.py` убран, других литералов в `src/` нет.
- Byte-for-byte транскрипт (`test_embedded_diff_lane_transcript_matches_published_030_byte_for_byte`) гоняется на чистом кандидате — строки WARN там нет, ожидания не тронуты. Pinned-prompt тесты сравниваются с `review._review_prompt(...)`, добавленный `sys.stderr.write('')` в стабе на них не влияет, а на ненулевом выходе `detail` по-прежнему падает обратно на stdout.
- `test_gate_leak_scan_reads_markers_from_base_not_candidate` не ломается новым подавлением: маркер там в *удалённой* строке `project.json`, а добавленная — пустой список.

Теперь замечания. Блокирующих нет, все ниже — advisory.

`diff-dev-null-drops-added-lines` — в `src/agentmarshal/journal/capture.py:361` и `:444` значение `None` из `_diff_path` служит сразу двумя вещами: «назначения нет» и «содержимое не сканировать». После заголовка `+++ /dev/null` все добавленные строки последующего ханка молча выбрасываются, тогда как до этой правки они попадали в `scan_for_leaks`. Для сканера секретов это fail-open, и у кода уже есть подходящий безопасный запасной вариант — плейсхолдер `"(unknown file)"` из строки 361. Через `git diff` такая форма не порождается, но docstring функции обещает корректный разбор любого unified diff.

`safe_path-collapses-distinct-files` — в `src/agentmarshal/journal/capture.py:297` описание пути не зависит от самого пути, а `hits` в строке 407 это `set`. Два разных файла, чьи пути содержат один и тот же маркер (`a/internal.corp/x.json` и `b/internal.corp/y.json`, оба с маркером в содержимом), дают одинаковый `LeakHit("<a path containing private marker #1>", "private-marker #1")` и схлопываются в один. Оператор видит одно место утечки вместо двух — ровно та потеря «где», которую задача чинила.

`diagnostics-lost-when-preservation-fails` — в `src/agentmarshal/journal/review.py:341` при `OSError` заметка сообщает, что байты сохранить не удалось, но сами байты никуда не выводятся. Предупреждение wrapper'а при этом теряется полностью, а именно это маскирование и описано в proposal 021. Отказ не выдавать их в stdout обоснован (его парсят), но stderr свободен и туда уже идёт сама заметка.

`launched-review-not-exported` — `launch_review` реэкспортируется из `src/agentmarshal/journal/__init__.py:25` и в `__all__`, а её новый тип возврата `LaunchedReview` — нет, хотя снятый оттуда `SubmittedReview` остался. Импортирующий из пакета не может назвать тип результата.

`sidecar-doc-describes-old-warn-line` — `docs/sidecar.md:247` говорит, что gate добавляет `WARN: possible leak in candidate additions (advisory, not blocking)` «with the markers it matched». Теперь строка несёт `файл: что совпало`, и формулировка описывает снятое поведение. `docs/` вне scope контракта, так что это заметка на следующую задачу, а не требование к этому диффу.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "945cbf4757d8676b7baafc10095932f83713de21", "verdict": "approved", "findings": [], "advisory_findings": ["diff-dev-null-drops-added-lines", "safe_path-collapses-distinct-files", "diagnostics-lost-when-preservation-fails", "launched-review-not-exported", "sidecar-doc-describes-old-warn-line"]}
AGENTMARSHAL_VERDICT_END
