Прошёлся по всем файлам scope, сверил каждый критерий приёмки с рабочим деревом, а не только с диффом.

Что подтвердилось:

- **CHANGELOG.md** — секция `## 0.4.1 — 2026-09-24` датирована днём релиза, три задачи с тега (CR-112, CR-113, CR-114) присутствуют, каждая названа в заголовке своего подраздела. Секция 0.4.0 не тронута, новых записей в ней нет. Запись про фикс говорит, что делает инсталляция, попавшая под отказ («this release reads it again» + ссылка на UPGRADING). Описание CR-114 сверено с `src/agentmarshal/journal/records.py:489-520` — категории `Cc/Cs/Zl/Zp` и bidi-контролы совпадают, единый предикат `forges_rendered_text` действительно один на записи и контракты. Заявление CR-112 сверено с `.github/workflows/release.yml:40-45` — отказ публиковать dev/local версию там есть. CR-113 сверено с `docs/proposals/README.md:81,108` и `docs/quickstart.md:445-451` — proposal 024 и 018 опубликованы, `provider-limit` задокументирован.
- **UPGRADING.md** — заголовок стал `## 0.4.0 → 0.4.1` в стиле остальных секций файла, и прямо сказано, что ничего, кроме установки, не требуется. Единственное поведенческое изменение действительно одно.
- **Версия** — `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11` и `tests/test_smoke.py:48` согласованы на 0.4.1; `--version` берёт `__version__` напрямую (`src/agentmarshal/cli.py:86-88`), так что печатает именно его. Запустить pytest в песочнице не дали (команда требует подтверждения), так что прогон CI я подтвердить не могу — только статическую согласованность.
- **Install-пины** — все команды, которые читатель может выполнить, называют 0.4.1: `README.md:77`, `docs/quickstart.md:26`, `docs/sidecar.md:75`. Больше пинов версии в репозитории нет (шаблон в `templates/github/` использует плейсхолдер `<VERSION>`).

Теперь замечания, все три — advisory.

В `CONTRIBUTING.md:123-126` пример версионирования после правки стал круговым: «carries the **next** release's version with a `.dev0` suffix — after 0.4.1 it reads the next release's version with that suffix» дословно повторяет само правило, так что вставка через тире больше ничего не иллюстрирует; заодно перенос строк сломан — строка «suffix — so anything built from it» обрывается на ~36 символах при принятой в файле ширине. Выбор не называть конкретный `0.5.0.dev0` понятен (следующая версия неизвестна, и критерий 4 запрещает называть неопубликованный релиз), но тогда оговорку честнее удалить целиком, а не превращать в тавтологию.

В `README.md:12,16,46,57,60` и `docs/quickstart.md:198,207,363` утверждения о возможностях по-прежнему привязаны к 0.4.0 («Version 0.4.0 ships the governed loop end to end», «remain inactive in 0.4.0», «in 0.4.0 a match does not fail the gate»), хотя README — это описание пакета, которое PyPI покажет для 0.4.1, и quickstart теперь заявляет, что описывает 0.4.1. Фактически эти фразы не ложны (поведение не менялось), и критерий 4 запрещает трогать высказывания о 0.4.0 как об истории, поэтому это не блокер — но страница, которая пинит 0.4.1 и тут же называет 0.4.0 поставляемой версией, читается противоречиво.

В `docs/quickstart.md:6` эмпирическое утверждение «was run against a wheel of `agentmarshal` 0.4.1 built before the release was published» изменено подстановкой номера; в снапшоте нет ничего, чем это подтвердить (в журнале у CR-115 только `opened` и `amendment`). Критерий приёмки требует, чтобы фраза оставалась истинной для названного wheel, поэтому прогон quickstart против сборки 0.4.1 стоит отразить в completion-отчёте рядом с read-only `validate` по журналу адоптера.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "32cb9b041d4b07e8d58fc9b326c38361f3c01504", "verdict": "approved", "findings": [], "advisory_findings": ["contributing-versioning-example-now-tautological", "readme-quickstart-capability-statements-still-name-0-4-0", "quickstart-wheel-claim-not-evidenced"]}
AGENTMARSHAL_VERDICT_END
