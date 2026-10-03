Полный прогон CI в этой песочнице заблокирован (любой `uv run`/`python3 -c` требует approval), поэтому пятый критерий — «the full CI sequence passes» — я проверить исполнением не смог; ревью статическое. Контрактную часть проверил сопоставлением файлов: заголовок MODIFIED-требования в дельте совпадает с живым спеком побайтно, блок ADDED лёг в `openspec/specs/process-log/spec.md` дословно, `openspec/changes/` содержит только `archive/` — архивация выглядит выполненной командой. Все 12 сценариев дельты закрыты тестами, чьи docstring их называют.

Нашёл два места, где исключение уходит наружу трейсбеком, хотя design.md в разделе Goals обещает обратное («Every failure reaches the caller as a named error, never a traceback»), а `cli.main` catch-all не имеет.

**step-start-proc-read-crashes-on-non-ascii-comm** — `src/agentmarshal/steps.py:253`: `/proc/<pid>/stat` читается с `encoding="ascii"` и строгим `errors`, а `except OSError` на строке 254 ловит только ввод/вывод. Поле `comm` в этом файле — сырые до 15 байт имени процесса, ядро экранирует там лишь пробелы и обратный слэш, не не-ASCII. Процесс с именем вроде `тест` (`prctl(PR_SET_NAME)` или exec бинаря с UTF-8 именем) даёт `UnicodeDecodeError` — не подкласс `OSError` — и `step start` падает трейсбеком. Это основной путь, а не экзотика: по умолчанию `pid` — это `os.getppid()`, то есть сам harness. Спек требует «the command SHALL work either way», а design.md прямо перечисляет «a dead or unreadable pid, output that does not parse» как случаи, дающие `unknown`. Остальной репозиторий эту ошибку ловит последовательно — больше двадцати сайтов (`project.py:105`, `review.py:1060`, `status_view.py:40` и т. д.); новый модуль из этой конвенции выпал. Тот же перекос у `_boot_time` на `steps.py:280`.

**step-start-deadline-overflow-traceback** — `src/agentmarshal/steps.py:212` и `src/agentmarshal/steps.py:225`: `_parse_deadline` ловит только `ValueError`, а `try` в `_run_start` (`steps.py:132`) — только `(JournalRecordError, StepError)`. `--deadline 999999999999d` упирается в `timedelta(seconds=...)`, который при нормализации больше 999999999 дней бросает `OverflowError`; `--deadline 9999-12-31T23:59:59-12:00` проходит `fromisoformat`, но `astimezone(UTC)` переносит дату за `datetime.max` и тоже бросает `OverflowError`. Ни то, ни другое не `ValueError`, так что оба значения `--deadline`, полностью подконтрольные вызывающему, печатают трейсбек вместо названной ошибки.

Ещё два замечания, не блокирующих.

**step-id-and-actor-unvalidated** — `src/agentmarshal/steps.py:91`, `85`, `86`: `--outcome` защищён `forges_rendered_text` (`steps.py:198`) именно потому, что design.md пишет: «`status` and `doctor` will print an outcome inline». Но `--step`, `--actor` и `--run-dir` попадают в лог без всякой проверки, а их `status`/`doctor` будут рендерить рядом тем же образом — тест `tests/test_steps.py:325` сам фиксирует, что `--step 01ABC` проходит, и `--step ""` тоже пройдёт. В журнале `actor` и идентификаторы проходят `_reject_control_characters` (`records.py:682` и далее). Сам JSON не рвётся — `json.dumps` экранирует перевод строки, — и чтение событий отложено в следующую задачу, поэтому это не блокирует; но дырка в той же модели угроз, которую change принимает явно.

**step-end-stdout-unspecified** — `src/agentmarshal/steps.py:184`: `step end` печатает step id на stdout. Спек задаёт stdout только для `step start` («SHALL ... print the new step id on stdout») и о `end` молчит, а тест `tests/test_steps.py:277` это поведение закрепляет. Либо поведение стоит внести в требование, либо убрать.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9ab3127d0b36a771bc59c01537aef22f6d11f66b",
  "verdict": "changes_required",
  "findings": [
    "step-start-proc-read-crashes-on-non-ascii-comm",
    "step-start-deadline-overflow-traceback"
  ],
  "advisory_findings": [
    "step-id-and-actor-unvalidated",
    "step-end-stdout-unspecified"
  ]
}
AGENTMARSHAL_VERDICT_END
