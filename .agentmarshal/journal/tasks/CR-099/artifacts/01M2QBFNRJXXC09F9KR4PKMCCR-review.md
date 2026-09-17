Проверил реализацию, тесты, шаблон, документ и openspec-материалы.

## Что подтвердил

**Режим не является обходом.** В `src/agentmarshal/journal/gate.py:944` новая ветка `elif latest is None and not review_required:` стоит после веток, обрабатывающих acceptance, и перед общим `else`. Любой кандидат, у которого `latest is not None`, попадает в прежние ветки и судится как раньше; проверка независимости рецензента на строке 969 по-прежнему сторожится `if latest is not None:`. Превратить отказ в пропуск режим не может.

**Дефолтный транскрипт не сдвинулся.** Единственная новая ветка требует `not review_required`, а `review_not_examined` по умолчанию `False`, так что `cli.py:828` печатает прежнее `gate: passed`. Ни один существующий тест в диффе не тронут. `complete.py:59` и `cli.py:866` (путь complete/merge) зовут `run_gate` без флага — собственный merge-путь проекта режим не использует, как и обещает design.md.

**Покрытие сценариев полное.** Все пять сценариев из `openspec/specs/gate-lanes/spec.md` названы в docstring'ах: `tests/test_gate.py:232, 296, 313, 329, 344` (нумерация по итоговому файлу). Делегирование закреплённого 0.3.0-теста повторяет уже существующий в репозитории приём (`tests/test_gate.py:448`), и поскольку пропуск сделан через `pytest.skip()` внутри тела (строка 416), а не декоратором, делегирующий тест корректно скипается при отсутствии релиза.

**Строки NOT EXAMINED** называют обе проверки и причину, в той же форме `NOT EXAMINED: <проверка> (<причина>)`, что и существующие строки findings-полосы (`gate.py:146, 246, 793`).

**Шаблон и документ** согласованы: `continue-on-error` убран, флаг добавлен, `docs/github-enforcement.md:37-39` честно проговаривает новое следствие — ветка без `CR-<n>` теперь валит job (проверил: `derive_gate_context` пропускает пустую строку, `load_task_status` падает, gate выходит с 1). Тестовой обвязки над `templates/` в репозитории нет, так что исключение двух пунктов раздела 2 из требования «тест на сценарий» заслуженное.

ADR-0002 и ADR-0005 читал — противоречий нет.

## Замечания (не блокирующие)

В sidecar-размещении `cli.py:826` печатает `gate: advisory checks passed; decides no merge` и никогда не доходит до ветки `review_not_examined`, так что закрывающая строка прогона с `--without-review` в sidecar не говорит, что ревью не смотрели; design.md обещает обратное («says so on its closing line») и отступление в нём не записано. Сами строки `NOT EXAMINED` в транскрипте есть, поэтому это мелочь.

Собственный workflow репозитория `.github/workflows/agentmarshal-governance.yml:3-4,31-34` остался с `continue-on-error: true` и комментарием «gate is advisory until review materialisation», ссылаясь при этом на `docs/github-enforcement.md`, который теперь описывает противоположный порядок; путь не входит в scope контракта CR-099, так что задача его тронуть не могла — это follow-up.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "6e16b9b750d3886d03005ecbf289c59299919885", "verdict": "approved", "findings": [], "advisory_findings": ["sidecar-closing-line-omits-not-examined", "own-workflow-left-advisory-and-cites-rewritten-doc"]}
AGENTMARSHAL_VERDICT_END
