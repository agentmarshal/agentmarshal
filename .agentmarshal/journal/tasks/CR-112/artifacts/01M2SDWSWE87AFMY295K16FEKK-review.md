Я не смог запустить CI: песочница запретила `uv sync`, `pytest`, `ruff`, `mypy` и даже `python3`. Поэтому последний критерий приёмки я проверил только статически.

Что проверил:
- **Версия.** `0.5.0.dev0` стоит во всех трёх местах: `pyproject.toml`, `src/agentmarshal/__init__.py`, `uv.lock`. В `uv.lock` она записана в канонической форме PEP 440, так что `uv sync --locked` не должен расходиться с lock-файлом. `--version` печатает `__version__`, это проверяет `tests/test_smoke.py:51`.
- **Запись версии в журнал.** `tool_version` в записях журнала проверяется только на непустую строку (`src/agentmarshal/journal/records.py:251`). Dev-версия ничего не ломает.
- **Release workflow.** Новая проверка идёт сразу после проверки тега, в том же шаге и до `uv build`. Сначала версия приводится к нижнему регистру, затем отклоняется любая версия с `dev` или `+`. Это покрывает все формы dev-версий по PEP 440 (`.dev0`, `-dev`, `dev`, `.dev`) и local-версии. Pre-release версии (`a`/`b`/`rc`) проходят, и контракт этого не запрещает.
- **Тесты с транскриптом 0.3.0.** Поиск опубликованного 0.3.0 в `tests/test_gate.py:33` не менялся: он по-прежнему ищет `--version` = `0.3.0` и отсутствие команды `finding`. На сборку `0.5.0.dev0` он не срабатывает, ожидания в тестах не тронуты.
- **CONTRIBUTING.md.** Правило изложено полностью: `.dev0` на default branch, release-задача снимает суффикс, первая задача после тега его возвращает.
- **Границы задачи.** Правки только в файлах из scope, записи в CHANGELOG нет, поведение не меняется.

Замечание вне scope, в вердикт не входит: docstring `released_030` в `tests/test_gate.py` теперь устарел. Там сказано, что эта сборка «prints the same one until the release bumps it», но `tests/test_gate.py` вне scope, а менять поиск 0.3.0 non-goals запрещают.

Блокирующих находок нет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d29de6108c46cbce3f6c59f0a0ad83ab148a8f4f", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
