Проверил контракт, диff и файлы на коммите `defae9e69448b88eed3fa45313f979460df99693`. Ниже — по критериям приёмки, потом три advisory-находки.

**AC1 (CR-223 ADV-2/3/4) — выполнен.** `tests/test_isolation.py:562-564` берёт абсолютный путь из `os.environ["AGENTMARSHAL_SNAPSHOT"]`, который `_stage_env` отдаёт стадии как `str(snapshot)` (`src/agentmarshal/stages.py:511`), т.е. независимо от `cwd`, который устанавливает проверяемый re-entry; skip в `tests/test_isolation.py:517-523` теперь срабатывает ровно тогда, когда недоступен read-only floor, и write-проверки (`tests/test_isolation.py:586-588`) стали безусловными — половина сценария больше не выпадает молча. Демонстрирует `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate`. Комментарий `src/agentmarshal/isolation.py:72` теперь называет `sys/statvfs.h`, и это верно: `ST_NOSUID`…`ST_RELATIME` в glibc объявлены в `sys/statvfs.h` через `bits/statvfs.h`, а `sys/vfs.h` — интерфейс `statfs` (прочитать `/usr/include` в этой песочнице не дали, но ошибки в правке нет).

**AC2 (CR-224) — выполнен.** `test_a_run_that_pauses_nothing_never_reads_the_journal` (`tests/test_stages.py:1964`) подменяет `stages_module.read_records` spy-ем в стиле уже принятом в файле и утверждает `calls == []` на прогоне, где `pre-gate-stop` проходит (`checked`), а `pre-gate-warn` падает (`exit 9`) — ленивость `accepted_pause` (`src/agentmarshal/stages.py:1005-1016`) запинена именно на том пути, где её легко потерять.

**AC3 (CR-225 F2/F3/F4) — выполнен.** F2: `validate_task_id(args.task)` поднят в обёртку, до `_resolve` (`src/agentmarshal/stages.py:1228-1233`), и это безопасно — единственные два других вызова `run_stages` (`src/agentmarshal/cli.py:1109`, `:1203`) стоят после `load_task_for_record` → `load_task_status`, который валидирует id сам (`src/agentmarshal/journal/status.py:147-150`); пинит `test_a_bad_task_id_is_refused_before_the_project_check` (`tests/test_stages.py:401`), прежний спек-сценарий `test_an_invalid_task_identifier_refuses_before_any_stage_is_planned` продолжает выполняться. F3: `try/except Exception` вокруг post-gate-вызова (`src/agentmarshal/cli.py:1202-1219`), одна строка на stderr через `escape_for_display` (который экранирует `\n` по имени), exit и запись не меняются; форсирует `test_a_post_gate_run_that_raises_leaves_the_completion_untouched` (`tests/test_complete_stages.py:690`) — pre-gate-план пуст, так что первый `TemporaryDirectory` просят уже после `completed`. F4: `test_both_commands_go_through_the_one_runner` теперь гоняет под spy-ем и `stage run`, и `complete`, и сверяет тройку `(phase, quiet)`.

**AC4 — выполнен с одной оговоркой.** `openspec/changes/` содержит только `archive/`, requirements не менялись; diff не выходит за scope (`stages.py`, `isolation.py`, `cli.py`, `tests/`). Оговорка: «no other behaviour changes» нарушено в одну сторону — `src/agentmarshal/stages.py:1111-1148` вводит новое поведение (OSError машинерии стадии → её собственный `not run`), которого ни один критерий не требует; сам имплементор помечает его в docstring-ах как «CR-227-ADV-2». Оно покрыто тестом `test_a_stage_whose_temporary_directory_fails_is_not_run_and_the_run_goes_on` (`tests/test_stages.py:2006`) и попадает под уже существующее требование `openspec/specs/extension-stages/spec.md:335-337` («a stage that may not run prints not run (<reason>)»), поэтому спек-дельта не нужна — но именно оттуда растут две находки ниже. CI-последовательность я не запускал (нет venv/uv в этом окружении); статус беру из записки координатора по этому коммиту.

**ADV-1 (correctness, advisory)** — `src/agentmarshal/stages.py:1111-1148`: новый `try` обнимает весь `with`, а не только создание каталога, поэтому `except OSError` ловит и ошибку *очистки* `TemporaryDirectory.__exit__` (Python 3.12, `ignore_cleanup_errors=False`: `_rmtree` гасит только `FileNotFoundError` и чинит `PermissionError`, остальные OSError пробрасывает). Тогда уже присвоенный `outcome` затирается: результат реально отработавшей стадии (`checked`/`failed`) превращается в `not run (the stage's own machinery: …)`, её stdout-строки теряются (`output=b""`), в process log уходит `decision: not-run` для стадии, которая прошла, а для `pre-gate-stop` появляется пауза и exit 3 там, где его не было. Сценарий: стадия оставила живого внука (`start_new_session=True`, группа убивается только по timeout), тот пишет в snapshot — `rmtree` ловит `ENOTEMPTY`. Fail-closed, поэтому advisory, а не блокер; лечится переносом `try` на одно только создание каталога.

**ADV-2 (contract-mismatch, advisory)** — критерий AC3 требует, чтобы падение post-gate-прогона, «including creating the stage's temporary directory», было «caught and reported on one stderr line». В реализации именно этот случай (OSError на создании каталога) перехватывается на уровень ниже — в `run_stages` — и сообщается строкой результата стадии на **stdout** (`openspec: not run (…)`), а не одной строкой `complete:` на stderr; до обработчика `src/agentmarshal/cli.py:1213` он уже не доходит. Тест `test_a_post_gate_run_that_raises_leaves_the_completion_untouched` обходит это, форсируя `RuntimeError`, так что названный в критерии случай в post-gate-полосе `complete` не запинен ни одним тестом (его аналог есть только для `stage run`/pre-gate в `tests/test_stages.py:2006`). Инварианты критерия (exit 0, запись `completed` на месте) при этом соблюдены в обоих вариантах.

**ADV-3 (claim-accuracy, advisory)** — комментарий `src/agentmarshal/stages.py:1133-1137` утверждает, что `_prepare_extension` и `_run_stage` «hand every failure of theirs back as an outcome, so an OS-level refusal reaching here is the stage's own machinery — the temporary directory». Для `_prepare_extension` это так (`except Exception` в трёх местах, `src/agentmarshal/stages.py:439-453`), а `_run_stage` не полон: дренаж report-pipe (`os.close`/`os.read`, `src/agentmarshal/stages.py:657-661`) и `process.communicate` (`:669`, `:677`) не обёрнуты и могут выпустить OSError. Поведение от этого не страдает (строка `not run` разумна и там), но утверждение «это непременно временный каталог» неточно, и диагностика припишет чужую ошибку машинерии каталога.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "defae9e69448b88eed3fa45313f979460df99693",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1", "ADV-2", "ADV-3"],
  "classes": {
    "ADV-1": "correctness",
    "ADV-2": "contract-mismatch",
    "ADV-3": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn 'run_stages' --include=*.py .", "result": "only src/agentmarshal/stages.py:254 (_run_stages), :1237, src/agentmarshal/cli.py:1109 and :1203, plus the test spy — every caller validates the task id first"},
      {"what": "grep -rn 'def load_task_status' -A 10 src/agentmarshal/journal/status.py", "result": "line 147-150 calls validate_task_id and re-raises as TaskStatusError, so complete's lane refuses a bad id before run_stages"},
      {"what": "grep -rn 'AGENTMARSHAL_SNAPSHOT' src/ tests/ openspec/specs/", "result": "set at src/agentmarshal/stages.py:511 to str(snapshot) = temp_root/snapshot-<index>, the read-only candidate; tests/test_isolation.py:563 now reads it"},
      {"what": "grep -rn 'TemporaryDirectory|mkdtemp' src/agentmarshal/", "result": "stages.py:1112 and isolation.py:530 both pass prefix= as a keyword, so the refuse_once(prefix) stub in tests/test_stages.py:2030 is compatible with the probe's own call"},
      {"what": "grep -n 'import test_stages as stage_helpers' tests/test_complete_stages.py", "result": "line 24 — the stage_helpers alias the amended test uses was already imported"},
      {"what": "ls openspec/changes/", "result": "only archive/ — no working change directory, as the contract requires"},
      {"what": "cat .python-version; grep -n requires-python pyproject.toml", "result": "3.12 / >=3.12 — TemporaryDirectory cleanup errors propagate by default, which is what ADV-1 relies on"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "no uv or virtualenv in this read-only snapshot; CI status for this commit taken from the coordinator's note"},
      {"what": "grep -rl ST_RELATIME /usr/include", "why": "the sandbox refused reads outside the project, so the ADV-4 header attribution is confirmed from glibc's documented layout rather than from this machine"},
      {"what": "git diff / git log", "why": "the snapshot is not a git repository"}
    ],
    "read": [
      "src/agentmarshal/stages.py (_resolve, _prepare_extension, _stage_env, _run_stage, _result_text, StageRunResult, run_stages, _run_stages)",
      "src/agentmarshal/cli.py (_run_complete, escape_for_display import)",
      "src/agentmarshal/isolation.py (MS_/ST_ flag constants, probe's TemporaryDirectory)",
      "src/agentmarshal/journal/status.py (load_task_status, load_task_for_record)",
      "src/agentmarshal/journal/records.py (validate_task_id)",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "tests/test_stages.py (helpers _manifest/_extension/_repo_with_extension/_stage_run/_events, the two new tests, the existing invalid-task-id scenario)",
      "tests/test_complete_stages.py (header imports, _repo, the amended one-runner test, the new post-gate raise test)",
      "tests/test_isolation.py (the read-only end-to-end test)",
      "openspec/specs/extension-stages/spec.md (not-run reasons, the shared-runner requirements at 1228-1310)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (decision 7)",
      ".agentmarshal/journal/tasks/CR-223/artifacts/01M5PKPDXN1GW6S57H7SZ9Z40E-review.md (ADV-2/3/4)",
      ".agentmarshal/journal/tasks/CR-225/records/01M5PT3FS64X65DPM1XYH77YTH-review.json and its artifact (F2/F3/F4)"
    ]
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/stages.py:1111 'try:' wraps the whole 'with tempfile.TemporaryDirectory(' block (:1112-1130), so the except at :1132 also catches TemporaryDirectory.__exit__/cleanup; outcome assigned by _run_stage at :1117 is overwritten at :1142-1146 with _Outcome('not-run', ..., b''), which then drives the printed lines (:1150-1156), record_event (:1197) and the pause bookkeeping (:1198-1203). CPython 3.12 tempfile.TemporaryDirectory.cleanup -> _rmtree(ignore_errors=False); its onexc only retries PermissionError and ignores FileNotFoundError",
    "ADV-2": "contract AC3 'including creating the stage's temporary directory — is caught and reported on one stderr line'; the OSError path is handled at src/agentmarshal/stages.py:1132-1146 and surfaces as the stdout result line built at :1158-1166, never reaching src/agentmarshal/cli.py:1213-1219; tests/test_complete_stages.py:713-716 monkeypatches tempfile.TemporaryDirectory to raise RuntimeError ('An OSError there is now the stage's own `not run` line'), so no test forces an OSError in complete's post-gate lane",
    "ADV-3": "src/agentmarshal/stages.py:1133-1137 claims _prepare_extension and _run_stage 'hand every failure of theirs back as an outcome'; _prepare_extension does (except Exception at :439, :449, :453), but _run_stage leaves os.close(report_pipe[1]) / os.read / os.close at :657-661 and process.communicate at :669 and :677 unguarded against OSError"
  }
}
AGENTMARSHAL_VERDICT_END
