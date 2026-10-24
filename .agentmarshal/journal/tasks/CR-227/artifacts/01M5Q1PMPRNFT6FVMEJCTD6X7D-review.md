Проверил диф построчно против контракта, ADR-0013, спеки и записей журнала CR-223/CR-225. Ниже — по критериям, затем одна необязательная находка.

**Критерий 1 (изоляция, CR-223 ADV-2/3/4) — выполнен.** `tests/test_isolation.py:561-564` строит абсолютный путь из `os.environ["AGENTMARSHAL_SNAPSHOT"]`, который `_stage_env` действительно выставляет (`src/agentmarshal/stages.py:511`), а не из `os.getcwd()`, то есть вторая нога теста больше не зависит от того самого `chdir`, который проверяется; `tests/test_isolation.py:518-523` теперь пропускает тест по причине probe, как только `verdicts.readonly is not None`, и write-проверки (`WRITE:blocked`, `ABSWRITE:blocked`, отсутствие ноты `not enforced: read-only candidate`) стали безусловными (`tests/test_isolation.py:587-589`) — то есть сценарий больше не «исполняется наполовину молча»; комментарий `src/agentmarshal/isolation.py:72` теперь называет `sys/statvfs.h`. Демонстрирует всё это `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate`. Сами системные заголовки в этой песочнице не читаются, так что атрибуция `sys/statvfs.h` сверена только со знанием glibc (`ST_*` — `bits/statvfs.h` через `sys/statvfs.h`, `sys/vfs.h` — интерфейс `statfs`), локально не подтверждена.

**Критерий 2 (ленивое чтение журнала, CR-224) — выполнен.** `tests/test_stages.py:test_a_run_that_pauses_nothing_never_reads_the_journal` подменяет `stages_module.read_records` spy-ом в стиле соседних тестов и утверждает `calls == []` при плане из `pre-gate-stop` (checked) и `pre-gate-warn` (exit 9 → предупреждение, не пауза). В `stages.py` `read_records` вызывается ровно в одном месте — `accepted_pause`, `stages.py:1056`, — и вызывается только для `pre-gate-stop` с решением не `checked`/`switched-off` (`stages.py:1169-1175`), так что пустой список действительно означает «журнал не открывали».

**Критерий 3 (CR-225 F2/F3/F4 и решение 7) — выполнен.** Порядок отказов восстановлен: `validate_task_id` снова стоит в обёртке до `_resolve` (`stages.py:1237-1243`), и `test_a_bad_task_id_is_refused_before_the_project_check` закрепляет оба конца — вне проекта плохой id даёт `stage run: task id …` без упоминания проекта, а валидный id — прежнюю строку `must be run inside an initialized project`. Снятие проверки из `run_stages` безопасно: вызывающих ровно двое, и у `complete` `load_task_for_record` → `load_task_status` валидирует id тем же `validate_task_id` (`journal/status.py:148`) до любого стейджа, так что комментарий `stages.py:801-805` точен. Отказ создания временного каталога стал строкой `not run (the stage's own machinery: …)` этого стейджа, а прогон продолжается (`stages.py:1145-1159`) — демонстрирует `test_a_stage_whose_temporary_directory_fails_is_not_run_and_the_run_goes_on` (exit 3, `warn ran` и `openspec: checked` на месте, события `["not-run", "checked"]`), что совпадает с решением 7 ADR-0013 («No silence. Every extension gets a result line», docs/adr/ADR-0013:113) и с общим требованием спеки `not run (<reason>)` (openspec/specs/extension-stages/spec.md:313-337), поэтому правки требований действительно не нужны. Отказ teardown-а не переписывает посчитанный исход, а печатается одной нотой голосом `stage run` (`stages.py:1131-1144`, спека 1256 требует именно этот голос для `note:`) — демонстрирует `test_a_stage_whose_teardown_fails_keeps_the_outcome_it_computed`. Пост-гейтовая полоса `complete` обёрнута в `except Exception` с одной строкой stderr и неизменными exit-статусом и записью (`cli.py:1202-1219`) — демонстрируют `test_a_post_gate_run_that_raises_leaves_the_completion_untouched` (RuntimeError на `tempfile.TemporaryDirectory`) и `test_an_oserror_in_the_post_gate_lane_is_one_stderr_line` (OSError из `_base_switches`, которого pre-gate-прогон не достигает, потому что его план пуст). F4 закрыт: `test_both_commands_go_through_the_one_runner` теперь гоняет под spy-ем и `stage run`, и `complete`, фиксируя `[("pre-gate", False), ("pre-gate", True), ("post-gate", True)]`.

**Критерий 4 — выполнен в проверяемой части.** `openspec/changes/` содержит только `archive/`, спека и `openspec/specs/` не тронуты, вне scope-а контракта ничего не менялось, подмены `tempfile.TemporaryDirectory` в тестах совместимы по сигнатуре с единственным другим вызовом в проде (`isolation.py:530`, тоже keyword `prefix`). Полную последовательность CI запустить не смог — в снапшоте нет venv/uv и запуск python не разрешён; статус взят из заметки координатора для 8d601a28.

**ADV-1 (advisory, не блокирует).** Комментарий `src/agentmarshal/stages.py:1146-1149` утверждает, что «`_prepare_extension` и `_run_stage` отдают любой свой сбой обратно исходом», — для `_prepare_extension` это так (`stages.py:434-463`, `except Exception` на каждом шаге), а `_run_stage` всё же может выпустить `OSError` наружу: слив отчётного пайпа `os.close`/`os.read` на `stages.py:657-661` не обёрнут ничем, и такой сбой попадёт в новый `except OSError` и будет назван «the stage's own machinery», то есть отнесён к временному каталогу. Строка результата при этом остаётся честной (`not run` с текстом ошибки), так что это неточность комментария, а не поведения.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8d601a283f30ae6d83d04f7077a5a8ea14a271f6",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1"],
  "classes": {
    "ADV-1": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn 'run_stages' src/ tests/", "result": "вызывающих два — cli.py:1109 (pre-gate, quiet) и cli.py:1203 (post-gate, quiet) — плюс обёртка stages.py:1250 и spy в тестах; снятие validate_task_id из run_stages не открывает третьего пути"},
      {"what": "grep -n 'read_records|journal_root' src/agentmarshal/stages.py", "result": "единственный вызов — stages.py:1056 внутри accepted_pause, который зовётся лишь для pre-gate-stop с решением не checked/switched-off (stages.py:1169-1175)"},
      {"what": "grep -rn 'TemporaryDirectory|mkdtemp' src/agentmarshal/", "result": "stages.py:1112 и isolation.py:530 — оба с keyword prefix, поэтому стабы refuse_once(prefix)/CleanupRefusal в тестах совместимы и probe получает реальный каталог"},
      {"what": "grep -rn 'AGENTMARSHAL_SNAPSHOT' src/ tests/ openspec/specs", "result": "stages.py:511 выставляет переменную абсолютным путём snapshot-<index>; tests/test_isolation.py:563 берёт её же"},
      {"what": "grep -n 'machinery|not run|note' openspec/specs/extension-stages/spec.md", "result": "требование 313-337 допускает любой 'not run (<reason>)'; сценарий 1302-1308 перечисляет машинные отказы (манифест, trust.toml) и exit 1; 1256 закрепляет голос 'stage run' для note-строк — новая нота и новый not-run им не противоречат"},
      {"what": "ls openspec/changes/", "result": "только archive/ — нового OpenSpec-change нет, как и требует критерий 4"},
      {"what": "чтение .agentmarshal/journal/tasks/CR-223 и CR-225 (review-записи и артефакты)", "result": "тексты ADV-2/3/4 и F2/F3/F4 совпадают с тем, что закрывает диф; F2 прямо говорит, что до CR-225 первым печатался отказ по task id"}
    ],
    "read": [
      "src/agentmarshal/stages.py (module docstring, run_stages, _run_stages, _resolve, _prepare_extension, _run_stage, _result_text, _Outcome)",
      "src/agentmarshal/cli.py (_run_complete целиком)",
      "src/agentmarshal/isolation.py (docstring, константы ST_*/MS_*, probe, _probe_child)",
      "src/agentmarshal/journal/status.py (load_task_status, load_task_for_record)",
      "src/agentmarshal/journal/records.py (validate_task_id)",
      "tests/test_stages.py (хелперы, тест на невалидный id, три новых теста)",
      "tests/test_complete_stages.py (хелперы, one-runner тест, два новых теста)",
      "tests/test_isolation.py:509-592",
      "openspec/specs/extension-stages/spec.md (требования о task id, result line, notes, одном runner, complete)",
      "docs/adr/ADR-0013-...md (решения 7 и 8)",
      ".agentmarshal/journal/tasks/CR-225/{records,artifacts}, .agentmarshal/journal/tasks/CR-223/artifacts",
      "CHANGELOG.md (0.6.0 раздела ещё нет — запись пишется к релизу, вне scope)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "в снапшоте нет venv и uv, запуск python не разрешён; статус CI для 8d601a28 взят из заметки координатора"},
      {"what": "git diff / git log против ревьюируемого коммита", "why": "снапшот не является git-репозиторием"},
      {"what": "проверка заголовков glibc (grep ST_NOSUID /usr/include)", "why": "песочница не даёт выходить за рабочий каталог — атрибуция sys/statvfs.h сверена только со знанием glibc"}
    ]
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/stages.py:1146-1149 — '``_prepare_extension`` and ``_run_stage`` hand every failure of theirs back as an outcome' против src/agentmarshal/stages.py:657-661, где слив отчётного пайпа ('os.close(report_pipe[1])', 'while chunk := os.read(report_pipe[0], 65536)', 'os.close(report_pipe[0])') не обёрнут в try, в отличие от Popen (stages.py:626-650) и communicate (stages.py:668-684); такой OSError попадёт в новый except на stages.py:1145 и будет назван 'the stage's own machinery'"
  }
}
AGENTMARSHAL_VERDICT_END
