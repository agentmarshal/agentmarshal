Прочитал исходники и тесты на месте; тесты и CI-последовательность здесь запустить нельзя (нет venv/uv, каталог не git-репозиторий), по CI опираюсь на заметку координатора.

**Находка (advisory, не блокирует)**

`ADV-1-dropped-pause-line-assertion` — в `tests/test_stages.py` из существующего спек-теста `test_a_journal_that_cannot_be_read_names_it_and_every_pause_stands` молча удалена последняя проверка `assert "paused before the gate" in captured.err` (диффом, последняя строка файла перед новым тестом); контракт такой правки не просит ни одним критерием, и это ослабляет именно ту половину сценария, которую он называет («every pause stands» — видимая pause-строка на stderr). Не блокер: в тесте остался `assert _stage_run(...) == 3`, а статус 3 возвращается только при стоящей паузе (`src/agentmarshal/stages.py:1190`), и сама строка закреплена ещё пятью тестами (`tests/test_stages.py:1420,1435,1674,1695,1736`, `tests/test_switches.py:410`).

**По критериям приёмки — где дифф их выполняет**

1. **CR-223 ADV-2/3/4.** Выполнен. ADV-2: абсолютный путь в E2E-пробе берётся из `os.environ["AGENTMARSHAL_SNAPSHOT"]` (`tests/test_isolation.py:562-564`), который `_stage_env` отдаёт стадии независимо от cwd (`src/agentmarshal/stages.py:511`, cwd ставится отдельно на `stages.py:627`). ADV-3: skip теперь по одному read-only floor с причиной probe (`tests/test_isolation.py:517-523`), а проверки записи стали безусловными (`tests/test_isolation.py:578-580`) — вместо прежней ветки, которая их просто роняла. Оба демонстрирует `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate` (`WRITE:blocked` + `ABSWRITE:blocked`). ADV-4: комментарий над маппингом флагов называет `sys/statvfs.h` (`src/agentmarshal/isolation.py:72`) — чисто текстовое требование, выполнено; сами заголовки на этой машине прочитать нельзя (sandbox не даёт `/usr/include`), но находки по этому поводу я не выношу.
2. **CR-224: ленивое чтение журнала закреплено тестом.** Выполнен: `test_a_run_that_pauses_nothing_never_reads_the_journal` (`tests/test_stages.py:1961-2001`) ставит spy на `stages_module.read_records` в том же стиле, что и соседний escape-тест, прогоняет `pre-gate` с одной `checked`-стадией и одной падающей `pre-gate-warn` и утверждает `calls == []`; это действительно пинит лень — call-site `read_records` вызывается только из `accepted_pause` (`src/agentmarshal/stages.py:1056`), которая зовётся лишь для `pre-gate-stop` с решением не `checked`/`switched-off` (`stages.py:1137-1143`), так что при эагерном чтении тест упал бы.
3. **CR-225 F2/F3/F4.** Выполнен. F2: `validate_task_id` вернулся в обёртку перед `_resolve` (`src/agentmarshal/stages.py:1204-1212`), т.е. восстановлен доCR-225-порядок отказов, на который и жаловалась F2 («вместо прежнего отказа по task id», `.agentmarshal/journal/tasks/CR-225/artifacts/01M5PT3FS64X65DPM1XYH77YTH-review.md:15`); пинит `test_a_bad_task_id_is_refused_before_the_project_check` (`tests/test_stages.py:400-422`) — обе ноги: плохой id вне проекта даёт `stage run: task id …` без упоминания проекта, валидный id вне проекта даёт прежнее «must be run inside an initialized project» (`stages.py:269`). Оговорка к формулировке критерия: буквальное чтение «prints the message it printed before CR-225 **before any task-id validation**» означало бы обратный порядок (сначала сообщение о проекте), но критерий прямо ссылается на CR-225 F2, а F2 требует именно отказа по id первым — разрешаю двусмысленность в пользу названной находки, и диффу это соответствует; `--phase` ограничен `choices` (`stages.py:239`), так что порядок с проверкой фазы не поехал. F3: пост-gate-прогон обёрнут в `try/except Exception` с одной строкой на stderr и `return 0` (`src/agentmarshal/cli.py:1199-1221`); форсирует `test_a_post_gate_run_that_raises_leaves_the_completion_untouched` (`tests/test_complete_stages.py:690-722`), который подменяет ровно тот `tempfile.TemporaryDirectory`, что F3 назвала незащищённым (`stages.py:1111`), и проверяет `exit 0`, единственную строку stderr и последнюю запись `completed`; тест корректен именно потому, что журнальные записи идут через `mkstemp`/`mkdtemp`, а не через `TemporaryDirectory` (`journal`-пути: `process_log.py:183`, `open_task.py:388`), поэтому подмена не ломает саму запись. F4: `test_both_commands_go_through_the_one_runner` теперь прогоняет под spy и `stage run`, и `complete`, фиксируя тройку `[("pre-gate", False), ("pre-gate", True), ("post-gate", True)]`, т.е. заодно и `quiet`-воицинг.
4. **Без изменения требований и прочего поведения.** Выполнен: `openspec/changes/` содержит только `archive/`, спеки не тронуты, журнал не тронут, все файлы диффа внутри scope (`stages.py`, `isolation.py`, `cli.py`, `tests/`); новые тесты помечены «Not a spec scenario» по уже принятой в репозитории конвенции. Поведенчески добавились только два мандата контракта (порядок отказа `stage run` и одна строка stderr при упавшем post-gate), `except Exception` не конфликтует с ruff-конфигом (`BLE` не включён, `pyproject.toml:52-62`). CI не запускал — беру из заметки координатора.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "813f12797a542b9f850eb3fb2483279c3c1011fb",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1-dropped-pause-line-assertion"],
  "classes": {
    "ADV-1-dropped-pause-line-assertion": "test-gap"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn 'AGENTMARSHAL_SNAPSHOT' src/ tests/ openspec/", "result": "src/agentmarshal/stages.py:511 exports it in _stage_env; tests/test_isolation.py:563 is the new independent absolute path; spec openspec/specs/extension-stages/spec.md:178,197"},
      {"what": "grep -rn 'paused before the gate' tests/ src/", "result": "tests/test_stages.py:1420,1435,1674,1695,1736; tests/test_switches.py:410; tests/test_complete_stages.py:141; src/agentmarshal/stages.py:1224 — the deleted assertion's text stays covered elsewhere"},
      {"what": "grep -rn 'TemporaryDirectory|mkstemp|mkdtemp' src/agentmarshal/", "result": "stages.py:1111 and isolation.py:530 are the only TemporaryDirectory uses; journal writes use mkstemp/mkdtemp, so the test's patch cannot block the completed record"},
      {"what": "grep -rn '\"--phase\"' -A 6 src/agentmarshal/", "result": "stages.py:237-242 — choices=('pre-gate','post-gate'), so argparse refuses an unknown phase before the new task-id check"},
      {"what": "ls openspec/changes; grep -rc 'Not a spec scenario' tests/*.py", "result": "only archive/; the docstring convention pre-exists in tests/test_stages.py, test_doctor_extensions.py, test_doctor_wrapper_runtime.py"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "no .venv and no uv in this sandbox, interpreters/package tools are not runnable here; CI status taken from the coordinator's note for this commit"},
      {"what": "git diff/log against the parent commit", "why": "the snapshot is not a git repository"},
      {"what": "grep ST_RELATIME over /usr/include to confirm ADV-4's header attribution", "why": "the sandbox refuses reads outside the snapshot; the criterion itself is textual and is met"}
    ],
    "read": [
      "src/agentmarshal/cli.py:1086-1222 (_run_complete, the new post-gate try/except)",
      "src/agentmarshal/stages.py:230-300 (parser, _resolve), 470-660 (_stage_env, _run_stage), 758-860 (run_stages head), 1020-1227 (lazy acceptance read, loop, _run_stages)",
      "src/agentmarshal/isolation.py:55-90, 300-320 (statvfs comment, readonly setup chdir)",
      "src/agentmarshal/journal/records.py:331-336 (validate_task_id message carries no user input)",
      "tests/test_stages.py:1-140 (helpers), 376-422, 1929-2001",
      "tests/test_complete_stages.py:1-185, 685-722",
      "tests/test_isolation.py:495-595",
      "openspec/specs/extension-stages/spec.md (searched for refusal-order and byte-for-byte clauses)",
      ".agentmarshal/journal/tasks/CR-225/records/*review.json and artifacts/01M5PT3FS64X65DPM1XYH77YTH-review.md (F2/F3/F4 wording)",
      ".agentmarshal/journal/tasks/CR-223/artifacts/01M5PKPDXN1GW6S57H7SZ9Z40E-review.md (ADV-2/3/4), CR-224 artifact (lazy-read-untested)",
      "pyproject.toml (ruff/mypy configuration)"
    ]
  },
  "evidence": {
    "ADV-1-dropped-pause-line-assertion": "diff tests/test_stages.py: '-    assert \"paused before the gate\" in captured.err' removed from test_a_journal_that_cannot_be_read_names_it_and_every_pause_stands (file now ends that test at tests/test_stages.py:1958 with the journal-line assertions only); nothing in the CR-227 contract asks for it. Residual coverage: the same test still asserts `_stage_run(...) == 3` (src/agentmarshal/stages.py:1190 returns 3 only when a pause stands) and grep -rn 'paused before the gate' tests/ lists tests/test_stages.py:1420,1435,1674,1695,1736 and tests/test_switches.py:410."
  }
}
AGENTMARSHAL_VERDICT_END
