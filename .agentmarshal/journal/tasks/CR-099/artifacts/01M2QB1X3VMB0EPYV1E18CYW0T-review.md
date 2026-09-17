Проверил diff против контракта CR-099, спеки `openspec/specs/gate-lanes/`, архивного change-пакета, ADR-0002 и ADR-0005. Запустить `pytest` в этой песочнице не дали (команда требует approval), поэтому критерий про byte-for-byte транскрипт проверен чтением кода, а не прогоном: новая ветка срабатывает только при `review_required=False`, а `partial` по умолчанию `False`, так что дефолтный путь не сдвигается.

Суть механизма держится. `--without-review` меняет ровно одну ветку — `elif latest is None and not review_required` (`src/agentmarshal/journal/gate.py:943`), обе review-bound проверки печатаются как `NOT EXAMINED` с причиной, `if latest is not None:` ниже продолжает судить independence, `complete.py:59` зовёт `run_gate` без флага, так что merge-authority проекта не задета. Обход не открылся: `scope`, `append-only`, `base-state`, `lifecycle`, attestation не тронуты, а `--findings` с флагом отбивается до всего остального (`cli.py:740`). Пять сценариев спеки покрыты тестами, чьи docstring их называют; шаблон потерял `continue-on-error` и собственного guard не завёл; чекбоксы в `tasks.md` проставлены.

Ниже — несовпадения, которые не блокируют, но которые стоит подчистить.

ADV-001 — `openspec/changes/archive/2026-09-17-gate-without-a-review/design.md`, секция `## Risks`: пункт про «оператор читает "not examined" как "passed"» утверждает «The gate has no summary line to count them in, and this note earlier claimed it did», но это изменение как раз добавляет summary-строку — `GateReport.partial` (`gate.py:66`) и `cli.py:828-829` печатают `gate: passed what it examined; the review was not examined`, и новый тест её пинит (`tests/test_gate.py:278`). Named contract document описывает отсутствие ровно того механизма, который в нём же и приехал, а departure нигде не записан, чего требует первый критерий приёмки.

ADV-002 — `src/agentmarshal/journal/gate.py:64-67`: комментарий к полю `partial` говорит «True when a check was reported as not examined rather than evaluated», но флаг отслеживает только review-пару. Findings-lane печатает шесть `NOT EXAMINED` строк и возвращает `partial=False` (`gate.py:245-266`), строка про removal of extension (`gate.py:791-794`) его тоже не поднимает. Вызывающий, который поверит комментарию и станет отличать полный pass от частичного по одному булеву, получит `False` там, где транскрипт полон неосмотренных проверок.

ADV-003 — `openspec/specs/gate-lanes/spec.md:11-16` (и идентичная строка в архивном спеке): нормативное предложение требует режим при «no review record **at all**», тогда как код и собственный сценарий этого же требования срабатывают на «нет записи **для коммита кандидата**» (`gate.py:894-900, 943`). Разница материальна: задача с `changes_required` на предыдущем коммите ветки получит `NOT EXAMINED` и зелёный gate на новом head. Код здесь защитим — ADR-0002 прямо называет единицей ревью «the task's diff at an exact commit», — но durable-артефакт лучше привести к формулировке сценария, иначе следующая реализация прочитает буквальное «at all».

ADV-004 — `docs/github-enforcement.md:78-81`: буллет внутри секции `## Open item: review materialisation (Phase C)` заканчивается «see the open item below», хотя это и есть тот самый open item, а ниже только сравнительная таблица Variant 1 / Variant 2. Ссылка висит в пустоту (такая же формулировка на строке 47 выше — там она корректна).

ADV-005 — `.github/workflows/agentmarshal-governance.yml:3, 33-39, 55`: собственный workflow проекта по-прежнему гоняет gate без `--without-review` под `continue-on-error: true` и с комментарием «Advisory until review materialisation», то есть репозиторий теперь противоречит шаблону, который сам же и отгружает, и документу, который только что переписал. Файл вне scope контракта, так что это пометка, а не ожидание от этого изменения.

ADV-006 — `tests/test_gate.py:232-243`: `test_a_default_run_prints_the_transcript_it_printed_before` — чистый алиас, вызывающий другую тестовую функцию. Целевой тест делает `pytest.skip(SKIP_030)`, когда релизного 0.3.0 нет; `released_030()` отбрасывает `agentmarshal` с PATH, если тот знает команду `finding`, то есть под `uv run` в CI проекта отбрасывается текущая сборка. Значит сценарий «the pinned transcript still matches» в собственном CI «демонстрируется» скипом. Наследуется от пиннингового теста, менять который контракт запрещает, — но независимого покрытия у сценария нет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "31462c3a541081459299b3d74cb15725ca924b66",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-001", "ADV-002", "ADV-003", "ADV-004", "ADV-005", "ADV-006"]
}
AGENTMARSHAL_VERDICT_END
