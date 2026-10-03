Проверил снапшот `6a3fc5fc78cd5783788733a01d816055b8ce6ab3` статически: прочитал `localstate.py`, изменённый `project.py`, `tests/test_localstate.py`, archived change, опубликованный spec, ADR-0014/0022 и всех остальных потребителей хелпера.

Что сошлось:

- `local_state(placement)` спрашивает git про `placement.project_root` — репозиторий журнала в обеих placement (`placement.py:76-100`), так что sidecar структурно не может уехать в host; все шесть локаций — `log/`, `extensions/`, `deps/`, `trust.toml`, `switches.toml`, `plan.toml` — совпадают с картой ADR-0014 и `plan.toml` из ADR-0022 §7.
- `_git_common_dir` именно вынесен, а не скопирован: единственный вызов `git rev-parse --path-format=absolute --git-common-dir` остался в `project.py:349`, `grep` других не находит. Проверка в `initialize_project:427` сохранила семантику — `reason` исключён из равенства (`compare=False`), поэтому два «неопределённых» ответа по-прежнему равны и отказ «worktree of host» жив (пинится `tests/test_placement.py:123` на настоящем worktree).
- Resolve ничего не создаёт, создание — отдельный `ensure_directory`; отказ даёт `LocalStateError` с путём репозитория и собственным stderr git, а `GitNotAvailableError` → `LocalStateError` (CLI ловит `AgentMarshalProjectError`, так что traceback не вылезет и из `initialize_project`).
- Все 8 сценариев delta-спеки названы в docstring-ах тестов; change заархивирован в `openspec/changes/archive/2026-10-03-local-state-location/` с живым Purpose в `openspec/specs/local-state/spec.md`, относительные ссылки на ADR из архивной позиции корректны; модуль ещё никем в `src/` не используется.

Оговорка: прогнать `uv run pytest / ruff / mypy / agentmarshal validate` в этой песочнице не удалось — запуск команд отклонён, подтвердить «full CI sequence passes» я могу только статически (по чтению ничего не ломается: длины строк, импорты, strict-типы, `NoReturn`-заглушка monkeypatch в порядке).

Два неблокирующих замечания.

Первое: `src/agentmarshal/localstate.py:83-93` — в sidecar, журнальный репозиторий которого сам является linked worktree хоста, `git_common_dir(project_root)` вернёт именно `.git` хоста, и local state ляжет в хост, то есть ровно то, что запрещают ADR-0008 и требование «never the host's» в спеке. Создать такую конфигурацию через `init` нельзя (её и отсекает сравнение в `project.py:427`), но при ручной правке `project.json` или добавлении worktree позже на моменте resolve ничего не перепроверяется, хотя `placement.host_root` под рукой и та же проверка стоила бы одного сравнения.

Второе: `src/agentmarshal/localstate.py:96-108` — `ensure_directory` принимает любой `Path` и делает `mkdir(parents=True)`, так что заявленное в design «a caller cannot get the sidecar case wrong because there is nothing to get wrong» относится только к половине «resolve»; половина «create» никак не привязана к `LocalState.root`, и тест про неизменность хоста доказывает свойство лишь для правильно разрешённых путей, а не для API.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "6a3fc5fc78cd5783788733a01d816055b8ce6ab3", "verdict": "approved", "findings": [], "advisory_findings": ["sidecar-journal-that-is-a-worktree-of-host-resolves-into-hosts-gitdir", "ensure-directory-accepts-any-path-without-containment"]}
AGENTMARSHAL_VERDICT_END
