Я проверил diff CR-106 по контракту, ADR-0004, ADR-0005 и спеке `openspec/specs/session-activity/`. Блокирующих проблем нет. Тесты я не запускал: `uv run pytest` требовал подтверждения, которого не было. Поэтому всё ниже проверено только чтением кода и grep.

**По критериям приёмки:**
- **Vocabulary определён один раз.** `_SESSION_ACTIVITIES` задан только в `records.py:152`. `backfill.py` свою копию удалил и импортирует этот набор. `cli.py:288` строит help из него же. Grep других определений не нашёл.
- **Номера schema.**
  - `create_session_record` ставит 6 только для `coordination` (`records.py:894`), остальные activity остаются на 3. `backfill.py:151` делает то же самое.
  - `_SUPPORTED_SCHEMAS` расширен до 6.
  - `_validate_session_record` отказывает записи `coordination` со schema меньше 6 (`records.py:527`).
  - Это то же правило floor из ADR-0004, по которому уже работали schema 4 и 5. То, что правило теперь применяется и к значениям vocabulary, а не только к полям, обосновано в design.md.
- **Сценарии спеки.** Каждый из четырёх покрыт тестом в `tests/test_session.py`, и docstring каждого теста называет свой сценарий. `write_record` и `read_records` проверяют и запись, и чтение. Тест на отказ проверяет, что журнал не создан.
- **Остальное.**
  - Поле с деньгами или ценой не добавлено.
  - Фикстура в `test_attestation.py` сдвинута с 6 на 7, как требует поправка к контракту.
  - Больше нигде в `src` номер schema записи не сравнивается и activity не перечисляется.
  - Старое сообщение об ошибке ни один тест не проверял, так что его изменение ничего не ломает.

**Одно замечание, не блокирующее:**

`A1-schema-stamp-duplicated`: правило «coordination → schema 6, иначе 3» записано отдельно в двух местах: `src/agentmarshal/journal/records.py:894` и `src/agentmarshal/journal/backfill.py:151`. Vocabulary теперь один, а выбор schema дублируется. Если в будущем появится ещё одна activity со своим номером schema, backfill может разойтись с `records.py`. Это тот же риск, из-за которого design.md убрал копию vocabulary.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7a34c1a7f45e001bef4ce9ef7d911002b9263905", "verdict": "approved", "findings": [], "advisory_findings": ["A1-schema-stamp-duplicated"]}
AGENTMARSHAL_VERDICT_END
