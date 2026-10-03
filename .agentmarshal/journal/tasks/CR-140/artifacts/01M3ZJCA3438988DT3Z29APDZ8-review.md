Проверил ADR-0020 против контракта и против файлов, на которые он опирается.

**Что сошлось:**
- `_scaffold_outbox` (`src/agentmarshal/project.py:296`) действительно создаёт `.agentmarshal/upstream/` и пишет README; best-effort и «существующий README не перезаписывается» — точно по коду (`mkdir(exist_ok=True)`, открытие на `"x"` с `FileExistsError` → успех). Pathspec `git add .agentmarshal ':(exclude).agentmarshal/upstream/**'` цитируется дословно из `_OUTBOX_README`.
- Пять полей (Symptom, Measurements, Version, Environment, Expected) живут в `CONTRIBUTING.md:31` «Reporting a finding», в outbox README их нет — как и сказано.
- `agentmarshal finding` — research-finding команда с `--task`/`--summary`/`--artifact`, `--task` обязателен (`src/agentmarshal/cli.py:300-311`).
- Измерения proposal 023 (9 findings, 8 в 3 коммитах, 0 из 8 в коммите про findings) и 029 (Environment полностью в 1 из 13, Version в 13 из 13) воспроизведены верно; `Source:`-линия и батч 2026-09-16 совпадают с `docs/proposals/README.md` и outbox README.
- Форма совпадает с ADR-0012..0018: Status/Date, параграф «Builds on», дисклеймер «не реализуется этим документом» (дословно по образцу ADR-0009), Context / Decision / Consequences / Alternatives considered. Все ссылки на ADR и proposals ведут в существующие файлы, proposals названы «proposal NNN» и слинкованы, приватных документов, адоптеров, клиентов и неопубликованных релизов нет. Номер 0020 корректен: 0019 занят параллельной задачей CR-139.
- CI-последовательность (`uv sync`/`validate`/`pytest`/`ruff`/`mypy`) на markdown-файл не реагирует: ни один тест не читает реальные `docs/adr/*`. Запустить тулинг в этой песочнице нельзя (нет разрешения и нет git-репозитория), так что это вывод из конфигурации и тестов, а не наблюдённый прогон.

Ниже — три необязательных замечания.

Список на строке 46 введён словами «Two proposals measured what that costs:», но содержит три пункта — третий (proposal 012) не измерение; читатель, считающий пункты, спотыкается.

Строки 110–111 утверждают, что outbox — «the one directory under `.agentmarshal/` that does not record the adopter's own work»; по карте мест в ADR-0014:142 рядом лежит `.agentmarshal/extensions/` (реализован, см. `src/agentmarshal/journal/extensions.py`), который тоже не является записью о работе адоптера и не является append-only/task-scoped/gated. В proposal 023 это утверждение было верным на 0.3.0, до extensions; в обобщении на `.agentmarshal/` оно стало спорным.

Решения 3 и 5 (строки 83 и 100) говорят «for each draft» и «each file in the outbox», но в outbox лежит написанный `init` README.md, который не является draft'ом и не имеет `Source:`-линии: по букве решения `check` назовёт его несоответствующим, а `status` — файлом, который никто не заявляет. Правка требует решения оператора (контракт запрещает добавлять пункты), поэтому — advisory.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "82a1dd92fe064d6562cfe212cdcccfcaaf6fcc0a",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "two-proposals-introduces-three-item-list",
    "outbox-not-the-only-non-record-directory-under-agentmarshal",
    "init-written-readme-unaddressed-by-check-and-status"
  ]
}
AGENTMARSHAL_VERDICT_END
