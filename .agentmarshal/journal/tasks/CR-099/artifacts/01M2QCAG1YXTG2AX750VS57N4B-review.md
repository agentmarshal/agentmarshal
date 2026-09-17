Просмотрел контракт, диff и окружающий код (`gate.py`, `cli.py`, шаблон, документ, спеки, существующие тесты). Запустить pytest в этой песочнице нельзя — команда требует approval, так что проверка сделана чтением.

## Что проверил

**Ядро режима (`gate.py:944-961`)** — новая ветка стоит строго между «acceptance не покрывает findings» и общим `check(approved, …)`, срабатывает только при `latest is None and not review_required`. Ветки выше требуют `latest is not None`, поэтому кандидат с review-записью судится ровно как без флага, включая проверку independence (`if latest is not None:` ниже не тронут). Режим физически не может превратить refusal в pass — `violations` не инкрементируется и не декрементируется, добавляются только две строки. Блок целиком лежит внутри `else:` рабочей полосы (`gate.py:742`), так что journal-only lane и findings lane не затронуты; `run_findings_gate` строит `GateReport` позиционно, новое поле остаётся `False`.

**Неизменность дефолтного транскрипта** — строки добавляются только в новой ветке, а закрывающие строки CLI (`cli.py:823-836`) переключаются по `report.review_not_examined`, который при дефолтном запуске всегда `False`. `tests/test_placement.py:394` (`gate: advisory checks passed; decides no merge`) и пиннинг 0.3.0 (`tests/test_gate.py:445`) остаются валидны. `complete` (`cli.py:871`, `complete.py:59`) вызывает `run_gate` без флага — merge authority проекта режим не использует, как и обещает design.md.

**Шаблон и документ** — `continue-on-error` убран, `--without-review` добавлен, своего guard'а у job нет, документ честно говорит, что approved-independent-review на этом провайдере не обеспечивается ничем. Утверждение «без идентификатора задачи job падает» проверил по коду: `grep | head` даёт пустой `task`, `derive_gate_context` пропускает `""` как есть (`task is not None`), `load_task_status` падает → `GateError` → exit 1. Fail closed, заявление верное.

**Сценарии** — все пять сценариев `spec.md` имеют тест, чей docstring их называет; `openspec/specs/gate-lanes/spec.md` и `.openspec.yaml` архива соответствуют конвенциям соседних capability-спек. Противоречий с ADR-0002 и ADR-0005 не нашёл: флаг не трогает ни capture policy, ни то, что означает записанный review, ни attestation.

## Findings

A-001: новая ветка закрывающей строки для sidecar (`src/agentmarshal/cli.py:826-830`, «advisory checks passed what they examined…») — единственный путь в диффе, который не покрыт ни одним тестом; sidecar-тесты пиннят только дефолтную формулировку.

A-002: ни `test_an_approving_review_reports_as_approving_under_the_mode`, ни `test_a_non_approving_review_still_refuses_under_the_mode` (`tests/test_gate.py:341-369`) не утверждают наличие строки `PASS: declared reviewer identity differs…` — они ловят регрессию «independence стал NOT EXAMINED», но не регрессию «independence тихо выпал совсем», хотя критерий 2 говорит о проверках во множественном числе.

A-003: `--without-review` описан только в `docs/github-enforcement.md` и в `--help`; provider-нейтральная справка по gate в `docs/quickstart.md:102-114` («Gate attestation modes») о нём молчит — файл вне scope контракта, так что это задача на следующий заход, а не упущение этой.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a9e1e1746c4ce986d6fd2c78836ad1cf7a3e6563", "verdict": "approved", "findings": [], "advisory_findings": ["A-001", "A-002", "A-003"]}
AGENTMARSHAL_VERDICT_END
