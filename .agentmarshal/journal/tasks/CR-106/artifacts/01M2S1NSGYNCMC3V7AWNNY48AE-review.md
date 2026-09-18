Я прочитал diff, `records.py` (валидацию и `write_record`), ADR-0004 и связанные с ним места. Тесты и линтеры запустить не получилось: sandbox не пропустил команды без одобрения. Поэтому ревью статическое.

**Что проверено:**
- **Словарь определён один раз.** `_SESSION_ACTIVITIES` объявлен только в `records.py`. `backfill.py` и help в `cli.py` берут его оттуда: копия в backfill удалена, строка в help больше не захардкожена.
- **Schema 6 стоит только у coordination-записей.** Номер выбирает `session_record_schema()`. Его вызывают и live-writer, и backfill, поэтому для `implementation`/`review`/`other` остаётся 3, как было раньше. Число 6 добавлено в `_SUPPORTED_SCHEMAS`. Validator отказывает `coordination`, если schema меньше 6, по тому же образцу, что `reviewed_contract` и schema 5.
- **Отход от floor rule из ADR-0004 оформлен.** Правило написано для полей, а здесь новое значение. В design.md это объяснено, так что противоречия с ADR нет.
- **Каждый сценарий delta spec покрыт тестом.** В `tests/test_session.py` у каждого теста docstring называет свой сценарий. Для отказа проверяется, что `journal_root` не создан.
- **Фикстура в `test_attestation.py` сдвинута с 6 на 7.** Это разрешено поправкой к контракту.
- **Полей с деньгами или ценой не добавлено.** Изменения укладываются в scope.

**Advisory:** `cli.py:50` и `backfill.py:31` импортируют из `records.py` приватное имя `_SESSION_ACTIVITIES`. Раз словарь теперь общий для нескольких модулей, лучше дать ему публичное имя, например `SESSION_ACTIVITIES`. Тогда общий контракт не будет держаться на имени, которое по соглашению считается внутренним для модуля. На корректность это не влияет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cdf1f7bd9f69371be71094003499872feb16ed47", "verdict": "approved", "findings": [], "advisory_findings": ["private-vocabulary-import"]}
AGENTMARSHAL_VERDICT_END

Кстати: коннекторы claude.ai Gmail, Google Calendar и Google Drive требуют авторизации в настройках коннекторов на claude.ai. Для этого ревью они не нужны.
