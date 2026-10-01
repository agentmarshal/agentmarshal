Проверил диф против кода, журнала, CHANGELOG, UPGRADING и контрактов CR-114 / CR-115.

Что сошлось:

- Хеш источника в заголовке 025 совпадает с контрактом символ в символ; псевдоним и профиль — `Adopter A (Python web service on Linux)` — ровно те, что уже используют 001–007 и 010.
- Механизм описан так, как он в коде: `_reject_control_characters` в `src/agentmarshal/journal/records.py:526`, проверка существовала до 0.4.0 для полей и finding id acceptance-записи (`records.py:414,426`), 0.4.0 распространил её на `findings` и `advisory_findings` ревью (`records.py:364,383`) — это же подтверждает контекст CR-114 — и валидация записи идёт на чтении (`read_records`, `records.py:1079`, падает на первой невалидной). Набор 0.4.1 (`_FORGEABLE_CATEGORIES` = Cc/Cs/Zl/Zp плюс `_BIDIRECTIONAL_CONTROLS` с U+061C, U+200E, U+200F) и один предикат `forges_rendered_text` на records/contracts/validate — всё как в тексте.
- Сообщение об отказе и `validate: journal invalid` (`cli.py:766`) воспроизводятся дословно; маршрут «с 0.3.0 сразу на 0.4.1» действительно есть в UPGRADING.md.
- Четыре диспозиции на месте, числа во внутренне согласованы (6+3+2 = 11 вхождений; 282 − 2 = 280 задач OK), таблица батча датирована 2026-09-24 и стоит выше батча 2026-09-18, строка в карте docs/README.md добавлена.

Одно замечание, не блокирующее.

В `docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md:18-19` абзац, заявленный как «механизм, как он в коде», утверждает, что общежурнальный `validate` «prints one failure line per task and moves to the next». Для этого класса отказа так и есть, но в общем виде `validate_journal` (`src/agentmarshal/journal/validate.py:182-209`) печатает по строке на каждое столкновение record id и на каждый дефект артефакта, то есть несколько строк на одну задачу; собственный docstring модуля прямо говорит «reports every violation rather than stopping at the first». Формулировку стоит привязать к этому конкретному случаю («здесь — по одной строке на задачу»), а не описывать ею поведение команды вообще.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "588445e947c77fbaaf29bab90a219595e386ecee", "verdict": "approved", "findings": [], "advisory_findings": ["validate-one-line-per-task-overstated"]}
AGENTMARSHAL_VERDICT_END
