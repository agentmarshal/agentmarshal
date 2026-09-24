Прошёл по контракту, delta-спеке, реализации и тестам; исполняемых проверок в этой песочнице не было (нет venv/python), поэтому CI-последовательность я оценивал статически — по ruff-конфигу, mypy-аннотациям и совпадению новых тестов с уже работающими хелперами (`tests/test_validate.py:25` — тот же `_project`).

Что сошлось:

- Предикат один — `forges_rendered_text` в `src/agentmarshal/journal/records.py:512`; `contracts.py:64` и `validate.py:72` зовут его, `str.isprintable()` в коде не осталось (только в комментариях и доках).
- Набор ровно тот, что требует критерий 2: `Cc`, `Cs`, `Zl`, `Zp` плюс 12 bidi-кодпоинтов (`records.py:498,507`) — пересчитал посимвольно, U+061C, U+200E, U+200F, U+202A–U+202E, U+2066–U+2069, без лишних.
- Все 7 сценариев delta-спеки закрыты тестом, чей docstring их называет (`tests/test_record_text_safety.py`).
- Схема-2 запись с U+202F в finding id проходит `validate_journal`; поля `source`/`artifacts` входят в `_SCHEMA_2_FIELDS`, `recorded_by` для схемы 2 не требуется — запись валидна.
- Ни один существующий тест не ломается: `tests/test_validate.py:315` и `tests/test_journal.py:324` используют `\n`, который остаётся в `Cc`.
- Формат сообщения об отказе не менялся; `validate: journal invalid` (`cli.py:766`) и шаблон `"{error}: {path}"` (`records.py:1121`) совпадают с примером в UPGRADING.md. Команды `validate`, `status`, `gate`, `complete` существуют.
- Циклического импорта `contracts` → `records` нет: `records` тянет только `actors`, `attestation`, `project`.

Две несблокирующие заметки ниже.

CR-114-A001: сужение правила снимает побочную защиту на пути в prompt ревьюера — `decisions` и `documents` из contract header рендерятся дословно в `src/agentmarshal/journal/review.py:152-159`, прямо над протоколом вердикта, а новый предикат принимает весь `Cf` кроме 12 bidi-символов, включая tag-блок U+E0020–U+E007F, который кодирует произвольный ASCII и невидим читателю; design.md это называет и откладывает «на собственное решение», но ни ADR, ни proposal, ни задачи под это нет — в отличие от non-goal про schema-scoped правила, которому контракт явно обещает decision record. Блокировать нельзя: критерий 2 прямо предписывает принимать всё вне названного набора.

CR-114-A002: `tests/test_record_text_safety.py:159-181` собирает схема-2 review-запись вручную, хотя `_hand_written_review` на строке 233 строит ровно ту же запись — первый тест мог бы просто вызвать хелпер (или хелпер подняться выше по файлу), сейчас в одном модуле лежат две почти идентичные 20-строчные JSON-простыни.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "778d8455434401c722f7b8e5124bdc62be065e9d", "verdict": "approved", "findings": [], "advisory_findings": ["CR-114-A001", "CR-114-A002"]}
AGENTMARSHAL_VERDICT_END
