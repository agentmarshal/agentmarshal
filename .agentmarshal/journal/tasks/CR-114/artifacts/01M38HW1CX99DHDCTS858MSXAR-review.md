Разобрался с диффом, исходниками и тестами. Вот что нашёл.

**CR-114-F001** — блокирующая. Сценарий delta-спеки «the rule guards every place that renders record text» (`openspec/specs/record-text-safety/spec.md:44`) не демонстрируется ни одним тестом: в `tests/test_record_text_safety.py` его нет, а существующий `tests/test_validate.py:296` `test_validate_refuses_an_artifact_ref_with_control_characters` использует `\n` — символ, который отвергали и старое `isprintable()`, и новый набор. То есть ровно тот call site, ради которого 2026-09-24 в scope добавили `validate.py:72`, ничем не закреплён: если вернуть там `not character.isprintable()`, весь suite останется зелёным, и drift, который задача существует чтобы убрать, вернётся незамеченным. Acceptance criterion №1 требует тест, в docstring которого назван сценарий.

**CR-114-F002** — совет. `tests/test_record_text_safety.py:121` покрывает сценарий «an unpaired surrogate is refused», но его docstring — «A value that could not be written back as UTF-8 is refused.» — сценарий не называет, в отличие от остальных пяти тестов файла и общей конвенции репозитория (`"""Scenario: ..."""`). По букве acceptance criterion №1 этот сценарий тоже не засчитан.

**CR-114-F003** — совет. Acceptance criterion №2 говорит «refuses exactly ... categories Cc, Zl and Zp, and the bidirectional controls U+202A-U+202E and U+2066-U+2069 — and accepts every other character». Реализация в `src/agentmarshal/journal/records.py:499-509` отвергает сверх этого `Cs` и U+061C, U+200E, U+200F. Для bidi-марок это ещё читается как «reorder text», но `Cs` под формулировку критерия не подпадает вовсе. Решение записано в `design.md` и в спеку, регрессии нет (все четыре класса отвергались и до изменения), но текст контракта и отгруженное правило расходятся, а механизм amendment в этой задаче использовался дважды и здесь не применён.

**CR-114-F004** — совет. `design.md` в разделе Context перечисляет call sites обоих предикатов и пропускает два: `src/agentmarshal/journal/artifacts.py:66` (`artifact name`) и `src/agentmarshal/journal/extensions.py:75` (`extension name`). Оба тоже ослабли, и оба имени становятся компонентом пути на диске — `.agentmarshal/extensions/<name>.toml` и `.../artifacts/<name>`. Теперь имя расширения может нести U+00A0, U+200B или private-use codepoint, то есть два разных манифеста будут выглядеть в transcript одинаково. Ни анализа, ни теста на это нет.

**CR-114-F005** — совет. Комментарий `src/agentmarshal/journal/records.py:497` и повторяющая его формулировка в `design.md` и `openspec/specs/record-text-safety/spec.md` подают скобку «The Cf characters left out (U+00AD, U+200B-U+200D, U+FEFF)» как исчерпывающую. На деле вне набора остаётся ещё около ста пятидесяти Cf-кодпоинтов, включая блок тегов U+E0020–U+E007F, который кодирует невидимый ASCII-текст. Про сам набор это не ошибка — теги действительно не ломают строку и не меняют порядок, — но UPGRADING.md обещает адоптеру, что оставшиеся отказы касаются символов, способных «break a line, hide text or fail to encode», и «deliberate boundary» выглядит уже́, чем есть.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "0a00651b93e34655a302b86b8f7f8af912381230",
  "verdict": "changes_required",
  "findings": ["CR-114-F001"],
  "advisory_findings": ["CR-114-F002", "CR-114-F003", "CR-114-F004", "CR-114-F005"]
}
AGENTMARSHAL_VERDICT_END
