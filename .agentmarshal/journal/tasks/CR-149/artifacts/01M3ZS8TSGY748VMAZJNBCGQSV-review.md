Разобрал контракт и диф, прочитал новый модуль, `status.py`, `records.py` и конфиг линтеров/CI. Запустить `pytest`/`ruff`/`mypy` в этой песочнице не дали (команды требуют подтверждения), поэтому проверку сделал чтением: сверил каждый ожидаемый в тесте байт с кодом, порядок записей, валидаторы, длины строк под `line-length = 88` и правила isort.

Что проверено по критериям:

1. **Пин вывода (критерий 1)** — `tests/test_status_view.py` импортирует только `agentmarshal.cli.main`, то есть проходит и на старом коде. Покрыты все семь типов с выделенной строкой (review ×2 — по коммиту и по finding, acceptance ×3 — finding/self-accepted/unchecked, completed, finding, abandoned, reopened, amendment) плюс `opened` и `session` на generic-строке. Проекция состояния для такой последовательности даёт `abandoned` — совпадает с пином. Записи валидны для `write_record`: id — 26 Crockford-символов, `accepted_commit = "a"*40` проходит `_validate_binding` и при этом `git show` на нём падает, что и даёт ветку «unchecked»; finding записан раньше ссылающихся на него review/acceptance.

2. **Перенос (критерий 2)** — `_print_task_detail`, `_is_self_accepted`, `_declared_commit_writers` целиком в `src/agentmarshal/journal/status_view.py`; один реестр `_RECORD_RENDERERS` по `record_type`, отсутствующий тип печатается generic-строкой. Циклов импорта нет (`status_view` → `status`, `status` не знает про `cli`).

3. **Байтовая идентичность (критерий 3)** — все f-строки совпадают посимвольно; три переформатированных в одну строку рендерера (`abandoned`, `reopened`, `amendment`) дают тот же текст. Разделение «посчитать строку → напечатать» не меняет порядок вывода, так как `subprocess.run` захватывает свой stdout. В `cli.py` остался только вызов; `cast` и `TaskStatus` из импортов убраны (а `subprocess` там ещё используется в другом месте — F401 не будет).

4. **Прочее (критерий 4)** — единственная внешняя привязка к перенесённому хелперу (`monkeypatch.setattr(cli_module, "_declared_commit_writers", …)` в `tests/test_acceptance.py`) обновлена; других ссылок на `_print_task_detail`/`_declared_commit_writers` в коде и доках нет. Длина самой длинной новой строки — ровно 88, порядок импортов соответствует isort, набор правил ruff (E/W/F/I/UP/B/SIM/RUF) ничего нового не ловит. CHANGELOG по конвенциям репозитория не требуется.

Advisory: докстринг нового теста `tests/test_status_view.py:3` написан в будущем времени — «The view is about to move from `agentmarshal.cli` to `agentmarshal.journal.status_view`», — хотя в этом же коммите перенос уже сделан; читатель смерженного дерева получит неверное описание текущего состояния.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c3b3c371053d4e209ba50dd77fdc8850ab2a96d3", "verdict": "approved", "findings": [], "advisory_findings": ["test-docstring-stale-tense"]}
AGENTMARSHAL_VERDICT_END
