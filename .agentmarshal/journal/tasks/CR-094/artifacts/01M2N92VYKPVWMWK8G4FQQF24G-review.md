Прошёл по всем десяти дайджестам, индексу и CONTRIBUTING, сверив проверяемые утверждения с кодом и журналом репозитория.

Что проверил и что сошлось:

- Все десять дайджестов (014–023) несут `Observed on: 0.3.0`, раздел измерений, «Proposed» и disposition с обоснованием; десять уникальных корректных sha256 (64 знака, нижний регистр).
- Утечек нет: в новых файлах нет путей, хостов, URL, идентификаторов задач репортёра и цитат его кода — в backticks только команды самого AgentMarshal; профиль «Adopter D» описывает setup, а не продукт/клиента/домен.
- Факты о самом проекте сверены: `doctor` действительно имеет четыре проверки (`git`, `git repository`, project file, project schema); словарь activity — implementation/review/other; `_run_reviewer` возвращает только stdout, то есть 021 всё ещё верно; ошибка плейсхолдера действительно не называет токен; шаблон `templates/github/agentmarshal-governance.yml` содержит `continue-on-error: true` и извлекает задачу из `head_ref` по `CR-[0-9]+`; `scan_for_leaks` возвращает только категорию, маркеры читаются из base-дерева.
- Цифры в 022 сошлись точно: 21 amendment-запись в 18 задачах из 91 завершённой; и CR-066 — реальный случай «правка критерия между вторым и третьим раундом после блокирующего вердикта changes_required».
- 016 подтверждается архивом `openspec/changes/archive/2026-09-06-keep-review-prose` и `prose=raw_output` в `submit_review`, версия в pyproject — 0.3.0, а 0.4.0 уже фигурирует как следующий релиз в UPGRADING.

Блокирующая проблема одна.

**outbox-journal-root-misstated** — `docs/proposals/023-upstream-outbox-has-no-transaction.md:13-15` утверждает, что outbox лежит «inside the journal root» и что его сметает wrapper, который «stage the journal directory». По собственной раскладке инструмента это неверно: `_scaffold_outbox` создаёт `.agentmarshal/upstream/` (`src/agentmarshal/project.py:289`), а journal root — это `.agentmarshal/journal/` (`src/agentmarshal/journal/review.py:341`, глоссарий в `docs/overview.md:90`). Стейджинг journal-директории outbox как раз не захватывает. Тот же файл сам себе противоречит ниже («the outbox is the one directory under the project directory that is not evidence», строка 47) и в disposition («stages the whole project directory», строка 55). Это центральное предложение механизма в публикуемом навсегда дайджесте, и принятое средство («the pathspec that does it») зависит от правильного пути.

Дополнительно, не блокирующе.

**contributing-where-column-not-named** — `CONTRIBUTING.md:61-64` описывает, что принятая proposal «names where it went», но нигде не называет это колонкой индексной таблицы, как требует пятый критерий приёмки; читатель узнаёт факт, но не куда смотреть, и отсылается к `docs/proposals/README.md`. Смысл критерия покрыт, буква — нет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "293d2c33adad7ed7ef718e630f6312e08eb143ca", "verdict": "changes_required", "findings": ["outbox-journal-root-misstated"], "advisory_findings": ["contributing-where-column-not-named"]}
AGENTMARSHAL_VERDICT_END
