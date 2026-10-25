Проверил diff против кода на коммите `1952617a1386647ee04f46bd06b0fbce69eb3779`. Ниже — по каждому acceptance criterion, затем два advisory-замечания.

**AC1 (CHANGELOG, write-time fix CR-236) — выполнен.** `CHANGELOG.md:245-252` теперь обещает ровно то, что держит код: `json.dumps` и `f"{content}\n".encode()` стоят в `src/agentmarshal/journal/records.py:2113-2117` до `_prepare_record_directory`/`_create_exclusive` (строки 2118-2120), а запись после создания файла (`record_file.buffer.write(body)`, строка 2124) ничем не откатывается — новая формулировка «a failure while writing or closing the created file is not rolled back» это и говорит. Demonstrates: `tests/test_record_text_safety.py::test_a_failure_while_encoding_leaves_no_file` (unpaired surrogate в `outcome` → `UnicodeEncodeError`, `assert not journal_root.exists()`); обратного теста — что частичная запись откатывается — в suite нет, что согласуется с суженным обещанием.

**AC2 (README, capture policy) — выполнен.** Предложение «They remain inactive in 0.6.0» убрано (`README.md:41-54`); review-класс назван shipped с тремя уровнями, и это ровно код: `capture.py:70-86` (preset `attested` по умолчанию → `REVIEWS: HASH`), `review.py:1595` (`commit` → `prose=raw_output`, дальше `submit_review.py:144` `write_artifact`), `review.py:1619` + `_keep_accepted_output` (`review.py:710-742`, событие `review-prose` в `log/files/` локального state), `review.py:1621` (`off` — «was not kept»). Не-shipped части названы отдельно и верно: `CaptureClass.ECONOMICS`/`SESSIONS` и `resolve_session_disposition` в production-коде не читаются нигде (встречаются только в `tests/test_capture.py`), а `journal/attestation.py:21` сам пишет «This module owns the declaration; it emits no Statement». Demonstrates: `tests/test_review_capture.py::test_by_default_the_prose_stays_out_of_the_journal`, `::test_commit_keeps_todays_behaviour`, `::test_off_keeps_nothing`, `::test_local_state_that_cannot_be_used_falls_back_to_a_temporary_file`, плюс `tests/test_capture.py` на preset-таблицу.

**AC3 (тела proposals) — выполнен.** Все 19 перечисленных файлов обновлены (012, 024, 025, 026, 027, 028, 029, 030, 031, 032, 034, 036, 037, 039, 040, 041, 042, 044, 045) плюс 009, 018, 020, 023, 035; каждый новый «Where» совпадает с колонкой Where в `docs/proposals/README.md` и проверяется кодом. Выборочно подтверждено: `gate.py:2312` + `cli.py:1530` (035), `status_view.py:665,673` (036), `status_view.py:298` и `report.py:117-126,949,1005,1038` включая нюанс «unmeasured session that carries a cost still sums» (044), `outbox.py:65,772` — `SENT` и `skipped as sent: <n>` (045), `outbox.py:114-145` (029, 023, 012), `project.py:322-340` + `CHANGELOG.md:855` в секции 0.2.0 (012), `records.py:203-225,909,914-954` — `commit`/`report_ready`/`cli_session`/`resets_at`/`cost{amount,currency,source}`/`contract` (018, 024, 031, 036, 041, 042), `agree.py:59-67` (031), `report.py:318-374` (032), `status_view.py:524-556` + `gate.py:2417-2434` (026, 039), `status_view.py:584-617` + `cli.py:363-371` (027), `brief.py:72,121` + `report.py:437` (028), `cli.py:486-491` (039), `steps.py:176-230` + `status_view.py:867-883` + `doctor.py:902-905` (040, 042), `review.py:341-360` (037), `templates/journal-transaction.sh:8-71` (032, 040), ADR-0022 §4 «The session outcome vocabulary» (строки 176-183) для `output-limit`/`stalled`/`safety-limit`/`time-limit` (034, 041, 042), ADR-0016:201 «the decision automates no per-finding status» (026). Исходный текст findings нигде не переписан: во всех файлах правка живёт в «## Where» (или новым датированным bullet в 035), датированные Disposition-секции оставлены как есть — ровно конвенция, по которой уже были написаны 024/025/044. Demonstrates: `tests/test_unmeasured_session_usage.py` (044), `tests/test_outbox.py` (045/029/023), `tests/test_status_base.py` и `tests/test_gate.py` (035), `tests/test_status_candidate_session.py` (036), `tests/test_report_lead_time.py` (032), `tests/test_status_count_deferrals.py` и `tests/test_complete_dispositions.py` (027), `tests/test_review_links_and_classes.py` (026/039), `tests/test_report_cost_checks_findings.py::test_failed_and_error_count_passed_and_skipped_do_not` и `tests/test_brief_last_failing_check.py` (028), `tests/test_review_verification_and_evidence.py` (030), `tests/test_contract_hash.py` и `tests/test_agree.py` (031), `tests/test_steps.py`/`tests/test_status_steps.py`/`tests/test_doctor_steps_paths.py` (040/042), `tests/test_review_launcher.py::test_a_file_that_does_not_decode_does_not_stop_the_review` (037), `tests/test_stages.py`/`tests/test_complete_stages.py` (009/039), `tests/test_journal_transaction.py` (032/040), `tests/test_acknowledge.py` (020), `tests/test_gate_assignment.py`/`tests/test_status_assignment.py` (034), `tests/test_project.py` (012).

**AC4 — выполнен в проверяемой части.** Diff трогает только `CHANGELOG.md`, `README.md` и файлы под `docs/proposals/` — всё внутри scope. Все новые relative-ссылки разрешаются: `docs/adr/ADR-0013`, `ADR-0015`, `ADR-0018`, `ADR-0021`, `ADR-0022` присутствуют в листинге `docs/adr/`, `023-…md` и `029-…md` — в `docs/proposals/`. Полную CI-последовательность я не запускал (read-only review, diff только документационный, координатор подтвердил прохождение на этом коммите) — отмечаю это в `verification.not_run`, а не как finding.

**ADV-016-hash-prose-stale** — `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md` (секция «Later — 2026-09-18») до сих пор пишет, что при уровне `hash` вывод ревьюера остаётся «in a local temporary file whose path the command prints»; с 0.5.0 это неверно — prose уходит в `log/files/` локального state клона с событием `review-prose` (`src/agentmarshal/journal/review.py:710-742`), а temp-файл остался только fallback'ом. Файл не входит в перечисленные в AC3 и утверждение стоит под датированным заголовком (конвенция репозитория читает такие заметки как «на тот момент»), поэтому это не блокирует, но цели «читатель proposal узнаёт, что код делает сейчас» он не достигает.

**ADV-changelog-serialisation-spelling** — в `CHANGELOG.md:248` добавленное «an encoding or serialisation failure» использует британское написание, тогда как единственное другое вхождение этого корня в файле — американское («canonically serialized», секция 0.6.0, CR-212-блок); «serialis» в CHANGELOG.md встречается ровно один раз и это строка данного diff.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "1952617a1386647ee04f46bd06b0fbce69eb3779",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-016-hash-prose-stale", "ADV-changelog-serialisation-spelling"],
  "classes": {
    "ADV-016-hash-prose-stale": "claim-accuracy",
    "ADV-changelog-serialisation-spelling": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 60 src/agentmarshal/journal/records.py", "result": "encode at line 2117 precedes _prepare_record_directory/_create_exclusive (2118-2120); post-creation write at 2124 has no rollback — AC1 wording holds"},
      {"what": "grep -rn 'CaptureClass\\.|resolve_session_disposition|level_for(' --include=*.py src/ tests/ | grep -v journal/capture.py", "result": "only tests/test_capture.py matches; economics and sessions levels are read by no production code"},
      {"what": "sed -n 1,100p src/agentmarshal/journal/capture.py", "result": "DEFAULT_PRESET='attested' → CaptureClass.REVIEWS: CaptureLevel.HASH, confirming README's 'hash (the default)'"},
      {"what": "grep -rn 'review-prose|CaptureLevel' --include=*.py src/ and sed -n 700,745p;1580,1635p src/agentmarshal/journal/review.py", "result": "commit→write_artifact (submit_review.py:144), hash→_keep_accepted_output with 'review-prose' event in log/files/, off→'was not kept'"},
      {"what": "grep -n 'Statement' src/agentmarshal/journal/attestation.py", "result": "line 21: 'This module owns the declaration; it emits no Statement'"},
      {"what": "grep -rn 'opened/amendment records of other tasks|Records absent from|Reviewed commit|did not end|tokens=unmeasured|unmeasured=|skipped as sent' --include=*.py src/", "result": "gate.py:2312, cli.py:1530, status_view.py:665/673/298, report.py:949/1005/1038, outbox.py:772 — all present as the proposals now state"},
      {"what": "grep -n '^### ' docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md; sed -n 176,184p", "result": "section 4 is 'The session outcome vocabulary' and lists provider-limit, output-limit, stalled, safety-limit, time-limit — citations in 034, 041, 042 are correct"},
      {"what": "grep -n -i 'automat|per-finding' docs/adr/ADR-0016-the-lifecycle-of-review-findings.md", "result": "line 201 'the decision automates no per-finding status' — matches 026's new wording"},
      {"what": "grep -n 'upstream' CHANGELOG.md; grep -n '^## ' CHANGELOG.md", "result": "'init creates .agentmarshal/upstream/ with a README' at line 855, inside the 0.2.0 section (713-876) — 012's '0.2.0' is right"},
      {"what": "ls docs/adr/ ; ls docs/proposals/", "result": "every ADR and proposal target newly linked by the diff exists (ADR-0013/0015/0018/0021/0022, 023-…, 029-…)"},
      {"what": "grep -rn -i 'not shipped|not yet shipped|not yet done|undecided|to be written' docs/proposals/*.md", "result": "remaining occurrences all sit in dated Disposition sections or in 038/043, whose index Where still says not shipped; no un-updated current-status line contradicts the index"},
      {"what": "grep -rc 'serialis' CHANGELOG.md ; grep -rl 'serializ' CHANGELOG.md", "result": "CHANGELOG.md:1 (the line this diff adds) against the file's own 'canonically serialized'"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section, lines 11-252; 0.2.0/0.4.0/0.5.0 boundaries)",
      "README.md lines 30-70",
      "docs/proposals/README.md (full index, all Where columns)",
      "docs/proposals/009, 012, 016, 019, 040, 042 bodies",
      "src/agentmarshal/journal/records.py (write_record, schema-7 field sets, cost/resets_at/contract validation)",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/journal/review.py",
      "src/agentmarshal/journal/submit_review.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/brief.py",
      "src/agentmarshal/journal/attestation.py",
      "src/agentmarshal/agree.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/steps.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/cli.py (submit-review prose path, report/gate/complete parsers, status --base)",
      "templates/journal-transaction.sh",
      "templates/github/agentmarshal-governance.yml",
      "docs/adr/ADR-0016, ADR-0022, ADR-0023",
      "tests/test_record_text_safety.py (encode-failure test), tests/test_review_capture.py, tests/test_capture.py, tests/test_report_cost_checks_findings.py, tests/test_review_launcher.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; the diff touches only Markdown under the contract's scope, and the coordinator states the full sequence passed on this commit"}
    ]
  },
  "evidence": {
    "ADV-016-hash-prose-stale": "docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md, section 'Later — 2026-09-18': 'By default its reviews level is hash: an accepted review's standard output stays out of the journal, in a local temporary file whose path the command prints' vs src/agentmarshal/journal/review.py:710-742 (_keep_accepted_output → _local_state_output, 'The file lands in log/files/ under the clone's local state … and a review-prose event names the file and its sha256'; the temporary file is only the _LocalStateUnavailable fallback)",
    "ADV-changelog-serialisation-spelling": "CHANGELOG.md:248 'an encoding or serialisation failure'; `grep -rc serialis CHANGELOG.md` → 1 (this line only), while the same file writes 'canonically serialized' in the 0.6.0 record-ext entry"
  }
}
AGENTMARSHAL_VERDICT_END
