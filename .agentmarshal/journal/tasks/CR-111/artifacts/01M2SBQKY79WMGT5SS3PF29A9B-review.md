Ревью закончено. Верди­кт — **approved**, блокирующих находок нет, есть две advisory. Тесты я не запускал: вызовы pytest в этой сессии требуют подтверждения, так что всё ниже проверено только чтением кода.

**Что проверил и что в порядке:**
- **Сценарии delta spec.** Каждый из девяти покрыт тестом с docstring `Scenario: …`. Новые пять лежат в `tests/test_review_capture.py`. Модифицированные четыре — в `tests/test_review_launcher.py` и `tests/test_journal.py`, их фикстуры теперь явно ставят `commit`.
- **Откуда берётся уровень.** Оба пути читают его через существующий `capture_policy_from_project(...).level_for(CaptureClass.REVIEWS)`, вызов идёт из `review_capture_level_from_journal` (`src/agentmarshal/journal/capture.py:250`). Файл проекта берётся по `journal_root.parent.parent`. Это корректно: `placement.py:77` всегда кладёт журнал в `<project>/.agentmarshal/journal`, в sidecar-размещении тоже. Второй настройки нет.
- **`agentmarshal review`.** Уровень определяется до запуска ревьюера, поэтому битая секция `capture` не тратит прогон. При `commit` в `submit_review` уходит `prose=raw_output`, как раньше, и строка `reviewer prose pinned:` на stderr не изменилась. При `hash` вывод идёт во временный файл, путь печатается на stderr. При `off` ничего не сохраняется, на stderr об этом сказано. Отказ от вердикта при любом уровне по-прежнему сохраняет вывод через `_reject`.
- **`submit-review --prose`.** Отказывает до любой записи, если уровень не `commit`. В сообщении есть и уровень, и `capture.overrides.reviews = "commit"`.
- **Этот репозиторий.** В `.agentmarshal/project.json` стоит `reviews: commit`.
- **Расхождение с ADR-0005.** По ADR-0005 `hash` означает приватное хранилище, а здесь это временный файл. Это отступление записано в `design.md` с обоснованием. Фраза «No setting turns this off» больше не встречается ни в одной документации.

**Advisory-находки:**

`adr0004-status-note-stale`: в `docs/adr/ADR-0004-journal-data-model.md:105-110` заметка «Status in 0.4.0» по-прежнему говорит, что policy-driven artifact writer не существует и что принятый вывод ревьюера сохраняется как hash-pinned артефакт журнала. После этого изменения оба утверждения неверны для дефолтного уровня `hash`. Этого ADR нет в перечне документов из acceptance, поэтому находка не блокирующая.

`readme-setting-not-named`: `README.md:62-65` сообщает дефолт («by default it is not») и говорит, что решает capture policy. Но конкретную настройку `capture.overrides.reviews = "commit"` README не называет, хотя остальные документы из перечня называют.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "87fef2af94468b9688a0e87d90b4225e0e8fec6f", "verdict": "approved", "findings": [], "advisory_findings": ["adr0004-status-note-stale", "readme-setting-not-named"]}
AGENTMARSHAL_VERDICT_END
