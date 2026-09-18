Проверил diff для CR-112 по снапшоту, прогнать CI-последовательность не удалось. Здесь запрещён запуск `uv`/`python` (`uv sync`, `pytest`, `ruff`, `mypy`, `agentmarshal --version`), поэтому всё ниже основано на чтении кода.

**Критерии приёмки:**
- **Версия `0.5.0.dev0`:** стоит одинаково в `pyproject.toml`, `src/agentmarshal/__init__.py` и в записи пакета в `uv.lock`. `agentmarshal --version` берёт её из `__version__` (`cli.py:88`), а `test_console_version_prints_package_version` это проверяет. Сам вывод команды я не видел.
- **Правило в `CONTRIBUTING.md`:** описаны все три части — суффикс `.dev0` на default branch, релизная задача его снимает, задача после тега возвращает. Тот же раздел говорит, что workflow отказывается публиковать dev- и local-версии.
- **Проверка в `release.yml`:** стоит в шаге «Verify tag matches project version», после проверки тега и до `uv build`. Существующая проверка тега не тронута.
- **Тесты на опубликованный 0.3.0 не менялись:** `tests/test_gate.py` находит 0.3.0 по выводу `--version` и проверке команды `finding`, изменение этого не задевает. Версия в коде нигде не разбирается: `records.py:252` проверяет только непустую строку. Упоминания `0.4.0` в `UPGRADING.md` и `docs/` относятся к опубликованному релизу и должны остаться. CHANGELOG, как и требует контракт, не тронут.

**Замечание, не блокирующее (`release-dev-check-case-sensitive`):** в `.github/workflows/release.yml:42` образец `*dev*|*+*` чувствителен к регистру. PEP 440 регистр не различает, поэтому `0.5.0.DEV0` с тегом `v0.5.0.DEV0` пройдёт обе проверки, `uv build` нормализует версию до `0.5.0.dev0`, и на PyPI уйдёт dev-сборка. Практически это маловероятно. Закрывается приведением версии к нижнему регистру перед `case` или нормализацией через `packaging`.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e331d242dc58e2f79250934ee636cccad9e3ccb4", "verdict": "approved", "findings": [], "advisory_findings": ["release-dev-check-case-sensitive"]}
AGENTMARSHAL_VERDICT_END

Коннекторы claude.ai Gmail, Google Calendar и Google Drive не авторизованы. Для этого ревью они не нужны, но пока их не подключат в настройках коннекторов claude.ai, они недоступны.
