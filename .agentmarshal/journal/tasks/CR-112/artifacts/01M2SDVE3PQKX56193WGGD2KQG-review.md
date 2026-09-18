Замечаний нет: ни блокирующих, ни advisory.

Сам CI я не запустил: окружение не разрешило команды `uv sync`, `pytest`, `ruff` и `mypy`. Так что пункт «весь CI проходит» я проверил только по коду. Для такого диффа риск небольшой.

- **Версия.** `0.5.0.dev0` стоит в `pyproject.toml`, `src/agentmarshal/__init__.py` и в записи editable-пакета в `uv.lock`. Команда `--version` берёт строку из `__version__` (`cli.py:86-88`), а `test_console_version_prints_package_version` сверяет вывод с ней. В записях журнала версия хранится как обычная строка без проверки формата (`tool_version`), поэтому суффикс `.dev0` ничего не ломает. `uv sync --locked` должен остаться согласованным.
- **Правило в CONTRIBUTING.md.** Новый раздел «Versions» описывает все три части правила: на default branch лежит следующая версия с `.dev0`, задача релиза убирает суффикс, первая задача после тега возвращает его.
- **Workflow релиза.** Новая проверка стоит в шаге «Verify tag matches project version», до `uv build`. Существующее сравнение тега с версией осталось на месте. Версию она сначала переводит в нижний регистр, поэтому ловит `dev` в любом регистре и написании (`.dev0`, `-dev`, `dev`), а по `+` ловит local-версии. Pre-release вроде `rc` проходит, и это правильно: критерий требует отсекать только dev- и local-версии.
- **Тесты 0.3.0.** Диф не трогает `tests/test_gate.py` и `tests/test_review_launcher.py`. Опубликованный 0.3.0 по-прежнему ищется по `--version == "0.3.0"` плюс отсутствию команды `finding`, и новая dev-версия эту проверку не задевает. Изменён только `test_version_is_declared` в `test_smoke.py`, и так и должно быть.
- **Scope и Non-Goals.** Все изменённые файлы входят в scope. CHANGELOG не тронут, поведение программы не меняется.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d29de6108c46cbce3f6c59f0a0ad83ab148a8f4f", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
