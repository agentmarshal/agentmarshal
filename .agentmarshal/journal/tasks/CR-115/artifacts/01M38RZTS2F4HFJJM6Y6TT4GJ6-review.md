Проверил дифф против контракта: версия, CHANGELOG, UPGRADING, все install-пины и все утверждения о текущем релизе.

Что сошлось:

- `pyproject.toml:3`, `src/agentmarshal/__init__.py:3` и запись editable-пакета в `uv.lock:11` — все три держат `0.4.1`; `--version` печатает `__version__`, это закреплено `tests/test_smoke.py:48`. Ни одного остатка `0.5.0` в `src/`, `tests/`, `uv.lock`, `docs/` не осталось.
- CHANGELOG: раздел `## 0.4.1 — 2026-09-24` датирован днём релиза, каждая из трёх записей названа своей задачей (CR-114, CR-112, CR-113), запись про фикс прямым текстом говорит, что делает установка, которой 0.4.0 отказал, и ссылается на UPGRADING. Описание правила сверил с `src/agentmarshal/journal/records.py:489-524`: категории `Cc`, `Cs`, `Zl`, `Zp` плюс bidi-символы, и это действительно один предикат `forges_rendered_text` на records и contracts — «не могут разойтись» подтверждается кодом. Раздел 0.4.0 не тронут, новых записей в нём нет.
- UPGRADING: раздел переозаглавлен в `## 0.4.0 → 0.4.1` и прямо говорит, что кроме установки ничего не требуется; прежний подраздел про отказ стал `###` внутри него. Ссылок на старый анchor («#after-040-…») в репозитории нет, так что переименование ничего не сломало.
- Все команды установки, которые читатель может выполнить, называют 0.4.1: `README.md:79`, `docs/quickstart.md:26`, `docs/sidecar.md:75`, и пример `framework.version` в sidecar. `tests/test_quickstart.py:27` исполняет только блоки раздела «The governed loop», так что несуществующий пока пин из раздела Install в CI не выполняется.
- Утверждения о текущем релизе переведены на 0.4.1 везде, где их достигает читатель: `docs/overview.md:146,149,157,165`, ADR-0004:105, ADR-0005:26, `docs/proposals/README.md:81`, `024-…md:72`. История сохранена своими номерами: README:61 «New in 0.4.0», строки про 0.3.0, раздел 0.3.0 → 0.4.0 в UPGRADING, «0.1.0 boundary» в ADR. Шаблон `templates/github/agentmarshal-governance.yml` пина не содержит, CI-конфиги версию не проверяют.
- CR-110 и CR-111 в раздел 0.4.1 не попали справедливо: они прошли до тега (CR-111 назван в записи 0.4.0, `CHANGELOG.md:80`), первой задачей после тега была CR-112.

Два некритичных замечания.

`docs/quickstart.md:6` теперь утверждает, что каждая команда раздела «The governed loop» прогнана на wheel `agentmarshal` 0.4.1, собранном до публикации. Ни в диффе, ни в журнале CR-115 (`records/` — только `opened` и две поправки, ни session-записи, ни артефактов) следов такого прогона нет; изменён только номер в предложении. Поведение `validate` с CR-114 поменялось, так что транскрипт 0.4.0 автоматически утверждением про 0.4.1 не становится — существо проверяет `tests/test_quickstart.py` на дереве исходников, но именно про wheel это заявление не подтверждено. Тот же класс замечания журнал уже фиксировал как некритичный в CR-109.

`CONTRIBUTING.md:127` и `UPGRADING.md:35` — новые строки не перенесены по ширине остального текста (~80 колонок): в CONTRIBUTING строка «release sets the version it publishes, replacing whatever the branch carried; the first task after the tag…» и в UPGRADING «place that runs `validate`, `status`, `gate` or `complete`, and the journal reads as it did before 0.4.0. There is no». Линтер markdown в CI отсутствует, так что это только расхождение с конвенцией файлов.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e2f86c676683f035dac392b4a10bd48409c77fde", "verdict": "approved", "findings": [], "advisory_findings": ["quickstart-041-wheel-run-unverified", "prose-lines-unwrapped-in-contributing-and-upgrading"]}
AGENTMARSHAL_VERDICT_END
