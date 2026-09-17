Изучил дифф, исходники, спеки и ADR-0005. Резюме проверки:

**Что сходится с контрактом**

- `render_leak_hits(hits, limit)` — один рендерер, обе точки вызова обновлены (`cli.py:1309` c `limit=None`, `gate.py:1187` c `limit=_LEAK_HIT_RENDER_LIMIT`). Больше вызовов в дереве нет (grep по `src/`, `tests/` чист), своей копии формы хита ни у одного caller'а не появилось.
- Граница двадцати переехала из `capture.py` в `gate.py:62` с комментарием, объясняющим, почему она принадлежит транскрипту — ровно решение «The bound is the caller's, the rendering is shared» из design.md. Счётчик остался внутри той же строки (решение «The count is part of the bounded rendering»), число не менялось.
- Обе новые сценарные проверки покрыты тестами с докстрингами, называющими сценарий: `tests/test_gate.py:1809` и `tests/test_leak_scan.py:66`. Хиты сортируются (`scan_diff_for_leaks` возвращает `sorted(hits)`), поэтому `secret00…secret19` показываются, `secret20` — нет, и `", and 1 more not shown"` детерминирован. Хелперы `_implement`/`_add_file` коммитят накопительно в одну ветку, так что в `head` действительно все 21 файл. Остальные сценарии требования (built-in signature, private marker, оба пути-секрета, отказ артефакта, merge boundary) уже имеют такие докстринги в `test_capture.py`/`test_gate.py`.
- `docs/sidecar.md:245-253` описывает строку в точности так, как её печатает `gate.py:1181` и `gate.py:1185-1188`, включая `(<reason>)` у skipped — это и есть то, что ожидает `tests/test_gate.py:1797`.
- Delta-спека и опубликованная `openspec/specs/leak-scan/spec.md` синхронны: MODIFIED-требование воспроизведено целиком, новый абзац про bound и два сценария добавлены в опубликованную capability.
- `LaunchedReview` добавлен и в импорт, и в `__all__` (`journal/__init__.py:25,45`), строка импорта ровно 88 символов — в лимит ruff укладывается.
- Противоречий с ADR-0005 нет: сканирование остаётся advisory, ничего про блокировку не менялось.

**Замечание (не блокирующее)**

ADV-EXPORT-TEST-DOES-NOT-PIN-ALL — тест `test_launched_review_is_exported_from_the_journal_package` в `tests/test_journal.py:91-97` проверяет только, что имя импортируется из `agentmarshal.journal` и совпадает с классом из `journal.review`. Заявленный же долг — отсутствие `LaunchedReview` в `__all__` пакета; удаление строки `"LaunchedReview"` из `__all__` (`src/agentmarshal/journal/__init__.py:45`) при сохранённом импорте оставит тест зелёным, хотя `from agentmarshal.journal import *` снова перестанет отдавать имя. Буква acceptance-критерия («can be imported … pinned by a test») выполнена, но регрессия именно экспорта не запинена.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "0ca8c9de586dc34434d9651f84dbc58524721c06", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-EXPORT-TEST-DOES-NOT-PIN-ALL"]}
AGENTMARSHAL_VERDICT_END
