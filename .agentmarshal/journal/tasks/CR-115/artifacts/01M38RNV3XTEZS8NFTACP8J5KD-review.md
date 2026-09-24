Прошёлся по всему diff'у и по состоянию дерева в снапшоте. Сначала что подтвердилось.

**Проверено и сходится:**
- Версия `0.4.1` стоит во всех трёх местах (`pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11`), `--version` печатает `__version__` (`src/agentmarshal/cli.py:86-88`), `tests/test_smoke.py:48` обновлён. Ни один тест не завязан на `.dev`-суффикс.
- `CHANGELOG.md:11` — секция `0.4.1 — 2026-09-24`, все три задачи (CR-114, CR-112, CR-113) присутствуют, запись про фикс говорит, что делает установка, которая напоролась на отказ; секция 0.4.0 не тронута. Описание правила совпадает с кодом: `_FORGEABLE_CATEGORIES`/`_BIDIRECTIONAL_CONTROLS` и все пять мест вызова (`records.py:364,383,414,426,470,481`, `contracts.py`, `artifacts.py`) — «acceptance field», «finding summary», «artifact reference», «contract header entry» все реально проверяются.
- `UPGRADING.md:3` озаглавлен как шаг `0.4.0 → 0.4.1` и прямо говорит, что больше ничего делать не нужно.
- Все statement'ы про текущий релиз переехали на 0.4.1 (README 12/16/46/57, overview 146/149/157/165, ADR-0004:105, ADR-0005:26, quickstart 198/207/363, sidecar 75/125, индекс proposals:81, proposal 024:72), а история 0.4.0 сохранена (README:61, 024:66, строки таблиц про 014–023).
- Все install-команды, которые читает новый пользователь, называют 0.4.1 (README:79, quickstart:26, sidecar:75); шаблоны в `templates/` пинов версии не содержат. Замена пина в quickstart не ломает CI: `tests/test_quickstart.py:27` берёт только блоки из `## The governed loop`, а install-блок выше этого раздела.

Дальше — замечания.

`UPGRADING.md:70` и `UPGRADING.md:78` всё ещё ведут установку с закреплённой 0.3.0 через 0.4.0 («change the pin to `==0.4.0`», «Verify `agentmarshal --version` reports `0.4.0` everywhere, then run `agentmarshal validate`»), а это ровно тот читатель, из-за которого существует релиз: по CR-114 журнал адоптера проходит под 0.3.0 и падает целиком под 0.4.0, записи закрытых задач не починить. Новая секция `0.4.0 → 0.4.1` нигде не говорит, что 0.4.0 можно пропустить и пиниться сразу на 0.4.1. Править историю 0.4.0 нельзя (критерий 4), но одной фразы в новой — уже входящей в scope — секции достаточно.

`CONTRIBUTING.md:128` и `UPGRADING.md:35` — одиночные строки на ~137 и ~116 символов в файлах, которые везде жёстко завёрнуты на ~80; в `README.md:60-62` абзац переwrapлен рвано. Ни один линтер markdown не гоняет, так что CI зелёный, но релизный коммит везёт следы ручной правки.

`docs/quickstart.md:6` теперь утверждает, что весь транскрипт прогнан на wheel `0.4.1`, собранном до публикации. Проверить это по diff'у нельзя: `tests/test_quickstart.py` повторяет цикл из исходного дерева, а не из wheel. Добавленный критерий требует, чтобы это утверждение осталось правдой, — сборку wheel и прогон нужно предъявить в completion (та же претензия уже звучала на CR-109).

Отдельно: критерий 5 я подтвердить не могу — в окружении нет ни `uv`, ни `pytest`, а запуск команд ограничен, так что полную последовательность CI и read-only `validate` по журналу адоптера должен зафиксировать completion.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e2f86c676683f035dac392b4a10bd48409c77fde", "verdict": "changes_required", "findings": ["upgrading-routes-pinned-0-3-0-adopter-through-0-4-0"], "advisory_findings": ["release-prose-unwrapped-lines", "quickstart-0-4-1-wheel-claim-unevidenced"]}
AGENTMARSHAL_VERDICT_END
