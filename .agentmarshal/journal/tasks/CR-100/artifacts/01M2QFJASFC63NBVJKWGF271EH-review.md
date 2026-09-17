Прошёлся по диффу, контракту, обоим ADR и файлам спеки в снапшоте. Ниже — что нашёл.

**F-001** — `src/agentmarshal/cli.py:1287`: standalone-команда вызывает `scan_diff_for_leaks(diff_text, markers)` с дефолтным `config_path=".agentmarshal/project.json"`, тогда как gate на соседнем call site (`src/agentmarshal/journal/gate.py:1137-1138`) сознательно передаёт `""` для sidecar. В sidecar-размещении markers читаются из конфига оператора (`sidecar_config`, `cli.py:1236`), а дифф — хостовый; хост при этом вполне может нести собственный embedded journal (ADR-0008, §«A sidecar journal references its host freely… where the host carries an embedded journal»). Тогда добавленный в хостовый `.agentmarshal/project.json` маркер — не декларация этого маркера, а настоящая утечка — глушится как self-match. Это ровно тот дрейф, который запрещает acceptance-критерий 3 («the two cannot drift»), и выход за границу сужения, заявленную в контракте («only an occurrence inside the configuration that declares the marker is ignored») и в `design.md` («Self-match is decided by where the marker occurs»). `sidecar_config` в этой функции уже в области видимости — правка на одну строку.

**F-002** — `tests/test_placement.py:286` изменён, но этого файла нет в `scope` контракта CR-100 (в `.agentmarshal/journal/tasks/CR-100/contract.md:5-19` перечислены только `test_capture.py`, `test_gate.py`, `test_review_launcher.py`, `test_project.py`), и в `records/` лежит один `opened` — ни одной amendment, расширяющей scope. Правка сама по себе вынужденная (строка ассертит старый текст сообщения), но её место — в поправке к контракту, а не молча в диффе.

**F-003** — `openspec/specs/leak-scan/spec.md` не является результатом применения дельты. В `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/leak-scan/spec.md:8-9` есть предложение «A path that itself contains a configured marker SHALL NOT be printed either…» и сценарий `a path that carries a marker is described, not printed` (строка 22) — в built-спеку не доехали ни то, ни другое (там 5 сценариев вместо 6). В итоге поведение `safe_path` (`src/agentmarshal/journal/capture.py:298`) реализовано и покрыто тестом, но не управляется ничем в действующей capability-спеке.

**F-004** — `tests/test_capture.py:331`: `test_a_path_that_carries_a_marker_is_not_printed_either` демонстрирует сценарий «a path that carries a marker is described, not printed», но его docstring сценарий не называет — в отличие от остальных семи, начинающихся с `Scenario: …`. Acceptance-критерий 1 требует буквально «a test whose docstring names it».

Advisory:

**A-001** — `src/agentmarshal/journal/review.py:327-337`: `_keep_diagnostics` на *успешном* пути превращает `OSError` в `ReviewLaunchError`, то есть полностью выбрасывает уже отработавший (и оплаченный) прогон ревьюера из-за того, что не записался временный файл. Комментарий на той же строке говорит «preservation is best effort», а соседний `_reject` (`review.py:355-359`) в такой ситуации деградирует до сообщения. Поведение и заявленный контракт функции расходятся.

**A-002** — `src/agentmarshal/journal/capture.py:298-304`: `safe_path` прячет из пути только private markers. Путь, который сам матчится встроенной сигнатурой (файл, названный ключом — такую форму конструирует `tests/test_capture.py:262`), печатается как есть, так что настоящий секрет из имени файла уедет в CI-лог. Формально вне текста дельты, но это тот же класс раскрытия, ради которого изменение затевалось.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9681bb563e63894f7c37ad447766c500496e62da", "verdict": "changes_required", "findings": ["F-001", "F-002", "F-003", "F-004"], "advisory_findings": ["A-001", "A-002"]}
AGENTMARSHAL_VERDICT_END
