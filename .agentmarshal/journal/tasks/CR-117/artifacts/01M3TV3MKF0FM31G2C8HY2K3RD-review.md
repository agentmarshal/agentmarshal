Проверил файлы в снапшоте построчно (не по памяти): `AGENTS.md`, `CONTRIBUTING.md`, последовательность проверок, упомянутые пути и команды.

Что сходится:

- `AGENTS.md` лежит в корне, 2394 байта (< 8 KB), целиком по-английски, LF, с завершающим переводом строки.
- Критерий 1: ограничение scope + «назови путь как departure» (строки 26–28), запрет на `.agentmarshal/journal/` с оговоркой про остальные файлы под `.agentmarshal/` (29–32), запрет git-операций при коммитящем харнессе (33–34), сверка утверждений с файлом (35–36).
- Критерий 2: путь контракта `.agentmarshal/journal/tasks/<task-id>/contract.md` и `agentmarshal brief --task <task-id>` — команда и флаг существуют (`src/agentmarshal/cli.py:109-112`, `:1340`). Правило про OpenSpec: архивировать только при scope, включающем `openspec/changes/archive/` и `openspec/specs/<capability>/`, только командой `openspec archive` (команда реальная — `.agents/skills/openspec-sync-specs/SKILL.md:143`), запрет ручной правки `openspec/specs/`, Purpose нового capability — в дельте.
- Критерий 3: блок команд в `AGENTS.md:44-49` совпадает строка в строку с `CONTRIBUTING.md:110-115`, без аргументов-путей; раздел «Report» даёт ровно три требуемых пункта.
- Критерий 4: внешних путей нет, все инструменты публичные (`uv`, `pytest`, `ruff`, `mypy`, `openspec`, `agentmarshal`); ссылка из раздела Development — `CONTRIBUTING.md:121-123`, внутри `## Development`. Обе markdown-ссылки ведут на существующие файлы.

Advisory (не блокирует): `AGENTS.md:31-32` говорит, что файл под `.agentmarshal/` вне журнала можно менять, когда его называет scope контракта, а брифинг, который тот же агент запускает по указанию `AGENTS.md`, печатает более строгое и уже устаревшее правило — «Do not edit anything under .agentmarshal/; the journal is not the implementer's to edit» (`src/agentmarshal/journal/brief.py:329-331`, закреплено тестом `tests/test_brief.py:87` и критерием CR-061). Поправка контракта от 2026-10-01 прямо признаёт, что задачи легитимно меняют `.agentmarshal/project.json` и `.agentmarshal/extensions/openspec.toml`, то есть устарел текст брифинга, а не `AGENTS.md`. Править `brief.py` вне scope CR-117 — это следовало назвать departure в финальном отчёте и вынести в отдельную задачу.

Критерий 5 (полная CI-последовательность) локально не проверить: в снапшоте нет `uv` и это не git-репозиторий, так что `uv run agentmarshal validate` и остальные шаги запустить нельзя. Изменение — только документация, без кода, так что риск по этому критерию минимальный; подтверждение остаётся за пайплайном.

AGENTAMARSHAL note: верно оформленный блок ниже.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "bb80247d1566e7d03f9c232e380625a1d8aaae7e", "verdict": "approved", "findings": [], "advisory_findings": ["brief-command-rule-contradicts-agents-md"]}
AGENTMARSHAL_VERDICT_END
