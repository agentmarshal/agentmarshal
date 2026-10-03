Прочитал контракт, дельта-спек, архив изменения, `settings.py`, `doctor.py` и оба тестовых файла; сверил дефолты с ADR-0016 (решения 3 и 4) и ADR-0022 §6.

Что проверил по критериям приёмки:

- **Изменение и архив.** `openspec/changes/` содержит только `archive/`, изменение лежит как `archive/2026-10-03-project-settings-0-5-0/` с `.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md` и дельтой `specs/project-settings/spec.md`; опубликованный `openspec/specs/project-settings/spec.md` имеет тот же заголовочный формат, что и остальные спеки (`# <cap> Specification` / `## Purpose` / `## Requirements`), и Purpose заполнен из дельты, а не оставлен заглушкой.
- **Покрытие сценариев.** Все 12 `#### Scenario:` из спека имеют тест с docstring, дословно повторяющим заголовок — 8 в `tests/test_settings.py`, 4 в `tests/test_doctor.py`. Расхождений в формулировках нет.
- **Дефолты.** Семь классов в `DEFAULT_FINDING_CLASSES` (`src/agentmarshal/settings.py:35`) совпадают с ADR-0016 решение 3 посимвольно; порог 3 и флаг `false` — с ADR-0022 §6.
- **Absent vs malformed.** Различение идёт по `in` (`settings.py:67`, `:81`, `:112`, `:124`), поэтому JSON `null` — present; секция-не-объект поднимает ошибку, называющую ключ. `bool` отсекается до `int` (`settings.py:117`). Контрольные символы проверяются общим `reject_control_characters` → `forges_rendered_text`, где `Cc` покрывает и `\n`, и `\t`, так что параметризация в тестах соответствует предикату.
- **Только doctor читает настройки.** `grep` по `src/`, `tests/`, `docs/`, `templates/` даёт единственного потребителя — `doctor.py:22`. Циклического импорта нет: `journal/contracts.py` тянет только `journal/records.py`.
- **Счётчики в doctor-тестах.** Я вручную прогнал обе арифметики: для `test_doctor_reports_every_precondition_met` получается 10 OK, для `test_doctor_handles_git_discovery_decode_error` — 6 FAIL / 2 TODO. `tests/test_cli.py:50` (`2 precondition(s)`) не затронут, так как три новые проверки на `{"schema": 1}` проходят. Других тестов, зависящих от числа проверок, в наборе нет.

Полную последовательность CI выполнить не смог: в этой песочнице запуск `uv`/`pytest` не разрешён. Проверка статическая — трассировка каждого нового теста по коду, длины строк под 88, совместимость с `ruff` (`E,W,F,I,UP,B,SIM,RUF`) и `mypy --strict` (сужения `isinstance` + `cast` не избыточны). Блокирующих дефектов не нашёл.

Две неблокирующие заметки, каждая — одной строкой прозы перед блоком:

**advisory-doctor-repeats-parse-failure** — в `src/agentmarshal/doctor.py:146` каждая из трёх новых проверок на нечитаемом `project.json` выдаёт то же сообщение `cannot parse …; repair the project file (…)`, что и `project schema` на строке 124, поэтому самый частый случай ручной правки файла печатает один и тот же текст четырьмя строками FAIL вместо одной; поведение заявлено в design.md, но выхлоп от этого шумнее.

**advisory-key-constant-duplication** — в `src/agentmarshal/settings.py:32`–`34` точечные константы (`"review.finding_classes"` и прочие) живут отдельно от фактического доступа к JSON (`_section(project, "review", …)` плюс `section["finding_classes"]` на строках 67–70, 112–115, 124–127), так что переименование ключа в константе изменит только текст ошибок и имя doctor-проверки, не затронув то, что реально читается; вывод сегментов из константы (`key.split(".")`) убрал бы эту пару, которую нужно держать в синхроне руками.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "59b8847b2e881b35afac91dafc5966707bd4c62b",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-doctor-repeats-parse-failure",
    "advisory-key-constant-duplication"
  ]
}
AGENTMARSHAL_VERDICT_END
