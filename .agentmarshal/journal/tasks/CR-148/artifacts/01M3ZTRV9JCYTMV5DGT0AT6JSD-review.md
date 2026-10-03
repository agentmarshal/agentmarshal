Проверил весь diff статически: прогнать `uv run pytest` / `ruff` / `mypy` в этой песочнице не дали (команды требуют подтверждения, сессия неинтерактивная), поэтому критерий «полная CI-последовательность проходит» я подтвердить исполнением не могу — ниже только то, что проверяется чтением.

**Что сошлось с контрактом**

- `openspec/changes/archive/2026-10-03-local-state-location/` содержит proposal.md, design.md, tasks.md, `.openspec.yaml` и дельту `specs/local-state/spec.md` с `## ADDED Requirements`; `openspec/specs/local-state/spec.md` сгенерирован в том же формате, что и соседние capability-спеки (`# <name> Specification` / `## Purpose` / `## Requirements`), Purpose не заглушка. Все 8 сценариев дельты дословно названы в docstring'ах тестов (`tests/test_localstate.py`), сценарий «a project outside git fails cleanly» покрыт двумя тестами.
- `local_state()` (`src/agentmarshal/localstate.py:75`) берёт `placement.project_root` — в обоих placement'ах это репозиторий с журналом, host в вызов не входит структурно. Шесть именованных локаций совпадают с картой мест ADR-0014 (строки 159–164) и `plan.toml` из ADR-0022 §7.
- Хелпер не скопирован: `_git_common_dir` переименован в `git_common_dir` (`src/agentmarshal/project.py:349`), единственный вызывающий — `initialize_project`; grep по репозиторию других копий не находит.
- Резолв ничего не создаёт, создание — отдельный `ensure_directory`; `GitNotAvailableError` и ненулевой exit git'а заворачиваются в `LocalStateError` с путём и причиной от самого git, а не traceback. `_run_init` ловит `AgentMarshalProjectError` (`src/agentmarshal/cli.py:357`), так что новое пробрасывание `GitNotAvailableError` из `git_common_dir` не даёт traceback в CLI.
- Ничто в `src/` модуль не импортирует — только тесты. Существующий тест «worktree of host» (`tests/test_placement.py:123`) переживает замену на dataclass: `reason` помечен `compare=False`, так что два `GitCommonDir(None, ...)` сравниваются равными ровно как раньше два `None`.

**Advisory-находки**

`design-md-overstates-initialize-project-change`: в `openspec/changes/archive/2026-10-03-local-state-location/design.md` (абзац про `_git_common_dir`) сказано, что теперь `initialize_project` «refuses with the cause named» при любой неопределённости, тогда как `compare=False` на `reason` воспроизводит старое поведение один в один — при отказе обоих вызовов отказ по-прежнему идёт с вводящим в заблуждение «is a worktree of host» и причину не называет, при отказе одного по-прежнему молча проходит. Реально изменился только путь `OSError`, который `find_git_root` отсекает раньше. Код честен (docstring `GitCommonDir` описывает это верно) — неточен именно архивный design.md.

`test-hardcodes-git-wording`: `tests/test_localstate.py:200` требует дословную английскую фразу git'а `"not a git repository"`, хотя соседний тест на строке 203 в своём же docstring обосновывает, что формулировки git нельзя угадывать и спрашивает их у git напрямую. Сообщения git локализуются, так что у разработчика с нерусской/нелокалью C тест падает; в CI (`python:3.12-slim`, локаль C) это скрыто.

Ни одна из двух находок не ломает поведение и не нарушает критерий приёмки, поэтому блокировать нечего.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a7baf413ebf06a33d7bd1a87ebf7ec43eb56815e", "verdict": "approved", "findings": [], "advisory_findings": ["design-md-overstates-initialize-project-change", "test-hardcodes-git-wording"]}
AGENTMARSHAL_VERDICT_END
