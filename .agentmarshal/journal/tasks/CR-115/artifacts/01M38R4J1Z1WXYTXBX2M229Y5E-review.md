Провёл сверку диффа с контрактом CR-115 по всем пяти критериям.

**Что проверено и сходится:**

- Версия `0.4.1` согласована в `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11`, а `--version` берёт её из `__version__` (`src/agentmarshal/cli.py:88`), что пинит `tests/test_smoke.py:48,59`.
- CHANGELOG 0.4.1 датирован днём релиза, все три задачи (CR-114, CR-112, CR-113) названы, запись о фиксе говорит, что делает установка, поймавшая отказ («this release reads it again» + ссылка на UPGRADING).
- Описание правила в CHANGELOG/UPGRADING (`Cc`, `Cs`, `Zl`, `Zp` + bidi marks/embeddings/overrides/isolates, один предикат на три места) совпадает с `src/agentmarshal/journal/records.py:499-524` и вызовами в `contracts.py:64`, `validate.py:72`.
- UPGRADING озаглавлен `## 0.4.0 → 0.4.1` и прямо говорит, что ничего больше действий не требует; секции 0.3.0 → 0.4.0 и ниже не тронуты.
- Полный sweep по репозиторию: все оставшиеся упоминания `0.4.0` вне журнала — исторические (UPGRADING, строки индекса proposals 014–023, ADR-0009, proposal 024 о трёх схемах, комментарий в `records.py`). Незакрытых install-пинов `0.4.0` не осталось (`README.md:79`, `docs/quickstart.md:26`, `docs/sidecar.md:75,125`). Тесты на опубликованный 0.3.0 (`tests/test_gate.py`) не задеты.
- Non-goal соблюдён: `.dev0` на ветке не восстановлен, публикации нет.

**Замечание (не блокирующее):** `CONTRIBUTING.md:126-127` — фраза «0.4.1 was published from a branch carrying `0.5.0.dev0`» стоит в прошедшем времени о релизе, который оператор ещё не опубликовал (это явный non-goal задачи), и при буквальном чтении спорит со следующим же предложением: задача подготовки релиза заменяет версию ветки до тега, так что в момент публикации ветка несёт `0.4.1`, а не `0.5.0.dev0`. Смысл примера верен, но формулировка — единственное место в диффе, где документ утверждает свершившийся факт публикации.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "11f369757322cd792364b6e030dd75f30cd2461b", "verdict": "approved", "findings": [], "advisory_findings": ["contributing-names-publication-as-past-fact"]}
AGENTMARSHAL_VERDICT_END
