Проверил контракт, delta spec, реализацию и тесты.

**Что подтвердил:**

- `str.isprintable()` исчез из всех трёх мест: `records.py:543`, `contracts.py:64`, `validate.py:72` — все зовут один предикат `forges_rendered_text` (`records.py:512`). Grep по `src/` подтверждает: других копий проверки нет.
- Отказной набор совпадает с criterion 2 буквально: `_FORGEABLE_CATEGORIES = {"Cc","Cs","Zl","Zp"}` плюс двенадцать bidirectional codepoints. Набор устойчив к версии Unicode — Cc, Cs, Zl, Zp закрыты и новых членов не получат, так что `Cn`-аргумент из design.md не подрывает само правило.
- `str.splitlines()` в `contracts.py:125` режет по `\n \r \v \f \x1c-\x1e \x85 U+2028 U+2029` — все они Cc/Zl/Zp, то есть суженное правило не оставило дыру на contract-стороне.
- Все семь сценариев delta spec имеют тест, чей docstring их называет. Ретроактивный кейс (`test_a_journal_an_earlier_release_accepted_stays_valid`) написан вручную как schema 2 с `tool_version 0.1.0`; поля `source`/`artifacts` разрешены на schema 2 (`_SCHEMA_2_FIELDS`), так что запись действительно валидируется, а не падает по другой причине.
- Старые тесты (`test_acceptance.py:258`, `test_findings.py:491,543`, `test_journal.py:319`, `test_validate.py:295`) используют `\n` — все остаются красными на запись, сообщения не менялись. Ни один существующий тест не пинил символ, который теперь принимается.
- `UPGRADING.md` воспроизводит реальный формат вывода: `read_records` даёт `"{error}: {path}"`, `validate_journal` префиксует `FAIL: {task}: `, а `cli.py:766` печатает `validate: journal invalid`. Никакого allowlist не вводится, и текст явно говорит, что его и не планируется.
- Циклического импорта нет: `records.py` тянет только `actors`, `attestation`, `project`, и ни один из них не импортирует `contracts`.

Запустить `pytest`/`ruff`/`mypy` в этой песочнице не дали (команды требуют подтверждения), так что criterion 6 в части «full CI sequence passes» проверен статически, а не прогоном.

CR-114-A1: `design.md` в разделе Context утверждает, что `extensions.py` достаёт record-предикат «through its own name» наравне с `artifacts.py`, но на деле `extensions.py:10-15` импортирует `reject_control_characters` из `contracts.py`, а не `_reject_control_characters` из `records.py` — поведение теперь одинаковое, но описание вызова в решении неверно.

CR-114-A2: `contracts.py:10` разворачивает слои — более примитивный модуль разбора контракта теперь импортирует тяжёлый `records.py` (ULID, запись файлов, `actors` → `subprocess`); решение это зафиксировало, но оставило скрытую хрупкость: первая же будущая надобность `records.py` в `validate_scope_entry` или `scope_covers` превращает это в жёсткий circular import.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "778d8455434401c722f7b8e5124bdc62be065e9d", "verdict": "approved", "findings": [], "advisory_findings": ["CR-114-A1", "CR-114-A2"]}
AGENTMARSHAL_VERDICT_END
