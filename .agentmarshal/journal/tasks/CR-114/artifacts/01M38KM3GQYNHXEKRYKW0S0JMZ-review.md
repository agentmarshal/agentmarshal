Проверил диff целиком против контракта, спеки и кода вокруг. Ниже — что смотрел и что нашёл.

**Что подтвердил:**

- `str.isprintable()` не осталось ни в одном call site — только в комментариях и docs (`grep` по `src/`). Предикат один: `forges_rendered_text` в `records.py:512`, его зовут `contracts.py:64`, `records.py:543` и `validate.py:72`.
- Набор точно покрывает всё, на чём рвёт строку `str.splitlines()` (`\n \r \v \f \x1c \x1d \x1e \x85 \u2028 \u2029`) — это Cc, Zl, Zp — плюс bidi по codepoint и Cs. Пробельные разделители (Zs) приняты.
- Цикла импорта нет: `contracts.py` → `records.py` → `actors/attestation/project`, обратно на `contracts` никто не ходит. Порядок в `journal/__init__.py` от этого не ломается.
- Все семь сценариев дельта-спеки имеют тест, чей docstring их называет (`tests/test_record_text_safety.py`), включая запись schema 2 от более раннего релиза с U+202F и обе половины read-side проверки ref в `validate.py`.
- Старые тесты на «control characters» (`test_acceptance.py:258`, `test_journal.py:327`, `test_findings.py`, `test_validate.py:326`) используют `\n` — всё ещё Cc, так что сообщения и отказы не поехали.
- `UPGRADING.md` не называет несуществующих механизмов: `validate`, `status`, `gate`, `complete` — реальные subcommand'ы; форма строки отказа совпадает с тем, что даёт `read_records` (`…: {path}`) и `cli.py:766`.
- Archive-раскладка изменения (`proposal/design/tasks/specs/<cap>/spec.md`) и формат промотированной спеки совпадают с существующими.

**Чего не сделал:** запустить `pytest`, `ruff`, `mypy` и `agentmarshal validate` в этой сессии не получилось — выполнение таких команд требует подтверждения, которого в non-interactive режиме нет. Критерий про «весь CI-прогон проходит» проверен только статически, не исполнением.

CR-114-A001 (advisory, не блокирует): суженное правило теперь принимает невидимые форматирующие символы в тексте, который рендерится не только в транскрипт, но и в brief'ы и review-промпты — tag-блок U+E0020–U+E007F кодирует туда произвольный ASCII, невидимый человеку; `design.md` это честно фиксирует как осознанную границу и откладывает «до собственного решения», но, в отличие от второго отложенного вопроса в Non-Goals контракта, никакого decision record под это не заведено, так что риск остаётся без владельца.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1a320f7639278d721986f7ac28db7352b3c0cbdb", "verdict": "approved", "findings": [], "advisory_findings": ["CR-114-A001"]}
AGENTMARSHAL_VERDICT_END
