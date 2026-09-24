Проверил diff против контракта CR-115 и против того, что реально лежит в репозитории.

**Что сошлось.** Версия 0.4.1 стоит во всех трёх местах (`pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, запись `agentmarshal` в `uv.lock`), других вхождений `0.5.0.dev0` в локе не осталось; `--version` печатает именно `__version__` (`src/agentmarshal/cli.py:86-88`), и `tests/test_smoke.py:48` обновлён. Секция `## 0.4.1 — 2026-09-24` датирована днём релиза, CR-112/CR-113/CR-114 все три названы, секция 0.4.0 не тронута. Заявления в записи про CR-114 сверил с кодом: `_FORGEABLE_CATEGORIES = {"Cc","Cs","Zl","Zp"}` плюс bidi-набор в `src/agentmarshal/journal/records.py:498-509`, и предикат `forges_rendered_text` действительно один на три места — записи (`records.py`), заголовки контрактов (`contracts.py:64`) и artifact ref в `validate.py:72`. Запись про CR-112 сходится с `.github/workflows/release.yml:40-45` и CONTRIBUTING, запись про CR-113 — с `docs/proposals/024-…md` и `docs/quickstart.md:444-451`. Заголовок в UPGRADING приведён к формату остальных секций и говорит, что кроме установки ничего делать не надо.

Критерий 5 (полный прогон CI и read-only `validate` по журналу адоптера) проверить не смог: в песочнице ревью нет ни `uv`, ни `git`, а отчёт о прогоне попадает в completion-запись, которой в diff ещё нет. Затронутые тесты и линтеры от изменений в документации не зависят, версионный assert совпадает; тестов, читающих CHANGELOG/UPGRADING, в `tests/` нет.

Ниже — необязательные замечания, ничего из них не блокирует релиз.

`changelog-refused-write-sentence`: в `CHANGELOG.md:28-29` фраза «The verdict a refused write produced is unaffected: a refused write wrote nothing» говорит о вердикте, которого отклонённая запись не производила — в `UPGRADING.md:39` та же мысль сформулирована корректно («Records written on 0.4.0 are unaffected»); правка на одну строку, файл в scope.

`upgrading-ragged-rewrap`: в `UPGRADING.md:11-13` правка оставила посреди абзаца короткую строку «upgrade to 0.4.1; it reads that record again.** The», тогда как весь остальной файл набран до ~79 колонок.

`published-docs-still-pin-0.4.0`: `README.md:77`, `docs/quickstart.md:26` и `docs/sidecar.md:75` продолжают советовать `pip install agentmarshal==0.4.0`, а `docs/proposals/README.md:81` указывает для 024 «default branch» вместо релиза, хотя CONTRIBUTING:65 требует от принятого proposal называть, куда он ушёл. Всё это вне scope CR-115 (gate такие файлы не пропустит), но после публикации README отправляет нового адоптера ровно в тот релиз, из которого UPGRADING велит уходить — стоит отдельной задачей до анонса.

`contributing-dev-version-claim`: `CONTRIBUTING.md:123-126` утверждает, что сборка с default-ветки «sorts after the last release, before the next one»; ветка несла `0.5.0.dev0`, а релиз вышел `0.4.1`, так что для этого релиза правило не выполнилось. Тоже вне scope — логичное место для правки в той задаче после тега, которая возвращает `.dev0`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "a0496d896f730b8430dd0edbc2e06de87f2884fc",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "changelog-refused-write-sentence",
    "upgrading-ragged-rewrap",
    "published-docs-still-pin-0.4.0",
    "contributing-dev-version-claim"
  ]
}
AGENTMARSHAL_VERDICT_END
