Прочитал diff и затронутый код на месте; тесты и CI-последовательность здесь запустить нельзя (нет `.git`, нет venv, исполнение python в песочнице запрещено), поэтому по прохождению проверок опираюсь на заметку координатора.

**По критериям приёмки — где дифф их выполняет**

1. **Критерий 1 (CR-223 ADV-2/3/4) — выполнен.** Абсолютный путь E2E-теста теперь берётся из `os.environ["AGENTMARSHAL_SNAPSHOT"]` (`tests/test_isolation.py:562-564`), то есть из независимого источника, который `_stage_env` отдаёт стадии (`src/agentmarshal/stages.py:511`), а не из `os.getcwd()`, который устанавливает сам проверяемый шаг re-entry (`subprocess.Popen(..., cwd=snapshot)`, `stages.py:630`); отсутствующая переменная дала бы `KeyError` вне `except OSError`, то есть тест упал бы громко, а не выдал ложное `ABSWRITE:blocked`. Skip теперь решается ровно read-only-полом — `if verdicts.readonly is not None` (`tests/test_isolation.py:520-524`), и ассерты `WRITE:blocked`/`ABSWRITE:blocked`/отсутствия ноты стали безусловными (`tests/test_isolation.py:588-590`), так что «половина сценария» больше не исполняется молча. Комментарий над таблицей флагов называет `sys/statvfs.h` (`src/agentmarshal/isolation.py:72`), что согласуется с тем, что константы читаются как `os.ST_*` и применяются к `os.statvfs(...).f_flag` (`isolation.py:287-308`); сами заголовки в этой песочнице недоступны (`grep` по `/usr/include` заблокирован), поэтому атрибуцию заголовка подтверждаю по коду и знанию glibc, а не исполнением. Демонстрирует `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate`.

2. **Критерий 2 (CR-224 `lazy-read-untested`) — выполнен.** `test_a_run_that_pauses_nothing_never_reads_the_journal` (`tests/test_stages.py:1962`) подменяет `stages_module.read_records` spy’ем в том же стиле, что уже используется в файле (`tests/test_stages.py:1917`), и утверждает `calls == []` на прогоне, где `pre-gate-stop` — `checked`, а `pre-gate-warn` — `failed (exit 9)`: именно та комбинация, где ленивость можно спутать с «нет записей». Это ровно тот пункт требования (`openspec/specs/extension-stages/spec.md`, «read lazily … never opens it»), который реализован в `accepted_pause` (`src/agentmarshal/stages.py:1047-1060`).

3. **Критерий 3 (CR-225 F2/F3/F4) — выполнен.** F2: `validate_task_id` теперь стоит в обёртке до `_resolve` (`src/agentmarshal/stages.py:1208-1212`), с тем же текстом `stage run: task id must match CR-<number>`, что печатал `run_stages` (`stages.py:801-804`), то есть прежний порядок отказа восстановлен и требование spec’а «invalid task identifier SHALL refuse before any manifest is read» (`spec.md:58`) не нарушено; пинится `test_a_bad_task_id_is_refused_before_the_project_check` (`tests/test_stages.py:400`), который проверяет обе ветки — плохой id вне проекта даёт task-id-отказ без «initialized project», валидный id — прежнее сообщение про неинициализированный проект. F3: вызов `post-gate` обёрнут в `try/except Exception` с одной stderr-строкой и сохранением `return 0` (`src/agentmarshal/cli.py:1200-1219`), `str(error)` прогнан через `escape_for_display`, так что строка остаётся одной даже с `\n` в сообщении; форсирует `test_a_post_gate_run_that_raises_leaves_the_completion_untouched` (`tests/test_complete_stages.py:690`), где `tempfile.TemporaryDirectory` подменён на бросающий и манифест объявляет только `post-gate` — pre-gate-план пуст и до `completed` временный каталог не запрашивается (`stages.py:879-885`), поэтому отказ действительно приходится на момент после записи. F4: сценарный тест теперь гоняет под spy и `stage run`, и `complete`, различая quiet-флаг — `calls == [("pre-gate", False), ("pre-gate", True), ("post-gate", True)]` (`tests/test_complete_stages.py:185-190`).

4. **Критерий 4 — выполнен в проверяемой части.** Дифф не трогает `openspec/`, а требование «its outcome SHALL change neither the record nor the exit status» (`openspec/specs/extension-stages/spec.md`, requirement «`complete` runs the `post-gate` stages after `completed` is written») новым перехватом как раз соблюдается, а не меняется; изменённые пути — только `stages.py`, `isolation.py`, `cli.py`, `tests/`, то есть в scope. Поведенческих изменений ровно два заявленных (порядок отказа в `stage run`, перехват post-gate); ветка `unknown phase` в `run_stages` из CLI недостижима (`choices` в парсере, `stages.py:236-242`), так что новая валидация не переставила ещё и её. Прохождение `uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy` здесь не исполнялось — беру из заметки координатора.

**Находки (все advisory, ни одна не блокирует)**

- `CR-227-ADV-1` — в `tests/test_stages.py` из существующего сценарного теста `test_a_journal_that_cannot_be_read_names_it_and_every_pause_stands` (`tests/test_stages.py:1930-1959`) при добавлении нового теста исчез последний ассерт `assert "paused before the gate" in captured.err`: сценарий «every pause stands» теперь держится только на `exit 3`, а pause-строку обёртки этот тест больше не проверяет. Ни один критерий такого изменения не просил; строка покрыта другими тестами (`tests/test_stages.py:1420,1435,1674,1695,1736`), поэтому это потеря покрытия, а не дыра.
- `CR-227-ADV-2` — перехват поставлен на call-site в `complete` (`src/agentmarshal/cli.py:1208-1218`), а не на самом незащищённом вызове `tempfile.TemporaryDirectory(prefix="agentmarshal-stage-")` внутри цикла рана (`src/agentmarshal/stages.py:1108`). Следствия: (а) `agentmarshal stage run --phase post-gate` на том же сбое по-прежнему падает traceback’ом — у `_run_stages` такого `try` нет (`stages.py:1213-1227`), и `main` ничего широкого не ловит (`cli.py:1808`); (б) в самом `complete` сбой на первой из нескольких post-gate-стадий обрывает цикл, и остальные расширения не получают ни result-строки, ни события, хотя ADR-0013 решение 7 требует строку каждому. Контракт просил ровно одну строку в `complete`, так что это остаточный зазор, а не невыполненный критерий; поведение `stage run` диффом не ухудшено.
- `CR-227-ADV-3` — docstring `_run_stages` (`src/agentmarshal/stages.py:1214-1220`) всё ещё описывает обёртку как «thin wrapper … it resolves the placement and the clone's local state … then prints what the result owes», не упоминая новый первый шаг — отказ по task id; `validate_task_id` теперь вызывается в двух местах (`stages.py:1209` и `stages.py:802`) с одинаковым текстом, и расхождение этих двух строк ничем не пришито. Комментарий над кодом порядок объясняет, но утверждение docstring стало неполным.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "813f12797a542b9f850eb3fb2483279c3c1011fb",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["CR-227-ADV-1", "CR-227-ADV-2", "CR-227-ADV-3"],
  "classes": {
    "CR-227-ADV-1": "test-gap",
    "CR-227-ADV-2": "correctness",
    "CR-227-ADV-3": "claim-accuracy"
  },
  "verification": {
    "read": [
      "src/agentmarshal/stages.py (module docstring, _stage_env, _run_stage launch, run_stages, accepted_pause, the loop's TemporaryDirectory, _run_stages, _resolve, the stage run parser)",
      "src/agentmarshal/cli.py (_run_complete in full, main dispatch, escape_for_display import, the switches except Exception at cli.py:1419)",
      "src/agentmarshal/isolation.py (MS_*/ST_* constants, _locked_mount_flags, probe's TemporaryDirectory)",
      "src/agentmarshal/journal/records.py (validate_task_id, read_records signature)",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "tests/test_isolation.py (the read-only e2e test and its neighbours)",
      "tests/test_stages.py (helpers _manifest/_extension/_repo_with_extension/_stage_run, the invalid-task-id test, the journal-unreadable test, the new lazy-read test)",
      "tests/test_complete_stages.py (helpers, the one-runner test, the new post-gate-raises test)",
      "openspec/specs/extension-stages/spec.md (stage run requirements and scenarios; the added complete/post-gate requirements)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (section A decisions 1-7)",
      ".agentmarshal/journal/tasks/CR-223/artifacts/01M5PKPDXN1GW6S57H7SZ9Z40E-review.md (ADV-2/3/4)",
      ".agentmarshal/journal/tasks/CR-224/artifacts/01M5PNJFKJ4ZK4XDRGARZXMF7G-review.md (lazy-read-untested)",
      ".agentmarshal/journal/tasks/CR-225/artifacts/01M5PT3FS64X65DPM1XYH77YTH-review.md (F2/F3/F4)",
      "pyproject.toml (ruff select, mypy strict, line-length)"
    ],
    "executed": [
      {"what": "grep -rn 'AGENTMARSHAL_SNAPSHOT' src tests", "result": "src/agentmarshal/stages.py:511 sets it to str(snapshot); tests/test_isolation.py:563 is the new independent source; tests/test_stages.py:635,761,767 already pin it"},
      {"what": "grep -rn 'tempfile|TemporaryDirectory|mkstemp|mkdtemp' src/agentmarshal (excluding stages.py)", "result": "only isolation.py:530 and journal/review.py:1230,1503 use TemporaryDirectory; the journal writers use mkstemp, so the F3 test's monkeypatch cannot hit the completion's own writes"},
      {"what": "grep -rn 'paused before the gate' tests/", "result": "test_stages.py:1420,1435,1674,1695,1736, test_switches.py:410, test_complete_stages.py:141,531,582 — the line removed from test_stages.py:1959 stays covered elsewhere"},
      {"what": "grep -n 'choices' src/agentmarshal/stages.py (stage run parser)", "result": "--phase has choices=('pre-gate','post-gate'), so run_stages' unknown-phase branch is unreachable from the CLI and the new validation reorders nothing else"},
      {"what": "grep -n 'select' pyproject.toml", "result": "ruff lint select = E,W,F,I,UP,B,SIM,RUF — no BLE, so the new 'except Exception' matches both the ruleset and cli.py:1419's existing style"}
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "no .venv and no uv in this environment and python execution is not permitted here; CI status for this commit taken from the coordinator's note"},
      {"what": "git diff / git log against the reviewed commit", "why": "the snapshot is not a git repository"},
      {"what": "grep -rn 'ST_NOSUID' /usr/include/ to confirm ADV-4's header attribution", "why": "the sandbox refuses searches outside the snapshot; the claim is checked against isolation.py's own use of os.ST_* on os.statvfs().f_flag instead"}
    ]
  },
  "evidence": {
    "CR-227-ADV-1": "tests/test_stages.py:1930-1959 — the test now ends at 'assert \"every pause stands\" in journal_lines[0]'; the diff's last hunk deletes '-    assert \"paused before the gate\" in captured.err' while appending test_a_run_that_pauses_nothing_never_reads_the_journal at 1962",
    "CR-227-ADV-2": "src/agentmarshal/cli.py:1208-1218 wraps the call site; src/agentmarshal/stages.py:1108 'with tempfile.TemporaryDirectory(prefix=\"agentmarshal-stage-\")' inside the per-stage loop is still unguarded, and src/agentmarshal/stages.py:1213-1227 (_run_stages) plus cli.py:1808 (main) catch nothing, so stage run --phase post-gate tracebacks; an abort on stage 1 of N skips the result lines ADR-0013 decision 7 owes stages 2..N",
    "CR-227-ADV-3": "src/agentmarshal/stages.py:1214-1220 docstring ('A thin wrapper over run_stages — it resolves the placement and the clone's local state … then prints what the result owes this command's transcript') vs the new first step at stages.py:1208-1212; validate_task_id is now called at both stages.py:1209 and stages.py:802 with the same message text"
  }
}
AGENTMARSHAL_VERDICT_END
