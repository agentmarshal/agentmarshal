В рамках контракта CR-112 блокирующих проблем нет, оценка — approved, с одним advisory-замечанием.

- **Версия.** `0.5.0.dev0` стоит во всех трёх местах из контракта: `pyproject.toml`, `src/agentmarshal/__init__.py` и `uv.lock`. `agentmarshal --version` печатает `__version__`, это проверяет `tests/test_smoke.py`, где ожидание обновлено.
- **CONTRIBUTING.md.** Новый раздел «Versions» описывает все три части правила: ветка по умолчанию несёт следующую версию с `.dev0`, задача релиза убирает суффикс, первая задача после тега его возвращает.
- **Workflow релиза.** Новая проверка запускается в шаге «Verify tag matches project version», после сверки тега и до `uv build`. Проверка тега осталась без изменений. Если `v0.5.0.dev0` запушат по ошибке, сверка тега пройдёт, а новая проверка остановит workflow.
- **Тесты 0.3.0.** Ожидания в `tests/test_gate.py::released_030` не тронуты, как требует контракт. Теперь `0.5.0.dev0` не совпадёт с `0.3.0`, так что сборка из default branch отсеивается уже по строке версии. Docstring в этой функции («The version string cannot tell the release from this build…») устарел, но файл вне scope, и менять способ поиска релиза контракт прямо запрещает (non-goal).
- **Что я не запускал.** `uv lock --check` и тесты не выполнены: запуск требовал подтверждения, а сессия non-interactive. Изменение в `uv.lock` совпадает с тем, что сгенерировал бы `uv lock` для editable-проекта, но полный прогон CI я не подтверждаю.

Advisory: проверка `case "$version" in *dev*|*+*)` в `.github/workflows/release.yml:42` чувствительна к регистру. PEP 440 допускает написание в любом регистре, поэтому версия вроде `0.5.0.DEV0` (с тегом `v0.5.0.DEV0`) пройдёт и сверку тега, и эту проверку. Потом `uv build` нормализует её в `0.5.0.dev0` и опубликует development-сборку. Надёжнее приводить строку к нижнему регистру или нормализовать через `packaging.version.Version(...).is_devrelease` / `.local`.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e331d242dc58e2f79250934ee636cccad9e3ccb4", "verdict": "approved", "findings": [], "advisory_findings": ["release-dev-check-case-sensitive"]}
AGENTMARSHAL_VERDICT_END

Claude.ai-коннекторы Gmail, Google Calendar и Google Drive ждут авторизации в настройках коннекторов на claude.ai. Для этого ревью они не нужны.
