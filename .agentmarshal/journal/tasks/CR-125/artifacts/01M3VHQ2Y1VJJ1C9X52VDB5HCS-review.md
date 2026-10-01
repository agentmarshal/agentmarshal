Проверил снапшот: код-утверждения в дайджестах, кросс-ссылки, индекс, карту документации и диапазоны номеров/релизов.

**Что проверил по факту (всё сходится):**

- `032`: gate действительно сам вычисляет journal-only lane — `_JOURNAL_PREFIX = ".agentmarshal/journal/"`, `journal_only = all(...)` (`src/agentmarshal/journal/gate.py:649`), транскрипт строка в строку совпадает с `gate.py:740`, в sidecar lane принудительно выключается (`gate.py:652-658`), а scope/review-проверки живут в `else`-ветке (`gate.py:742+`) — то есть «пропускает их целиком» верно. Правка CR-124 сделана корректно.
- `037`: `review`'s `_run_git` читает git в text-режиме с `encoding="utf-8"` без `errors` (`journal/review.py:198-208`), а `UnicodeDecodeError` не перехватывается в `_run_review` (ловится только `ReviewLaunchError`, `cli.py:742`) — traceback и «not shipped yet» достоверны. Хелпер gate'а strict-декодит и деградирует в `WARN: leak-scan skipped` (`gate.py:241-257`, `gate.py:1146`) — «один root cause, две формы» подтверждается.
- `039`: `status` печатает `verdict= findings=N advisory=N` (`cli.py:548-551`), счётчика `changes_required` в проекте нет вообще, `finding` — research-запись (findings lane требует пустого scope), `brief` собирается из контракта, истории amendments, decisions и documents — findings среди входов нет. ADR-0010 реально проводит границу «manifest, not code we run».
- `040`: типов записей ровно девять (`records.py`), «started»/lease нет.
- `024`/`026`/`033`/`034`/`035`: header, Disposition, Where и строка индекса согласованы; batch-introduction финальный на четырнадцать файлов (027-040, 3 на 0.3.0 + 11 на 0.4.0), карта `docs/README.md` имеет строку на каждый новый дайджест, все упомянутые релизы (0.3.0/0.4.0/0.4.1) и номера proposals опубликованы, sha256 — 64 hex, уникальные.

Два замечания, не блокирующих:

Квалификатор диспозиции в `docs/proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md:3` (и в соответствующей строке индекса) говорит «accepted *(in part; ...)*», хотя в самом файле ни одна часть не отложена и не отклонена: fail-fast правило accepted, checkout-free write accepted, нужда в видимости accepted — не решён только механизм. По словарю индекса («the part we are not taking named in parentheses») «in part» здесь нечего обозначать, и в этом же корпусе 032 и 034 в такой же ситуации (нерешённый механизм при полностью принятых частях) носят просто «accepted».

Переформулировка `033` ломает согласие с `031`: `docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md:82` теперь говорит «the withdrawal is accepted» и даёт файлу диспозицию, а `docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md:103` по-прежнему утверждает «We record the withdrawal rather than a disposition». 031 вне scope этой задачи, так что исправить его здесь было нельзя — нужен follow-up или расширение scope.

Чего проверить не смог (ограничения среды, не находки): исходные файлы репортёра 022-025 и dispositions-документ координатора в снапшоте отсутствуют, поэтому дословность измерений, соответствие sha256 и совпадение диспозиций с документом не верифицируемы; выполнение команд в этой песочнице запрещено, так что `validate`/`pytest`/`ruff`/`mypy` я не запускал — изменение только документационное, и ни один тест не завязан на содержимое `docs/proposals/` или `docs/README.md` (единственная ссылка — `tests/test_project.py`, про корневой README).

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "3de8f919b7eeff0ae96a3bfa91029345051ace74", "verdict": "approved", "findings": [], "advisory_findings": ["040-disposition-in-part-qualifier-unsupported", "033-withdrawal-framing-contradicts-031"]}
AGENTMARSHAL_VERDICT_END
