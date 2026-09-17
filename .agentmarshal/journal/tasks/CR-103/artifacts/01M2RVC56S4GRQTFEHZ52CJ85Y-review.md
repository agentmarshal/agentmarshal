Проверил diff против контракта, спеки, ADR-0005 и кода в снапшоте. Запустить тесты в этой сессии не удалось — `pytest`/`python -c` требуют подтверждения, которого в неинтерактивном режиме нет; поэтому проверка статическая, по чтению кода и фикстур.

**Что сходится.**

- Все девять сценариев из `openspec/changes/archive/2026-09-18-bounded-leak-scan-output/specs/leak-scan/spec.md` закрыты тестами, чьи docstring их называют: семь старых в `tests/test_capture.py` (337, 355, 376, 242, 489) и `tests/test_gate.py:1773`, два новых — `tests/test_gate.py:1806` и `tests/test_leak_scan.py:63`. Реализация не отступает от решений design.md: лимит стал параметром, счётчик остался внутри той же строки, двадцать осталось числом гейта.
- Критерий 2. `render_leak_hits(hits, limit)` при `limit=None` не режет ничего и не добавляет суффикс; `src/agentmarshal/cli.py:1309` передаёт именно `None`. Гейт передаёт `_LEAK_HIT_RENDER_LIMIT = 20` (`src/agentmarshal/journal/gate.py:62,1187`), и на 21 попадании строка кончается `, and 1 more not shown`. Порядок попаданий — порядок `git diff`, то есть алфавитный, поэтому `secret00` в строке, а `secret20` нет: ассерты теста опираются на это верно.
- Критерий 3. `render_leak_hits` — единственное место, где собирается `f"{hit.path}: {hit.identification}"`; grep по всему дереву даёт только два вызова (cli и gate) и тесты. Ни один вызывающий не форматирует попадание сам.
- Критерий 4. `docs/sidecar.md:247-248` теперь даёт ровно ту строку, которую пинит `tests/test_gate.py:1795`, байт в байт по шаблону.
- Критерий 5. `LaunchedReview` есть в импорте и в `__all__` (`src/agentmarshal/journal/__init__.py:25,45`), порядок `__all__` и isort не нарушены, строка импорта ровно 88 символов — в лимит ruff попадает. Тест `tests/test_journal.py:94` пинит тождество объекта.
- Scope соблюдён: все десять затронутых путей внутри контракта, архивная директория оформлена как остальные (`.openspec.yaml`, `design.md`, `proposal.md`, `specs/`, `tasks.md`). Опубликованная спека `openspec/specs/leak-scan/spec.md` совпадает с дельтой. CR-100 сценария про границу не заводил, так что переименование `test_a_rendered_warning_is_bounded_and_counts_the_rest` в `test_render_leak_hits_uses_the_callers_limit` ничего не рассиротило.

**Advisory-находки.**

ADV-SIDECAR-SKIPPED-LINE-INCOMPLETE — `docs/sidecar.md:249` в том же переписанном абзаце называет вторую строку гейта как `WARN: leak-scan skipped`, тогда как `src/agentmarshal/journal/gate.py:1181` печатает `WARN: leak-scan skipped ({error})` — то есть причина пропуска, ради которой строку и читают, в документе не показана. Формулировка досталась в наследство от до-CR-100 текста, но абзац этим изменением переписан целиком, и критерий «описывает строку так, как её ожидает собственный тест гейта» для соседней строки выполнен лишь как подстрока.

ADV-TEMP-RETENTION-BACKLOG-ITEM-MISSING — `openspec/changes/archive/2026-09-18-bounded-leak-scan-output/design.md:17-19` утверждает, что политика удержания файлов во временном каталоге «is recorded as its own backlog item», и то же обещал ещё CR-100 (`openspec/changes/archive/2026-09-17-adopter-small-defects/design.md:58-59`). В `docs/proposals/` (001–023) и нигде в `openspec/` такого пункта нет — отложенное решение второй раз объявлено записанным, но не отслеживается. Завести его в этой задаче было нельзя: `docs/proposals/` вне scope.

Ни то, ни другое не мешает мержу: поведение, спека и тесты согласованы.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b72564daf990c9c8877e2ddcbb9901382839ac6c", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-SIDECAR-SKIPPED-LINE-INCOMPLETE", "ADV-TEMP-RETENTION-BACKLOG-ITEM-MISSING"]}
AGENTMARSHAL_VERDICT_END
