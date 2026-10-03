Проверил diff целиком против контракта: функцию хеширования, регистрацию поля, правила схемы, delta-спеку и архив, тесты, а также все места в `src/`, которые считают sha256.

Что подтвердил по файлам:

- `contract_sha256` (`src/agentmarshal/journal/contracts.py:255`) декодирует байты как UTF-8, нормализует `\r\n` → `\n`, затем `\r` → `\n` (порядок верный: `"\r\r\n"` даёт `"\n\n"`, как универсальные переводы строк в Python), BOM оставляет в тексте, отказ называет `source`.
- Лончер (`review.py:990`) — единственное место, где хешируется контракт; оба пути чтения контракта (`review.py:1075`, `review.py:1246`) используют `read_text(encoding="utf-8")`, т.е. текст уже нормализован, и повторная нормализация — тождество. `reviewed_contract` не меняется; это пришпилено и end-to-end тестами (`tests/test_review_launcher.py:627`, `:681`). Остальные `hashlib.sha256` в репозитории — артефакты, outbox и stat-файлы backfill, не контракты.
- Поле `contract`: `_SCHEMA_7_CONTRACT_FIELDS`, две записи `_FIELD_FAMILIES` (`records.py:277-278`), `_FORGEABLE_TEXT_FIELDS` (`records.py:326-327`), правило `contract-hash-7` с привязкой к 7 (`records.py:576`, `:746`), ветка в `_minimum_schema` (`records.py:1269`), опциональный keyword в обоих writer'ах. Ни один вызов в `src/` не передаёт `contract` (`migrate.py:380`, `cli.py:900`, `open_task.py:172`) — non-goal соблюдён, фикстуры гейта не тронуты.
- Все 12 сценариев delta-спеки имеют тест с docstring, который их называет; текст архивной delta побайтово совпадает с тем, что легло в `openspec/specs/contract-governance/spec.md`; MODIFIED не требуется — обобщённые формулировки record-schema (строки 62-66, 108, 121-124) ввёл CR-160, и `contract` под них подпадает.

Одно непринципиальное замечание (не блокирующее): правило `contract-hash-7` в `src/agentmarshal/journal/records.py:576` не отсекает тип записи — в отличие от `session-fields-7` (`records.py:549`), которое сразу возвращается для не-`session`. Сейчас это безопасно (единственный тип с полем `contract` — `opened`/`amendment`, а правило `fields` стоит раньше в порядке регистрации и отвергает чужое размещение), но проверка формы 64-hex распространится автоматически на любой будущий тип с полем `contract` — например на `agreement` из ADR-0022, который дизайн сам упоминает как отдельную задачу, — без осознанной регистрации.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e692e9a6a333acfe4397d8d076888a3da6026640", "verdict": "approved", "findings": [], "advisory_findings": ["contract-hash-7-not-keyed-by-record-type"]}
AGENTMARSHAL_VERDICT_END
