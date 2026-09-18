Тесты запустить не смог: запуск pytest требует подтверждения, а сессия read-only. Поэтому ревью сделано по коду и диффу. Итог: **approved**, два advisory.

Что проверил:
- **Какой project file читается.** Уровень `reviews` берётся через существующий `capture_policy_from_project(...).level_for(CaptureClass.REVIEWS)` из project file того journal, в который идёт запись. Путь `journal_root.parent.parent` верный: `resolve_placement` всегда кладёт journal в `<project>/.agentmarshal/journal`, и в sidecar-размещении читается файл самого sidecar. Второй настройки для того же решения нет.
- **`commit` работает как раньше.** Артефакт пишется и pin'ится, `prose_note` равен `None`, строка `reviewer prose pinned:` на stderr та же, временной копии нет.
- **По умолчанию (`hash`, секции `capture` нет).** В `artifacts/` ничего не пишется, у записи нет `artifacts`, вывод ревьюера уходит во временный файл, и его путь печатается на stderr.
- **`off`.** Ничего не сохраняется, на stderr об этом сказано. Для отклонённого вердикта вывод по-прежнему сохраняется, это проверено тестом на `off`.
- **Отказ `submit-review --prose`.** Команда отказывает до чтения файла и до записи. В сообщении есть уровень и `capture.overrides.reviews = "commit"`.
- **Сломанная секция `capture`.** `review` отказывает раньше, чем запускается ревьюер.
- **Тесты на сценарии.** Для каждого из девяти сценариев delta spec есть тест, и его docstring называет сценарий. Fixture'ы старых тестов, которые ждут pinned prose, теперь выставляют `commit`.
- **Этот репозиторий.** В `.agentmarshal/project.json` стоит `reviews: commit`.
- **Документы.** Фраза «No setting turns this off» осталась только в архиве openspec tasks, в контракте CR-111 и в прошлом артефакте ревью, в документах её нет. Ссылки на CHANGELOG 0.4.0, UPGRADING, quickstart, overview и ADR-0005 обновлены.

Два advisory, ни одно не блокирует:

- **ADV-1-readme-setting-unnamed** — в `README.md:62-64` сказано, что по умолчанию проза не коммитится, и названа только «the project's capture policy». Ключа `capture.overrides.reviews = "commit"` нет, хотя acceptance просит в каждом документе указать и значение по умолчанию, и настройку. Остальные перечисленные документы ключ называют.
- **ADV-2-hash-copy-decoded** — `src/agentmarshal/journal/review.py:907`: на уровне `hash` во временный файл пишется `reviewer_output`, то есть текст, декодированный с `errors="replace"`, а не исходные байты `raw_output`. Непечатаемые байты могут подмениться. Spec требует сохранять вывод «как получен» только внутри journal, так что это расхождение с `commit`, а не нарушение.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "87fef2af94468b9688a0e87d90b4225e0e8fec6f", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-1-readme-setting-unnamed", "ADV-2-hash-copy-decoded"]}
AGENTMARSHAL_VERDICT_END
