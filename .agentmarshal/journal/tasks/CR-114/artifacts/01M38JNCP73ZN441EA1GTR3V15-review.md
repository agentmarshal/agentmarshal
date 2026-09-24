Разобрал диff, реализацию и окружающий код. Выполнить CI не смог: в этой песочнице запуск `python3`/`uv` не разрешён, так что по критерию 6 («полная последовательность CI проходит») я проверял статически — тесты, которые могли бы сломаться от смягчения правила, я нашёл и перечитал (`tests/test_acceptance.py:258`, `tests/test_findings.py:491,543`, `tests/test_validate.py:326`, `tests/test_journal.py:327`); все они пинят `\n`, который по-прежнему отвергается, и ни один тест не утверждает отказ для символа, который стал приниматься.

Что проверено по существу:

- Предикат один (`records.py:512`), им пользуются все три места: `records.py:543`, `contracts.py:64`, `validate.py:72`; `str.isprintable()` в коде не осталось нигде (только в пояснительных комментариях и доках). Цикла импортов нет — `records.py` не тянет `contracts.py`, а `attestation.py`/`actors.py` не тянут ни того, ни другого.
- Набор совпадает с критерием 2 буквально: `Cc` (в нём же `\t`, `\v`, `\f`, `\x1c-\x1e`, U+0085), `Cs`, `Zl`, `Zp` плюс перечисленные bidi-кодпоинты. Всё, на что делит `str.splitlines()` — а именно так читает вывод парсер вердикта (`review.py:288`) — покрыто. `Zs`, `Co`, остальной `Cf` приняты.
- Сравнение findings в гейте — точное `set(...) == set(...)` (`gate.py:162`, `gate.py:914`), без `.strip()`, так что id с U+202F не склеивается с соседним и подделать строку по-прежнему нельзя.
- Пример вывода в UPGRADING.md соответствует реальному формату: `FAIL: {task}: {error}: {path}` (`records.py:1121`, `validate.py:205`) и `validate: journal invalid` (`cli.py:766`). Механизмов, которых нет, заметка не называет, allowlist прямо отрицается.
- Все семь сценариев delta-спеки названы в docstring'ах тестов; `record-text-safety` оформлена по конвенции остальных спек; ADR-0004 (валидация fail-closed, «loaders continue to accept schemas 1 and 2 unchanged») и ADR-0007 не противоречат изменению.

Два замечания без блокировки:

CR-114-A001: в `openspec/specs/record-text-safety/spec.md:14` перечисление «Where this rule is applied» подано как исчерпывающее, но пропускает два живых вызова того же предиката — имя артефакта (`src/agentmarshal/journal/artifacts.py:66`) и имя расширения (`src/agentmarshal/journal/extensions.py:75`), поведение которых это изменение тоже смягчило; design.md о них говорит, нормативная спека — нет.

CR-114-A002: docstring `test_the_rule_holds_the_same_on_both_sides` (`tests/test_record_text_safety.py:213`) утверждает, что `\n`, `\r`, U+2028 и U+2029 «never reach this check on the contract side» — это неверно для экранированной формы: TOML `"first\\nforged"` раскрывается в настоящий перевод строки и до проверки доходит, что и пинит `tests/test_journal.py:319-327`; покрытие на месте, ошибочно именно объяснение, на которое будет опираться следующий читатель.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d8429eed58514665bece9b322cdf4ce07dc53530", "verdict": "approved", "findings": [], "advisory_findings": ["CR-114-A001", "CR-114-A002"]}
AGENTMARSHAL_VERDICT_END
