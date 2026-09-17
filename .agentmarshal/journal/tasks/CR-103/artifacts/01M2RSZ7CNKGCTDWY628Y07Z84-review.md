Проверил diff против контракта, ADR-0005, published spec и кода в снапшоте.

**Что сошлось.** Все восемь сценариев MODIFIED-требования в `openspec/changes/archive/2026-09-18-bounded-leak-scan-output/specs/leak-scan/spec.md` закрыты тестами, чьи docstring их называют: пять старых (`tests/test_capture.py:242,337,355,376,489`), `tests/test_gate.py:1779` и два новых — `tests/test_gate.py:1809` и `tests/test_leak_scan.py:66`. Delta-спека дословно применена в `openspec/specs/leak-scan/spec.md`, архив собран по конвенции соседних изменений (`.openspec.yaml` + `design.md` + `proposal.md` + `specs/` + `tasks.md`, все задачи `[x]`).

Решения design.md выполнены: `render_leak_hits` (`src/agentmarshal/journal/capture.py:324`) берёт `limit` параметром, `_run_leak_scan` (`src/agentmarshal/cli.py:1309`) передаёт `None`, gate — свою константу `20` (`src/agentmarshal/journal/gate.py:1182`); счётчик остался частью той же строки, а не второй строкой. Рендерер по-прежнему один — grep по всему репозиторию даёт ровно два call site, и ни один из них не воспроизводит форму хита у себя. `remaining = len(hits) - len(shown)` вместо прежнего `len(hits) - _RENDER_LIMIT` — арифметика теперь не может уйти в минус. `LeakHit` — `order=True` dataclass, `scan_diff_for_leaks` возвращает `sorted(hits)`, так что порядок в обоих новых тестах детерминирован по пути: `src/secret00.py` попадает в срез, `src/secret20.py` — нет, остаток ровно 1. `LaunchedReview` добавлен и в импорт, и в `__all__` (сортировка `__all__` сохранена), строка импорта в `__init__.py:25` — ровно 88 символов, в line-length ruff укладывается. Формулировка в `docs/sidecar.md:247-248` совпадает с тем, что пинит `tests/test_gate.py:1796`. Все затронутые пути — внутри scope.

Оговорка: выполнить тесты я не смог — запуск python в этой песочнице требует одобрения, так что прохождение suite обосновано статически, а не прогоном.

Ниже — три необязательных замечания, ни одно не блокирует.

**sidecar-omits-the-bound** — `docs/sidecar.md:247-249` описывает предупреждение gate как `WARN: possible leak in candidate additions (advisory, not blocking): <file>: <what matched>` и молчит о том, что строка ограничена и добирает `, and N more not shown`. Именно это изменение опубликовало ограничение в `openspec/specs/leak-scan/spec.md` («MAY bound how many it shows, and SHALL say how many it did not»), а sidecar.md — единственный операторский документ, описывающий эту строку транскрипта; читатель не узнает из него, что хиты могут быть скрыты.

**bound-rationale-lost-in-the-move** — `src/agentmarshal/journal/gate.py:57`: константа `_LEAK_HIT_RENDER_LIMIT = 20` переехала без объяснения числа. Комментарий, который в `capture.py` обосновывал границу («A marker present in two hundred files used to render as one category token…»), удалён, а новый комментарий над `render_leak_hits` объясняет только, что выбор принадлежит caller'у. Довод «почему именно двадцать» теперь живёт лишь в архивном design.md — для репозитория, где почти каждая константа несёт своё «зачем», это шаг назад.

**redundant-f-prefix-in-gate-warning** — `src/agentmarshal/journal/gate.py:1181`: сегмент `f"(advisory, not blocking): "` не содержит ни одной подстановки. Из-за неявной конкатенации с соседним f-string'ом ruff F541 не сработает, но префикс тут лишний — это должна быть обычная строковая литеральная часть.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "09ae82d2bc58ba71eec6fbb57037eb215f232f9f", "verdict": "approved", "findings": [], "advisory_findings": ["sidecar-omits-the-bound", "bound-rationale-lost-in-the-move", "redundant-f-prefix-in-gate-warning"]}
AGENTMARSHAL_VERDICT_END
