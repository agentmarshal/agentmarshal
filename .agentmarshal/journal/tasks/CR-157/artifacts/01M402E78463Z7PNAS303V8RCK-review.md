Прочитал контракт, дельту спеки, `steps.py`, `process_log.py` и тесты; сверил с ADR-0022 §4/§7 и `openspec/specs/process-log/spec.md`. Прогнать CI (`pytest`/`ruff`/`mypy`) здесь не получилось — sandbox отказал в запуске python, поэтому «the full CI sequence passes» я проверил только статически (длина строк ≤ 88, аннотации под `mypy --strict`, импорт `_SESSION_ACTIVITIES` — уже принятый в репо паттерн), не исполнением.

Что в порядке: архив `2026-10-03-step-commands` лежит с proposal/design/tasks/дельтой, MODIFIED-заголовок requirement'а совпадает с текущим посимвольно, все 10 ADDED-сценариев и оба новых MODIFIED-сценария имеют тест с докстрингом, который их называет; `openspec/changes/` пуст — change заархивирован, Purpose спеки не тронут. `cli.py` получил ровно хук (две строки). `_writer_for` идёт через `find_project_root` → `resolve_placement` (без `require_host`) → `local_state`, то есть sidecar пишет свой лог — это подтверждено тестом. Валидация задачи и outcome выполняется до открытия writer'а, так что при отказе событие не ложится. Разбор поля 22 `/proc/<pid>/stat` через `rfind(")")` корректен, и `_elapsed_seconds` правильно читает `[[dd-]hh:]mm:ss`. Открытая словарность outcome согласована с ADR-0022 §4 («accepts any non-empty string»), так что расхождения с ADR тут нет.

Теперь то, что нужно поправить.

**step-start-traceback-on-non-ascii-comm** — `src/agentmarshal/steps.py:252-255`: `/proc/<pid>/stat` читается с `encoding="ascii"`, а `except` ловит только `OSError`; имя процесса (`comm`) — произвольные байты, поэтому для процесса с не-ASCII именем чтение падает `UnicodeDecodeError` (это `ValueError`, не `OSError`), исключение уходит наружу из `pid_started_at` и `_run_start` и команда завершается трейсбеком вместо `pid_started_at: "unknown"` — прямое нарушение критерия 3 («where it cannot, the field says so rather than guessing, and the command still works»).

**deadline-overflow-traceback** — `src/agentmarshal/steps.py:210-225`: `_DURATION` принимает неограниченное `\d+`, и на большом значении `timedelta(...)`/сложение с `datetime.now(UTC)` бросает `OverflowError`, который не ловит ни локальный `except ValueError`, ни `except (JournalRecordError, StepError)` в `_run_start`; та же дыра на ISO-ветке при `.astimezone(UTC)`. То есть `step start --deadline 999999999d` или `--deadline 9999-12-31T23:59:59-12:00` даёт трейсбек вместо отказа «neither an ISO-8601 time nor a duration».

**ps-fallback-untested** — `src/agentmarshal/steps.py:292-326`: портативный fallback (`_ps_started_at` и парсер `_elapsed_seconds`) не покрыт ни одним тестом — единственный тест `pid_started_at` на Linux идёт только по ветке `/proc`, так что нетривиальный разбор `etime` держится на глаз; плюс `subprocess.run` без `timeout` может подвесить команду на зависшем `ps`.

**unvalidated-rendered-fields** — `src/agentmarshal/steps.py:91, 85-86`: `--step`, `--actor` и `--run-dir` принимают любой текст, тогда как `--outcome` проверяется `forges_rendered_text`; обоснование из design.md («`status` и `doctor` будут печатать это inline») одинаково применимо ко всем четырём, и сейчас подделываемый текст спокойно попадает в лог.

**step-end-undocumented-stdout** — `src/agentmarshal/steps.py:184`: `step end` печатает step id в stdout, и тест это закрепляет (`tests/test_steps.py:294`), но ни дельта-спека, ни design.md такого вывода не описывают — поведение зафиксировано только тестом.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9ab3127d0b36a771bc59c01537aef22f6d11f66b",
  "verdict": "changes_required",
  "findings": ["step-start-traceback-on-non-ascii-comm", "deadline-overflow-traceback"],
  "advisory_findings": ["ps-fallback-untested", "unvalidated-rendered-fields", "step-end-undocumented-stdout"]
}
AGENTMARSHAL_VERDICT_END
