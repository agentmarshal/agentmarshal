Проверил diff по контракту CR-115: все 15 файлов в scope, версия 0.4.1 согласована в `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11` и `tests/test_smoke.py:48` (а `--version` печатает `__version__`, что закреплено тестом `test_console_version_prints_package_version`).

Содержательные утверждения тоже сверил с кодом, а не только с текстом:
- Заявление CHANGELOG «one predicate decides it for records, contract headers and the artifact reference» подтверждается: `forges_rendered_text` определён в `src/agentmarshal/journal/records.py:512` и вызывается из `contracts.py:64` и `validate.py:72`.
- Набор отказываемых символов (`Cc`, `Cs`, `Zl`, `Zp` + bidi) в CHANGELOG и UPGRADING совпадает с `_FORGEABLE_CATEGORIES` и `_BIDIRECTIONAL_CONTROLS`.
- `docs/sidecar.md:125` с `"version": "0.4.1"` корректен: `initial_project_data` (`src/agentmarshal/project.py:130`) пишет туда `__version__`.
- Историю не переписали: «New in 0.4.0» в README, дисп未позиции proposals 014–023 и датированная заметка «Later — 2026-09-18» в proposal 019 сохранили свои номера. Прежняя секция `## After 0.4.0` в UPGRADING демонтирована в `### A review record refused over a space separator`, и якорных ссылок на неё нигде нет.
- Не осталось ни одного install-пина на 0.4.0: `README.md:80`, `docs/quickstart.md:26`, `docs/sidecar.md:75` — все 0.4.1. Упоминание `0.5.0.dev0` в `CONTRIBUTING.md:127` теперь подано как история этой ветки, а не как правило.

Два замечания без блокировки.

Первое: `UPGRADING.md:78` — в процедуре перехода 0.3.0 → 0.4.0 шаг 3 по-прежнему требует «Verify `agentmarshal --version` reports `0.4.0` everywhere», хотя новый абзац на `UPGRADING.md:9-13` отправляет того же читателя ставить `==0.4.1`. Оговорка на строке 10 покрывает пин, но не шаг проверки: читатель увидит 0.4.1 и решит, что апгрейд не встал.

Второе: `docs/quickstart.md:6` теперь утверждает, что весь transcript раздела «The governed loop» прогнан на wheel 0.4.1. В diff изменён только номер, и ни в нём, ни в записях CR-115 нет следа повторного прогона. Фактически transcript не пострадал — нигде в нём не печатается версия, а `tests/test_quickstart.py` гоняет цикл из исходников в CI, — но добавленный критерий контракта требует, чтобы утверждение оставалось истинным для названного wheel, так что прогон стоит зафиксировать в completion вместе с CI и read-only `validate` по журналу адоптера.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "da1bb6b778f885455cd0692847ffec6093a0644c", "verdict": "approved", "findings": [], "advisory_findings": ["upgrading-0-3-0-procedure-still-verifies-0-4-0", "quickstart-0-4-1-wheel-claim-unverified"]}
AGENTMARSHAL_VERDICT_END
