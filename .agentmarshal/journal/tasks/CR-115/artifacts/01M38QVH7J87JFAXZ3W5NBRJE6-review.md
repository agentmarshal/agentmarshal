Проверил снапшот по контракту: версии, документы, ссылки на код и журнал. Команды в этом окружении выполнять не дали, поэтому CI-последовательность и прогон `validate` по журналу адоптера (критерий 5) я не запускал — они остаются за completion-записью; всё остальное проверено чтением.

Что сошлось:

- Версия 0.4.1 стоит в `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11` и в `tests/test_smoke.py:48`; `--version` печатает `__version__` (`src/agentmarshal/cli.py:88`), это закреплено тестом.
- CHANGELOG: секция `0.4.1 — 2026-09-24` называет все три задачи (CR-112, CR-113, CR-114), 0.4.0 не тронута. Утверждения про CR-114 сходятся с кодом: `_FORGEABLE_CATEGORIES = {"Cc","Cs","Zl","Zp"}` и `_BIDIRECTIONAL_CONTROLS` в `src/agentmarshal/journal/records.py:498-509`, один предикат `forges_rendered_text` вызывается из `contracts.py:64` и `validate.py:72`. Про CR-112 — проверка в `.github/workflows/release.yml:43-48` действительно отклоняет dev/local версии.
- UPGRADING: раздел озаглавлен `0.4.0 → 0.4.1` и прямо говорит, что ничего другого делать не требуется; адоптеру названа конкретная версия.
- Все install-пины и все утверждения о текущем релизе переведены на 0.4.1 (README, quickstart, sidecar, overview, ADR-0004/0005, индекс proposals, proposal 024); исторические номера (0.1.0/0.2.0/0.3.0/0.4.0 как история, строки 014–023 в индексе) остались на месте. Транскрипты quickstart версию не содержат, `tests/test_gate.py::released_030` не задет.

Ниже — непринципиальные замечания.

**contributing-release-example-contradicts-the-rule** — `CONTRIBUTING.md:126-129`: пример «0.4.1 was published from a branch carrying `0.5.0.dev0`» буквально противоречит следующей же фразе («the task that prepares a release sets the version it publishes, replacing whatever the branch carried»): тегируемый коммит несёт 0.4.1, а не `0.5.0.dev0`. Смысл понятен («ветка угадала 0.5.0, а понадобился патч»), но формулировка описывает публикацию неверно — в том самом разделе, который эта задача и переписывала из-за неточного примера.

**readme-status-paragraph-not-rewrapped** — `README.md:60-68`: после вставки предложения про 0.4.1 абзац не переформатирован: строка 62 обрывается на половине ширины, а строка 68 уходит примерно на 130 символов при принятых в файле ~79. Чисто косметика, но диффом внесена именно здесь.

**upgrading-0-4-1-omits-the-pin-change** — `UPGRADING.md:3-7`: у всех предыдущих разделов есть блок «Per installation method» с явным «change the pin to `==X`», а у 0.4.0 → 0.4.1 его нет. Адресат этого раздела — как раз закреплённая установка (адоптер сидел на pinned 0.3.0), и ей недостаточно «install it»: нужно поменять пин на `==0.4.1`. Критерию контракта текст формально удовлетворяет.

**quickstart-wheel-claim-unevidenced** — `docs/quickstart.md:6`: утверждение «was run against a wheel of `agentmarshal` 0.4.1 built before the release was published» в диффе поменяло только номер; подтверждения нового прогона wheel'а нет. Косвенно его держит `tests/test_quickstart.py`, который повторяет блоки страницы по исходникам (то есть по 0.4.1) в CI, — но это прогон по дереву, а не по wheel'у; стоит назвать прогон в completion.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "11f369757322cd792364b6e030dd75f30cd2461b", "verdict": "approved", "findings": [], "advisory_findings": ["contributing-release-example-contradicts-the-rule", "readme-status-paragraph-not-rewrapped", "upgrading-0-4-1-omits-the-pin-change", "quickstart-wheel-claim-unevidenced"]}
AGENTMARSHAL_VERDICT_END
