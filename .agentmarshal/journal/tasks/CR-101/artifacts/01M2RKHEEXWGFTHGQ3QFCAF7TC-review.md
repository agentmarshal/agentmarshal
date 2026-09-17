Разобрал диф целиком, плюс сверился с реальным состоянием кода в снапшоте: `review.py`, `gate.py`, `artifacts.py`, `cli.py`, `records.py`, `submit_review.py`, `placement.py`, оба spec-файла и тесты. Запустить pytest в этой сессии не удалось (команда требует подтверждения), поэтому проверка тестов — статическая: я вручную развернул оба шаблона промпта и сверил с закреплёнными ожиданиями.

Что проверил по существу:

- **Commit-промпт байт в байт.** `_REVIEW_PROMPT` теперь собирается из `_prose_instruction()` и `_verdict_protocol("reviewed_commit", …)`. Развернул вручную — совпадает с неизменённым ожиданием в `test_prompt_without_named_material_is_the_prompt_written_before_schema_2`, включая место, где в старом исходнике стоял перенос строки через `\`.
- **Транскрипт findings-lane.** `finding_reviewer_identity_refusal(..., launching=False)` возвращает ровно те же строки, что печатал прежний инлайн-код, и на успешной ветке `check(True, …)` получает тот же fallback-текст. `test_findings.py` и три ассерта в `test_gate.py` не тронуты и проходят по смыслу.
- **Резолвер один.** `_artifact_path` ушёл из `gate.py`, `artifact_path` в `artifacts.py` — единственное место с `resolve(strict=True)` + `relative_to` для артефактов; `gate` и `review` реэкспортируют один и тот же объект. Циклов импорта нет: `gate` не тянет `review`, пакетный `__init__` тоже чист.
- **Инъекция вердикта.** Префикс ставится через `splitlines()`, а парсер читает вывод тем же `splitlines()` — значит любой разделитель, который видит парсер (`\r`, `\x85`, `\u2028`, …), уже разбит и префиксован. Заголовки секций тоже защищены: строка контента `Verified artifact: …` придёт как `| Verified artifact: …`. Summary и refs от подделки закрыты на уровне записи — `_reject_control_characters` в `records.py`.
- **Sidecar.** `require_host=args.reviewed_finding is None` плюс `journal_root.parents[1]` в `_launch_finding_review` дают корень sidecar-проекта, а не хоста; `host_root` на этом пути не используется вообще.
- **Схема записи.** `reviewed_finding` + `reviewed_contract` → schema 5, и `_validate_record` это допускает (`_SCHEMA_4_FIELDS` требует ≥4, `_SCHEMA_5_FIELDS` открывается на ≥5). Потребители (`acceptance.py`, `report.py`) привязку выбирают по полю, а не по номеру схемы.
- **Сценарии.** Все 13 сценариев `findings-review` и оба сценария `reviewer-adapter` покрыты тестами, чьи докстринги их называют; архивная копия спеки и опубликованная различаются только заголовком и `ADDED Requirements` → `Requirements`.

Блокирующих дефектов не нашёл. Одно замечание ниже — не блокирующее.

adv-launch-review-ignores-base: в `src/agentmarshal/journal/review.py:981` публичная `launch_review` уходит в `_launch_finding_review` до какой-либо проверки `base`, поэтому вызов с `reviewed_finding` и непустым `base` молча роняет `base` на пол — при том что соседняя проверка строкой выше специально отказывает на паре `commit` + `reviewed_finding` с обоснованием «a public caller handed both would otherwise have the finding judged silently», а CLI (`src/agentmarshal/cli.py:702`) на ту же комбинацию отвечает `review --base applies only to --commit`; два входа в один и тот же код расходятся в трактовке одинаково бессмысленного вызова.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9dfad34c7a8129e24315db3dc98bba4ae9ff622f", "verdict": "approved", "findings": [], "advisory_findings": ["adv-launch-review-ignores-base"]}
AGENTMARSHAL_VERDICT_END
