Проверил файлы в снапшоте, а не по диффу: `AGENTS.md` (2394 байта, английский, корень репозитория), `CONTRIBUTING.md`, путь контракта `.agentmarshal/journal/tasks/CR-117/contract.md`, наличие подкоманды `brief --task` в `src/agentmarshal/cli.py:109-112`, подкоманду `openspec archive` (упомянута как published CLI в `.agents/skills/openspec-archive-change/SKILL.md`) и последовательность проверок в `gitflic-ci.yaml`.

Что сходится по критериям:
- Границы (scope/departure, `.agentmarshal/journal/` неизменяем, остальное под `.agentmarshal/` по scope, никаких git-команд, проверка утверждений по файлу) — `AGENTS.md:24-36`.
- Чтение задачи и правила OpenSpec (архив только когда scope называет `openspec/changes/archive/` и `openspec/specs/<capability>/`, только командой архивации, никогда не править `openspec/specs/` вручную, Purpose новой capability — в delta) — `AGENTS.md:7-22`.
- Последовательность проверок в `AGENTS.md:43-50` побайтово совпадает с `CONTRIBUTING.md:109-116`, без path-аргументов и идентична CI-скрипту в `gitflic-ci.yaml`; раздел Report покрывает три требуемых пункта (`AGENTS.md:55-61`).
- Путей вне репозитория нет, все инструменты published (`uv`, `pytest`, `ruff`, `mypy`, `agentmarshal`, `openspec`); ссылка из раздела Development — `CONTRIBUTING.md:121-123`.
- Диff трогает ровно два пути из scope; изменения только в markdown, тесты корневые документы не читают (`tests/test_quickstart.py` смотрит лишь `docs/quickstart.md`), так что CI-последовательность не затронута.

Advisory (не блокирует, за пределами критериев приёмки): `AGENTS.md` не упоминает `AGENTMARSHAL_ACTOR`, хотя `CONTRIBUTING.md:87-92` требует от агента объявлять себя через эту переменную. Контекст контракта прямо называет вторую аудиторию файла — агент внешнего контрибьютора, — и такой агент из `AGENTS.md` об этом правиле не узнает. Один пункт в Boundaries закрыл бы разрыв; настройка окружения, впрочем, может считаться делом harness/координатора, что контракт относит к non-goals.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "bb80247d1566e7d03f9c232e380625a1d8aaae7e", "verdict": "approved", "findings": [], "advisory_findings": ["agents-md-omits-actor-declaration"]}
AGENTMARSHAL_VERDICT_END
