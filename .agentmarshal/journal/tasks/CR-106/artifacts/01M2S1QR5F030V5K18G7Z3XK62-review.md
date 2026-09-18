Я прочитал diff, ADR-0004 и ADR-0005, `records.py` и `backfill.py` в снапшоте, а также новые тесты. Запустить pytest не получилось: команда требует подтверждения, а сессия неинтерактивная. Поэтому то, что тесты проходят, я не проверял, а вывел из кода.

**Что соответствует контракту:**
- **Словарь определён один раз.** `_SESSION_ACTIVITIES` задан только в `records.py:152`. `backfill.py` и `cli.py` импортируют его, а не держат свою копию. Поиск по `src/`, `tests/`, `docs/` и `templates/` других копий не нашёл: совпадения есть только в параметризации теста и в тексте proposal 018.
- **Номер схемы.** `session_record_schema()` ставит 6 только для `coordination` и 3 для остальных трёх activity. Им пользуются и обычный writer, и backfill. Валидатор отказывает записи с `coordination`, если схема ниже 6. Это то же «правило пола» из ADR-0004, что уже работает для `_SCHEMA_5_FIELDS`.
- **Сценарии покрыты тестами.** На каждый из четырёх сценариев delta spec есть тест в `tests/test_session.py`, и docstring называет сценарий. Тест на «nothing is written» корректен: `write_record` валидирует запись до `_prepare_record_directory`.
- **Остальное по контракту.** Полей с деньгами или ценой нет. Правка фикстуры в `tests/test_attestation.py` (6 → 7) укладывается в поправку к контракту. ADR-0005 не нарушен: тип записи и predicateType не меняются.
- **Поведение backfill.** Раньше `coordination` из v1-stat превращалось бы в `other`, теперь оно сохраняется со схемой 6. Именно так это и описано в design.md.

**Одно замечание, не блокирующее:**

`cli.py:50` и `backfill.py:31` импортируют приватное имя `_SESSION_ACTIVITIES` из другого модуля. Словарь теперь стал общим API, поэтому ему лучше дать публичное имя, например `SESSION_ACTIVITIES`.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cdf1f7bd9f69371be71094003499872feb16ed47", "verdict": "approved", "findings": [], "advisory_findings": ["private-vocabulary-import"]}
AGENTMARSHAL_VERDICT_END

Коннекторы claude.ai Gmail, Google Calendar и Google Drive не авторизованы. Для этого ревью они не нужны, но пользоваться ими нельзя, пока ты не подключишь их в настройках коннекторов на claude.ai.
