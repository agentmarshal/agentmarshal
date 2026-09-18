Одна проблема блокирует релиз. Остальные acceptance criteria выполнены, это я сверил с исходниками.

**Блокирует:**

`docs/quickstart.md:6` и `docs/quickstart.md:22` по-прежнему говорят про 0.3.0. Там утверждается, что «every command below was run against the published `agentmarshal` 0.3.0 release», и предлагается ставить `pip install agentmarshal==0.3.0`. Но диф уже поменял строки 196, 197 и 350 той же страницы на «in 0.4.0», а сама страница описывает то, чего в 0.3.0 нет: `review --dry-run` (строка 59), finding reviews с `reviewed_finding` (строки 50 и 86) и schema-2 contract extensions (строка 200). Кто поставит закреплённую 0.3.0 и пойдёт по гайду, упрётся в команды, которых там нет. Страница противоречит сама себе, и это нарушает критерий «every statement about 'the current release' names 0.4.0». Утверждение о проверке нужно переписать честно, а не просто заменить номер версии: 0.4.0 ещё не опубликован, а публикация по контракту — non-goal.

**Что подтвердилось:**
- **Workflow.** Джоб `governance` в `.github/workflows/agentmarshal-governance.yml` теперь дословно повторяет комментарий из шаблона. В шаблоне реально стоит `--without-review`.
- **`docs/overview.md`.** Раздел roadmap больше не называет направление «designed». Бывший пункт «Contract extensions» явно отделён от поля `extensions` из ADR-0010.
- **Proposal 005.** Больше не ссылается на неопубликованное: теперь указывает на ADR-0009 и CR-086. Старое упоминание in-toto осталось только в разделе, помеченном как история.
- **UPGRADING, schema 5.** Сходится с кодом: `review.py:883` всегда передаёт `reviewed_contract`, и `records.py` тогда проставляет schema 5. У `submit-review` в CLI такого поля нет.
- **UPGRADING, schema 6 и лимит leak-scan.** Schema 6 используется только для `coordination`. Лимит в 20 хитов действует только в gate (`_LEAK_HIT_RENDER_LIMIT`).
- **CHANGELOG.** Упомянуты все 25 задач, CR-084…CR-108.
- **Версия.** Номер обновлён в `pyproject.toml`, `__init__.py`, `uv.lock` и в smoke test.

Сам я `pytest` и `agentmarshal --version` не запускал: `uv run` требовал разрешения, а это ревью только на чтение. Поэтому то, что тесты с закреплённым транскриптом 0.3.0 проходят, я не проверил. Их ожидания в дифе не тронуты.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "244081cfa1c8dad80fb09fbc5c5fe761ff2d44c7", "verdict": "changes_required", "findings": ["QUICKSTART-PINS-030"]}
AGENTMARSHAL_VERDICT_END
