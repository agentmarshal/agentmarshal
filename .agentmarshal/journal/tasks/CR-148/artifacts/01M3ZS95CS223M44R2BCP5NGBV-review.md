Review готов. Прогнать CI-последовательность в этой сессии не получилось (команды `uv run` требуют интерактивного подтверждения, которого здесь нет), поэтому AC5 «full CI sequence passes» я проверил только статически: синтаксис, длины строк под 88, аннотации под `mypy --strict`, magic trailing comma в импорте (ruff format не схлопнет его), отсутствие других потребителей модуля.

По существу контракт выполнен:

- Все восемь сценариев delta-спеки имеют тест, docstring которого называет сценарий дословно — `tests/test_localstate.py` закрывает embedded, linked worktree, sidecar, именованные локации, неизменность host, «resolve ничего не создаёт», явное создание и чистую ошибку.
- Изменение заархивировано: `openspec/changes/archive/2026-10-03-local-state-location/` (proposal, design, tasks, delta) + `openspec/specs/local-state/spec.md` с настоящим Purpose, а не плейсхолдером; `openspec/changes/` пуст, кроме `archive`. Формат совпадает с соседними архивами, включая `.openspec.yaml`.
- Хелпер не скопирован, а раскрыт: `_git_common_dir` → `git_common_dir` в `project.py:332`, единственное место, спрашивающее git; grep подтверждает, что второй копии нет.
- Имена локаций совпадают с картой ADR-0014 (строки 158–164) и `plan.toml` из ADR-0022 (строка 247).
- `local_state` берёт `placement.project_root`, так что `host_root` в вызов структурно не попадает; модуль нигде ещё не используется.

Теперь то, что я считаю достойным замечания — всё необязательное.

**`localstate-error-cause-not-from-git`** — `src/agentmarshal/localstate.py:88`: при ненулевом коде возврата git'а stderr отбрасывается и подставляется фиксированная причина «(not a git worktree)». Сценарий спеки требует «git's reason», а Risks в design.md обещает, что устаревший worktree-указатель «git itself reports the failure; same clean error path». На деле реальные причины — `detected dubious ownership in repository` (safe.directory, частая вещь в CI) или git старше 2.31, который не знает `--path-format=absolute` — будут отрапортованы оператору как «это не git worktree», то есть ложно. Это ровно та же конвенция, что у `find_git_root`, поэтому не блокирую, но причина здесь действительно не от git.

**`init-comment-overstates-the-fix`** — `src/agentmarshal/project.py:410` и соответствующее решение в `design.md`: комментарий утверждает, что неразрешимое сравнение «now it refuses once, naming why», а design.md — что «now any failure refuses with the cause named». Обработан только `GitNotAvailableError`; ветка, где оба вызова вернули `None`, по-прежнему проваливается в сравнение `None == None` и отказывает сообщением «sidecar journal X is a worktree of host Y» — ложным утверждением без причины. На git < 2.31 эта ветка достижима и отвергнет любой корректный `init --host`. Сама дыра досталась в наследство; новое здесь — комментарий, который говорит, что её закрыли.

**`git-common-dir-docstring-contradiction`** — `src/agentmarshal/project.py:333`: первая строка docstring осталась «or `None` if git cannot say», тогда как добавленный ниже абзац ровно эти случаи (git не запускается, вывод не UTF-8) переводит в исключение. Читающий только сводку получит прежний контракт.

**`tree-snapshot-helper-duplicated`** — `tests/test_localstate.py:54` дословно повторяет `_tree_snapshot` из `tests/test_placement.py:178`. Обе версии фильтруют `path.is_file()`, так что «byte-for-byte what they were before» из спеки не покрывает появление пустых каталогов в host. Настоящий режим отказа тест всё же ловит — три `.toml` пишутся файлами и при неверном корне всплыли бы в снимке, — но утверждение шире, чем проверка.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "df7f28f5d7facb186b02eb456aabeb7a44108550",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "localstate-error-cause-not-from-git",
    "init-comment-overstates-the-fix",
    "git-common-dir-docstring-contradiction",
    "tree-snapshot-helper-duplicated"
  ]
}
AGENTMARSHAL_VERDICT_END
