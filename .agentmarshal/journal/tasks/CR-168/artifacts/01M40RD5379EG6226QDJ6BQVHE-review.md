Я прочитал diff, реализацию, спеку, фикстуры и тесты в снапшоте, а также соседние места, которые печатают или парсят транскрипт гейта.

**Что проверено по критериям контракта**

- `run_gate` считает по `task.records` (это тот же набор, что `read_records`, который лане уже читает) записи `record_type == "review"` с `verdict == "changes_required"` — над всей задачей, независимо от `reviewed_commit`; строка печатается последней перед вердиктом и только `say`, так что `violations` не меняется (`src/agentmarshal/journal/gate.py:1248`).
- Порог читается через `changes_required_threshold(journal_root.parents[1])`. В обоих размещениях `journal_root` — это `<root>/.agentmarshal/journal` (`src/agentmarshal/journal/placement.py:77`), так что `parents[1]` — корень проекта в embedded и корень сайдкара в сайдкаре, ровно как у существующего `markers_from_config`. Перехват `(OSError, ValueError)` закрывает все пути `read_project_file`: отсутствующий файл (`OSError`), нечитаемый JSON (`JSONDecodeError` ⊂ `ValueError`), не-объект и `ProjectSettingsError` — то есть «нечитаемый порог» действительно не валит прогон.
- Формулировки трёх вариантов строки совпадают с design.md дословно; `>=` соответствует «reached» в ADR-0016 решение 4; `INFO`/`WARN` не ломают ни одного потребителя — транскрипт нигде в `src/` и в `templates/github/` не парсится по префиксам, а тесты leak-scan берут `next(... startswith("WARN:"))`, и строка счётчика идёт после них.
- Фикстуры: три реализационных кейса получили ровно одну строку, `embedded-journal-only` не изменён; в сайдкаре журнальный кейс идёт по реализационной лане (ADR-0008 решение 2) и строку получил. Все пять сценариев закрыты тестами с docstring'ами, называющими сценарий, включая «вердикт и код выхода те же» (`assert passed` + `main(...) == 0`).
- `docs/quickstart.md` — единственный транскрипт в доках, который пинит тест (`tests/test_quickstart.py:112` сравнивает блок посимвольно), и он обновлён. Транскрипт в `UPGRADING.md:231` — это журнальная лана опубликованной 0.2.0, строки там быть не должно.

Блокирующих дефектов не нашёл. Две советующие заметки ниже.

ADV-001: `docs/sidecar.md:226-230` показывает advisory-транскрипт сайдкара (реализационная лана), и после этой правки реальный прогон печатает там ещё строку `INFO: changes_required verdicts for CR-001: 0 (threshold 3)` — ровно ту, что получила фикстура `sidecar-implementation.stdout`; страница при этом перечисляет строки транскрипта придирчиво («which is why the transcript above has no such line»), так что дрейф заметен читателю. Файл вне `scope` контракта (там только `docs/quickstart.md`), поэтому это задел на поправку контракта или отдельную задачу, а не упущение внутри данного диффа.

ADV-002: `src/agentmarshal/journal/gate.py:1253` считает все review-записи задачи, включая привязанные к находке (`reviewed_finding`, ADR-0009 — `_validate_review_record` допускает обе привязки), тогда как требование в `openspec/specs/gate-lanes/spec.md` описывает набор как «every review record of the task, whatever commit it names»; для задачи, у которой есть и review находки с `changes_required`, и реализационная лана, код считает больше, чем буквально обещает текст. Поведение защитимо (это «сколько раз задачу вернули»), но текст и код стоит свести — например «whatever it names».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cdb26d82c692ddb1299704e16a8998d98e384317", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-001", "ADV-002"]}
AGENTMARSHAL_VERDICT_END
