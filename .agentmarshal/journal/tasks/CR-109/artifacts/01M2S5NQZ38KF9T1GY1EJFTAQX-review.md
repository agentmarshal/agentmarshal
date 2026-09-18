Ревью CR-109 (коммит 7140defa) — **changes_required**: одно блокирующее замечание и четыре некритичных. Тесты запустить не дали, всё сверено статически по снапшоту.

**Что выполнено:**
- **Версия.** Везде `0.4.0`: `pyproject.toml`, `__init__.py`, `uv.lock` и smoke-тест. `--version` печатает `__version__`, это закреплено в `tests/test_smoke.py:59`.
- **CHANGELOG.** Все 25 задач с CR-084 по CR-108 названы. Слов «planned/next/in line/soon» в разделе 0.4.0 нет. Выборочные утверждения сходятся с кодом:
  - в gate лимит `_LEAK_HIT_RENDER_LIMIT = 20`;
  - режим `--without-review` есть;
  - finding без проверяемых артефактов отклоняется;
  - маркер не ищется в файле, где он объявлен;
  - версия OpenSpec 1.12.0.
- **Схемы записей в UPGRADING.** Описание схем 4, 5 и 6 совпадает с `records.py`. `agentmarshal review` всегда передаёт `reviewed_contract` (`review.py:883`), поэтому каждое такое ревью пишется со схемой 5.
- **Три замечания CR-107:**
  - из заголовка roadmap в `docs/overview.md` убрано слово «designed», и у каждого пункта теперь сказано, есть ли опубликованный дизайн;
  - в workflow у job `governance` вернули комментарий шаблона дословно;
  - в proposal 005 добавлена датированная секция: обещанный порядок работ не выполнился.
- **Тест транскрипта 0.3.0.** Его ожидания не менялись. Упоминания 0.3.0 как истории оставлены как есть.

Блокирующее: `UPGRADING.md` (раздел 0.3.0 → 0.4.0) не упоминает изменение gate из CR-093. Теперь gate видит у переименования обе стороны, удаление и добавление. Поэтому кандидат, который переносит файл из пути вне scope, раньше проходил, а в 0.4.0 будет отклонён. Кроме того, перенос в `.agentmarshal/journal/` теперь считается diff-lane кандидатом, а не journal-only. Это такое же ужесточение для существующих установок, как отказ writer'ов из CR-102, который в гайде описан, а контракт требует назвать все такие изменения.

Некритичное: в `UPGRADING.md` старый подраздел «Contract headers gain schema 2» по-прежнему заканчивается фразой «the record schema do not change». А прямо над ним в том же разделе новый текст вводит record schemas 4, 5 и 6, и читатель получает противоречие.

Некритичное: `docs/quickstart.md:6-8` теперь утверждает, что каждая команда прогнана на wheel 0.4.0, но в диффе нет подтверждения такого прогона. Там же новая строка не перенесена по ширине остального текста.

Некритичное: запись CR-099 в CHANGELOG говорит, что GitHub workflow перешёл на режим без ревью. Но не сказано, что после этого GitHub-джоба требование одобренного независимого ревью не проверяет. `docs/github-enforcement.md` это частичное покрытие прямо называет, а changelog должен говорить, где возможность частичная.

Некритичное: в `docs/proposals/005-research-findings-have-no-record-type.md:42` фраза «is next in line» в секции принятия осталась в настоящем времени и без пометки «Superseded». Секцию об отсрочке так пометили. Новая секция «Later» поправку вносит, но только в конце документа.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7140defa4e2ae65bd6414efafa5735928b82c8a5", "verdict": "changes_required", "findings": ["UPGRADING-MISSING-CR093-RENAME-SCOPE"], "advisory_findings": ["ADV-UPGRADING-RECORD-SCHEMA-UNCHANGED-CONTRADICTS", "ADV-QUICKSTART-VERIFICATION-UNEVIDENCED", "ADV-CHANGELOG-GITHUB-REVIEW-UNENFORCED-UNSTATED", "ADV-PROPOSAL-005-ACCEPTED-SECTION-UNMARKED"]}
AGENTMARSHAL_VERDICT_END
