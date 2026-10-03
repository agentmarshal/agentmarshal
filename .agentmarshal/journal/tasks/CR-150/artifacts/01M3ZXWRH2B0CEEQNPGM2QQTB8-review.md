Проверил контракт, диff и фактическое состояние репозитория (`outbox.py`, `capture.py`, `gate.py`, `project.py`, ADR-0020, CONTRIBUTING, архив изменения и опубликованный spec).

Что сходится:

- **AC1** — в `openspec/changes/archive/2026-10-03-outbox-new-and-check/` есть `proposal.md`, `design.md`, `tasks.md`, `specs/outbox/spec.md`; `.openspec.yaml` такой же, как у соседних архивов. `diff` между delta и `openspec/specs/outbox/spec.md` — ровно та подстановка, которую делает `openspec archive` (`# Spec Delta` → `# outbox Specification`, `## ADDED Requirements` → `## Requirements`), то есть правка руками исключена. Все 21 сценарий спеки покрыты тестами, чей docstring их называет.
- **AC2** — `_write_draft` считает максимум из `NNNN-<slug>.md` с исключением дат, создаёт через `O_EXCL` с инкрементом при коллизии (перезаписать нельзя ни гонкой, ни подложенным файлом), `_FIELD_HINTS` совпадает с CONTRIBUTING.md:38-42 дословно, Version из `__version__`, Environment из `platform.platform()` (не содержит hostname — приятная деталь), путь печатается, отсутствие outbox отказывается с сообщением. Схема имени описана в design.md.
- **AC3/AC4** — README исключён только из проверки полей (`is_draft = entry.name != _README`), но его имя и содержимое идут в скан; `_is_regular` отвергает symlink/каталог/FIFO и валит прогон; non-UTF-8 декодируется lossy и всё равно обыскивается; имя файла сканируется отдельно (`_name_hits`) и маскируется через `safe_path` везде, включая строки конформности; `_os_error_text`/`_config_error_text` не печатают ни `str(OSError)`, ни текст `GateError`/`CaptureError` (а `CaptureError` — подкласс `ValueError`, не `GateError`, так что порядок `except` корректен); exit 0 только при пустых `problems`, отсутствии нерегулярных записей и пустых `hits`.
- **AC5** — `cli.py` получил ровно три строки (import, `outbox.register(subparsers)`, dispatch), группа регистрируется из своего модуля. Циклов импорта нет. Проверил `[tool.ruff.lint]` (E,W,F,I,UP,B,SIM,RUF — без `D`), длины подозрительных строк (`outbox.py:80` и `:202` — ровно 88), isort-порядок и mypy-strict узкие места (`error.errno`/`error.strerror` сужаются, `_SubParsersAction[ArgumentParser]` совпадает с типом в `cli.py:92`). Тестов, перечисляющих набор CLI-команд, в `tests/` нет, CI только ubuntu — так что symlink/`chmod(0)`-тесты не упадут.

Запустить сам CI-набор я не смог: в этом снапшоте нет ни `uv`, ни `pytest`, а выполнение `python3 -m pytest` песочница не разрешила. Это единственный критерий (AC5, «full CI sequence passes»), который я подтверждаю только статически, а не прогоном.

Два неблокирующих замечания:

`outbox.py:38-39` заводит собственные литералы `_UPSTREAM_DIR = "upstream"` и `_README = "README.md"`, тогда как создаёт эти же имена `project.py:309-310` в `_scaffold_outbox`; общей константы нет, хотя `project.py` ровно для таких имён экспортирует `PROJECT_DIR_NAME`/`PROJECT_FILE_NAME`/`PROJECT_CONFIG_RELPATH` — переименование в `init` молча разойдётся с `check`, и README начнёт докладываться как draft без всех пяти полей.

`outbox.py:67` — `_HEADING = r"^## (.+?)\s*$"` терпит пробелы справа, но не лишний пробел слева: заголовок `##  Symptom` (два пробела), который CommonMark рендерит точно так же, попадает в группу как `" Symptom"` и поле докладывается как `missing Symptom` — то есть ровно та команда, что существует для объяснения пропусков, даёт сбивающий с толку ответ на опечатку.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1381fd13cd435ec4be0ace67509ca50d1db35ba8", "verdict": "approved", "findings": [], "advisory_findings": ["outbox-duplicates-init-outbox-literals", "heading-match-rejects-extra-leading-space"]}
AGENTMARSHAL_VERDICT_END
