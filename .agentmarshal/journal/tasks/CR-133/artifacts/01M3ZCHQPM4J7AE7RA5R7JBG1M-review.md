Проверил ADR-0015 против файлов, на которые он опирается.

**Что сошлось:**
- Минимальная схема: `records.py:907` (`session_record_schema` → 6 для `coordination`, иначе 3) и `records.py:992` (review → 5 только при `reviewed_contract`, иначе 4/3) подтверждают формулировку «новое поле несёт схему, которая его ввела… остальное штампует 3»; ADR-0004 («writers stamp 4 only when those fields are used and keep 3 as the floor») и ADR-0011 D4 говорят то же.
- `tool_version` действительно только проверяется как непустая строка (`records.py:252`) и ни одного правила не выбирает.
- Строгое чтение: ADR-0004 D4 — «Validation is fail-closed», ссылка верна.
- 0.4.0 / 0.4.1: CHANGELOG (строки 16–29, 54–58) и proposal 025 подтверждают и ужесточение по `str.isprintable()` над существующим полем `findings`, и U+202F в записях schema 2 от 0.1.0, и остановленный апгрейд на 0.3.0, и то, что 0.4.1 правило сузило (послабление → на все схемы).
- Отдельные нумерации: contract header — `{1, 2}` (`contracts.py:147`), манифест — `schema = 2` в ADR-0013; записи — 1..6 (`records.py:145`), так что «(7)» как следующий номер непротиворечиво.
- `gate: passed` — реальная строка вывода (`cli.py:871`); `status`, `report`, `brief` — реальные команды (`cli.py:115`, `311`, `111`).
- Форма совпадает с ADR-0011..0013 (Status/Date, «Builds on», дисклеймер «records a decision», Context/Decision/Consequences/Alternatives), ревизия спецификации названа в точности как требует контракт, ответ на вторую рекомендацию proposal 025 есть, проверка релиза против журналов адоптеров не упомянута, ни один приватный документ, адоптер или неопубликованный релиз/решение по номеру не назван, все пять ссылок разрешаются, язык английский (CONTRIBUTING «Public artifacts are English»).
- Строка в карте документации отсутствует — это Non-Goal контракта, и ни один тест её не требует (в `tests/` нет проверки `docs/adr`).

**Advisory (не блокирует):** Decision 9 в `docs/adr/ADR-0015-...md:92-94` — единственный пункт решения, которому в критерии приёмки нет соответствия в перечислении («checks at write time…; …; the same rule for the contract header and the extension manifest; consequences and alternatives — no point dropped and none added»), и он связывает *будущее* решение конкретным номером схемы записи (7). Сверить с утверждённым русским текстом третьей ревизии может только оператор — по репозиторию номер 7 корректен (поддерживаются 1..6), но если какое-то другое новое поле приедет раньше, номер придётся переписывать в принятом ADR.

**Полную последовательность CI я не выполнял:** в снапшоте нет ни `.venv`, ни `uv`, и это не git-репозиторий, поэтому `agentmarshal validate` и git-зависимые тесты упали бы по причинам окружения, а не диффа. Диff добавляет один markdown-файл и не трогает код, тесты или данные, так что на `pytest`/`ruff`/`mypy`/`validate` он повлиять не может.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "84c69a2a493857720c89db60ab1cbc6c3a82ed29", "verdict": "approved", "findings": [], "advisory_findings": ["decision-9-binds-a-later-decision-to-schema-7-and-is-outside-the-enumerated-points"]}
AGENTMARSHAL_VERDICT_END
