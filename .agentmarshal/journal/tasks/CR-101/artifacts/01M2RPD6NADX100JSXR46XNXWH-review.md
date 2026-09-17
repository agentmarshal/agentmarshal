Прочитал изменение целиком: `review.py`, `gate.py`, `artifacts.py`, `cli.py`, спеки, доки и тесты. Проверил ключевые инварианты статически (запуск pytest в этой песочнице заблокирован, поэтому сверял ожидания тестов с кодом вручную).

Что подтвердилось:

- Пин commit-промпта сохранён побайтово: `_REVIEW_PROMPT` через `_prose_instruction()` / `_verdict_protocol("reviewed_commit", …)` / `_named_contract_material(preamble="")` даёт ровно ту же строку, что в `test_prompt_without_named_material_is_the_prompt_written_before_schema_2`.
- Транскрипт findings-гейта не сдвинулся: `finding_reviewer_identity_refusal(..., launching=False)` возвращает ровно прежние формулировки в обеих ветках, а `check(identity_refusal is None, ...)` воспроизводит старую логику один-в-один.
- Резолвер один: `artifact_path` живёт в `artifacts.py`, `gate.py` и `review.py` держат один и тот же объект функции; третьей копии в `src/` нет (`validate.py` решает другую задачу — принадлежность артефакта журналу).
- Инъекция вердикта закрыта по-настоящему: префикс ставится по `str.splitlines()`, то есть по тому же разбиению, которым читает парсер, а `summary` и `ref` отбиваются `_reject_control_characters` на уровне записи, так что сентинел не может попасть в нулевую колонку ни через контент, ни через заголовки.
- Все 15 сценариев обеих спек названы в docstring'ах тестов; сценарий `contract-history` не потерян — его брифовую половину по-прежнему держит `tests/test_brief.py:70`.
- Циклического импорта `review → gate` нет: `gate.py` тянет только подмодули, не пакет `agentmarshal.journal`.

Блокирующих дефектов не нашёл. Два замечания ниже — advisory.

ADV-PROMPT-ABS-PATH: в `src/agentmarshal/journal/review.py:86-88` промпт утверждает «The verified artifacts are also files in your working directory, at the paths named below», но для артефакта с абсолютной ссылкой первый названный ниже путь — это `Verified artifact: /abs/path` из рабочего дерева, а не копия в снапшоте; ревьюер, запущенный без песочницы, откроет именно живой файл, что противоречит смыслу сценария «the reviewer is told where a verified artifact is» («following the prompt leads to the pinned copy and not to the working tree»). Достаточно оговорить в этой фразе, что при наличии строки `Snapshot path:` читать нужно её.

ADV-PROPOSAL-CAPABILITIES: в `openspec/changes/archive/2026-09-18-review-binds-to-a-finding/proposal.md:39-41` раздел `## Capabilities` объявляет только `new: findings-review`, хотя изменение везёт дельту `specs/reviewer-adapter/spec.md` и правит опубликованный `openspec/specs/reviewer-adapter/spec.md` — ровно ту capability, ради которой вторая поправка контракта расширила scope. Архивный proposal недоговаривает то, что изменение сделало.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "3a95a761f7825cecd7a115ef0fb0f14b0e9f43ba", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-PROMPT-ABS-PATH", "ADV-PROPOSAL-CAPABILITIES"]}
AGENTMARSHAL_VERDICT_END
