## Review CR-227 — commit 8d601a283f30ae6d83d04f7077a5a8ea14a271f6

**Критерий 1 (CR-223 ADV-2/3/4) — выполнен.** Абсолютный путь берётся из протокольной переменной: `tests/test_isolation.py:562-564` читает `os.environ["AGENTMARSHAL_SNAPSHOT"]`, и это ровно тот путь, который рантайм кладёт в env (`src/agentmarshal/stages.py:511` — `"AGENTMARSHAL_SNAPSHOT": str(snapshot)`), а не то, что оставляет `os.chdir` из re-entry (`isolation.py:312`). Skip теперь зависит только от read-only floor (`tests/test_isolation.py:519-523`), и write-ассерты стали безусловными (`tests/test_isolation.py:586-588`) — половина сценария больше не отбрасывается молча. Комментарий над mapping называет `sys/statvfs.h` (`isolation.py:72`), и fallback-значения ему соответствуют (`ST_RELATIME` 4096 против `MS_RELATIME` `1 << 21`). Демонстрирует `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate`.

**Критерий 2 (CR-224 lazy-read) — выполнен.** `test_a_run_that_pauses_nothing_never_reads_the_journal` (`tests/test_stages.py:1964`) подменяет `stages_module.read_records` spy-функцией в стиле уже принятом в файле и ассертит `calls == []` на прогоне, где `pre-gate-stop` — `checked`, а `pre-gate-warn` падает (warning, не пауза). Spy ловит именно то связывание имени, которым пользуется ленивый `accepted_pause` (`stages.py:1215`), так что тест действительно отличает ленивое чтение от жадного.

**Критерий 3 — выполнен по всем четырём частям.** Порядок отказов восстановлен: `validate_task_id` переехал из runner'а в обёртку перед `_resolve` (`stages.py:1238-1244`), что возвращает поведение до CR-225 — F2 жаловался ровно на обратное (журнал CR-225: «теперь печатает "must be run inside an initialized project" вместо прежнего отказа по task id»). Формулировка критерия тут читается двусмысленно, но цитируемый F2 её разрешает однозначно; пинит `test_a_bad_task_id_is_refused_before_the_project_check` (`tests/test_stages.py:401`) — оба сообщения, оба порядка. Снятие проверки из `run_stages` безопасно: `complete` зовёт `load_task_for_record` → `load_task_status` → `validate_task_id` (`journal/status.py:147-150`) до любой стадии, и spec-требование «An invalid task identifier SHALL refuse before any manifest is read» (`openspec/specs/extension-stages/spec.md:58`) остаётся верным. Отказ `tempfile.TemporaryDirectory` даёт стадии свою строку `not run (the stage's own machinery: …)` и прогон идёт дальше (`stages.py:1143-1158`) — `test_a_stage_whose_temporary_directory_fails_is_not_run_and_the_run_goes_on` (`tests/test_stages.py:2006`) проверяет exit 3, пропуск `stop ran`, наличие `warn ran`, `openspec: checked` и события `["not-run", "checked"]`, то есть decision 7 («Every extension gets a result line», ADR-0013:113) соблюдён. Отказ teardown ловится внутри `finally` и не перезаписывает вычисленный outcome (`stages.py:1131-1142`) — `test_a_stage_whose_teardown_fails_keeps_the_outcome_it_computed` (`tests/test_stages.py:2059`) оставляет стадию `checked` и пинит одну note-строку. Пост-gate lane обёрнут в `except Exception` с одной stderr-строкой и без влияния на статус и запись (`cli.py:1202-1218`) — `test_a_post_gate_run_that_raises_leaves_the_completion_untouched` (`tests/test_complete_stages.py:690`) и `test_an_oserror_in_the_post_gate_lane_is_one_stderr_line` (`:728`, OSError из `_base_switches`). F4: `test_both_commands_go_through_the_one_runner` (`:156`) теперь гоняет и `stage run` под spy и ассертит `[("pre-gate", False), ("pre-gate", True), ("post-gate", True)]`.

**Критерий 4 — выполнен в проверяемой части.** Под `openspec/` ничего не менялось, и не требовалось: `not run (<reason>)` в spec открытая форма (`extension-stages/spec.md:17`), note-строки обязаны сохранять голос `stage run` даже в quiet-режиме (`spec.md:1256-1258`) — новая note это соблюдает, а diff не выходит за scope контракта. Полную CI-последовательность я не прогонял: sandbox этой сессии не даёт запускать интерпретатор, поэтому опираюсь на заявление координатора.

**ADV-1 (advisory, claim-accuracy).** Комментарий в `src/agentmarshal/cli.py:1198-1201` объясняет новый `except Exception` именно тем случаем, который после этого же diff до него больше не доходит: «A run that raises at all — the stage's temporary directory is created inside the runner — is reported on one line», тогда как OSError при создании этой директории теперь превращается в строку стадии `not run (the stage's own machinery: …)` внутри runner'а (`stages.py:1143-1158`) и наружу не поднимается. Сам имплементатор это осознаёт — в комментарии теста `tests/test_complete_stages.py:713-715` написано прямо противоположное тому, что говорит комментарий в cli.py, — но cli.py остался с устаревшим примером; читатель заключит, что сбой temp-директории на post-gate даёт строку «could not finish», а не result-строку стадии. Правка чисто комментарий, поведение верное.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8d601a283f30ae6d83d04f7077a5a8ea14a271f6",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1"],
  "classes": {"ADV-1": "claim-accuracy"},
  "verification": {
    "read": [
      "src/agentmarshal/stages.py (run_stages 758-1253, _prepare_extension 403-465, _run_stage 530-694, _stage_env 476-514, _run_stages 1226-1253)",
      "src/agentmarshal/cli.py (_run_complete 1040-1220, escape_for_display import :50)",
      "src/agentmarshal/isolation.py (module docstring, flag constants 55-82, _bind_read_only 293-312)",
      "src/agentmarshal/journal/status.py:144-193 (load_task_status/load_task_for_record validate the task id)",
      "src/agentmarshal/journal/records.py:331-335 (validate_task_id message), :2667-2692 (read_records)",
      "tests/test_stages.py (helpers 1-180, :370-425, :1964-2095)",
      "tests/test_complete_stages.py (:1-200, :685-760)",
      "tests/test_isolation.py:508-590",
      "openspec/specs/extension-stages/spec.md (:17-110, :1229-1330)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md decision 7 (:113-117)",
      ".agentmarshal/journal/tasks/CR-225 review/completed records (F2 text), .agentmarshal/journal/tasks/CR-223 completed record (ADV-2/3/4 dispositions)"
    ],
    "executed": [
      {"what": "grep -rn 'run_stages' src/ tests/", "result": "only cli.py:1109 and cli.py:1203 call it, both after load_task_for_record — the removed in-runner validate_task_id is covered by the loader"},
      {"what": "grep -rn 'TemporaryDirectory|mkdtemp' src/", "result": "stages.py:1112 and isolation.py:530 both pass prefix= as a keyword, so the tests' refuse_once(prefix)/CleanupRefusal substitutes fit every call the run makes"},
      {"what": "grep -rn 'TemporaryDirectory\\[' . --include=*.py", "result": "only the two new uses in tests/test_stages.py:2031,2072 — no prior art in the repo for the runtime subscript"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "this review session's sandbox refuses to execute python3/uv/pytest at all; relying on the coordinator's statement that the sequence passed on this commit"},
      {"what": "runtime check that tempfile.TemporaryDirectory[str] is subscriptable (class base at tests/test_stages.py:2072 is evaluated at import, and the file has no 'from __future__ import annotations')", "why": "no interpreter available; since pytest passed on this commit the subscript must resolve, so no finding is raised"}
    ]
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/cli.py:1198-1201 ('A run that raises at all — the stage's temporary directory is created inside the runner — is reported on one line and changes just as little.') versus src/agentmarshal/stages.py:1143-1158, where an OSError from tempfile.TemporaryDirectory(prefix=\"agentmarshal-stage-\") becomes _Outcome('not-run', f\"the stage's own machinery: …\") and never leaves run_stages; tests/test_complete_stages.py:713-715 states the corrected version ('An OSError there is now the stage's own `not run` line (CR-227-ADV-2); the run-level report is for a raise the runner does not handle itself') and forces the cli.py path with a RuntimeError instead."
  }
}
AGENTMARSHAL_VERDICT_END
