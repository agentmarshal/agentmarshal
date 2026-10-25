Проверил весь diff против контракта, кода и индекса `docs/proposals/README.md`.

## Что сделано

**AC1 — CHANGELOG, обещание write-time fix: выполнено.** `CHANGELOG.md:247-253` теперь говорит ровно то, что держит код: кодирование происходит до создания файла (`src/agentmarshal/journal/records.py:2113-2124` — `body = f"{content}\n".encode()` стоит перед `_create_exclusive(path)`), и добавлена вторая половина правды — «a failure while writing or closing the created file is not rolled back», которой код и правда не делает (`record_file.buffer.write(body)` без cleanup). Демонстрирует это `tests/test_record_text_safety.py::test_a_failure_while_encoding_leaves_no_file` — surrogate в `outcome` проходит validation, падает на encode, и тест утверждает `not journal_root.exists()`; пути «упало после create» не покрывает ни один тест, что и подтверждает корректность новой оговорки.

**AC2 — README, capture policy: выполнено.** `README.md:43-56` больше не называет политику inactive: уровень `reviews` берётся из preset ровно как в `src/agentmarshal/journal/capture.py:69-88` (`attested`→`HASH`, `full`→`COMMIT`, `minimal`→`OFF`), override — `capture.py:149-150` + `review_capture_level_from_journal` (`capture.py:250-259`), `commit` пинит prose как journal artifact (`submit_review.py:137-144` → `write_artifact`), `hash` кладёт под local state с событием `review-prose` (`review.py:710-743`). Неотгруженное названо отдельно и проверяемо: `level_for(CaptureClass.ECONOMICS/SESSIONS)` и `allow_public_sessions` не вызываются нигде вне `capture.py` (grep по `src/` пуст), `attestation.py:21` сам говорит «it emits no Statement». Демонстрируют `tests/test_capture.py::test_preset_resolved_levels`, `::test_override_beats_preset` и `tests/test_review_capture.py::test_by_default_the_prose_stays_out_of_the_journal`, `::test_commit_keeps_todays_behaviour`, `::test_off_keeps_nothing`, `::test_local_state_that_cannot_be_used_falls_back_to_a_temporary_file`.

**AC3 — Where-строки proposals: выполнено.** Все 19 обязательных файлов (012, 024–032, 034, 036, 037, 039–042, 044, 045) обновлены, плюс 009, 016, 018, 020, 023, 035. Каждое утверждение бьётся с кодом: `gate.py:2312` («candidate adds opened/amendment records of other tasks») и `cli.py:1530` («Records absent from <base>») для 035; `status_view.py:665,673` для 036; `outbox.py:65,772` и `--index` у `check/send/status` (`outbox.py:126,134,142`) для 045; `status_view.py:298` + `report.py:949,1005,1038` для 044; `steps.py:199,230` и `doctor.py:954` для 040/042; `session.py:124-129` (`cli_session`, `report_ready`, `resets_at`) для 041/042/024; `records.py:270,523-525` (`previous_review`/`classes`/`verification`/`evidence`, `contract`) для 026/030/031; `complete.py:152,247` для 027; `report.py:58,437` и `brief.py:76-121` для 028; ADR-0022 §4 (строка 176-183) и §5 для 034/041/042; цитата в `ADR-0018:33` для 027. Остальные proposals проверил отдельно — ни один непротронутый файл не называет pending то, что отгружено (043 и 038 действительно не отгружены, индекс это же и говорит). Текст находок репортёров нигде не перезаписан: все правки — в секциях `## Where` или дата-помеченных нотах. Тесты, демонстрирующие описанное: `tests/test_unmeasured_session_usage.py` (044, включая `::test_an_unmeasured_sessions_recorded_cost_joins_the_per_currency_sums`), `tests/test_review_links_and_classes.py` (026/030/039), `tests/test_advisory_dispositions.py` + `tests/test_complete_dispositions.py` (027), `tests/test_contract_hash.py` + `tests/test_agree.py` (031), `tests/test_check.py` + `tests/test_brief_last_failing_check.py` (028), `tests/test_outbox.py` (029/045), `tests/test_journal_transaction.py` (019/032/035/040), `tests/test_status_schema_7_lines.py` (034/036). Самой прозы документации в этом репозитории не проверяет ни один тест — её «тест» это код, на который она ссылается.

**AC4 — границы и ссылки: выполнено** в проверяемой части. Diff трогает только `CHANGELOG.md`, `README.md`, `docs/proposals/` — всё в scope. Все новые relative-ссылки разрешаются: `ADR-0013`, `ADR-0015`, `ADR-0018`, `ADR-0021`, `ADR-0022` существуют в `docs/adr/`, `023-`, `029-`, `033-` — в `docs/proposals/`.

## Advisory

`ADV-016-dated-note-postdated` — в `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:71-74` дата-помеченная нота «## Later — 2026-09-18» отредактирована на месте и теперь говорит «since 0.5.0 it is kept under the clone's local state» — то есть нота от сентября несёт знание о релизе от 2026-10-23, без маркера поправки; при этом конвенция проекта (и этого же diff) — дописывать дату: 035 добавляет «- 2026-10-26: …», а 042 несёт «Amended the same day:». Новая `## Where` того же файла уже говорит то же самое, так что правка в ноте ещё и дублирующая.

`ADV-023-release-attribution` — в `docs/proposals/023-upstream-outbox-has-no-transaction.md:71-72` сказано «The documentation shipped in 0.4.0 — the README `init` writes into the outbox states the convention and says the outbox is not journal evidence», но README, который пишет `init`, и формулировка конвенции отгружены в 0.2.0 (`CHANGELOG.md:855`), а 0.4.0 добавил только «the generated upstream outbox says it is not evidence» (`CHANGELOG.md:613`). В том же diff 012 относит это к 0.2.0 — читатель получает две разные даты для одного факта. Disposition самого 023 («The README sentence and the pathspec ship first») говорит про sentence про not-evidence, а не про конвенцию.

Полную CI-последовательность (`uv sync --locked`, `agentmarshal validate`, `pytest`, `ruff`, `mypy`) я здесь не запускал — вызовы инструментов в этой read-only среде не прошли approval; опираюсь на заявление координатора, что она прошла на 4e1be0f.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4e1be0fbb5a04eb99229393d8d5002cf10047c63",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-016-dated-note-postdated", "ADV-023-release-attribution"],
  "classes": {
    "ADV-016-dated-note-postdated": "style",
    "ADV-023-release-attribution": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 60 src/agentmarshal/journal/records.py", "result": "records.py:2113-2124 — json.dumps + .encode() before _create_exclusive(path); the write/close after creation has no rollback, so CHANGELOG.md:247-253's narrowed promise holds"},
      {"what": "grep -rn 'level_for|CaptureClass\\.|resolve_session_disposition|may_commit_session_publicly|allow_public_sessions' src/ excluding journal/capture.py", "result": "no hits — only capture.py:259 reads a level, and it reads CaptureClass.REVIEWS; README's 'economics and sessions classes are not read' confirmed"},
      {"what": "sed -n '69,88p' src/agentmarshal/journal/capture.py", "result": "_PRESETS: minimal→REVIEWS OFF, attested→REVIEWS HASH, full→REVIEWS COMMIT; DEFAULT_PRESET='attested' — matches README.md:46-49"},
      {"what": "grep -rn 'records of other tasks|Records absent from|tokens=unmeasured|Reviewed commit|did not end|skipped as sent|step-started' src/", "result": "gate.py:2312, cli.py:1530, status_view.py:298/665/673, outbox.py:772, steps.py:199,230 — each string the updated Where sections name exists"},
      {"what": "grep -n 'advisory_dispositions|previous_review|verification|evidence|contract|implementers|independence' src/agentmarshal/journal/complete.py src/agentmarshal/journal/records.py src/agentmarshal/journal/contracts.py", "result": "complete.py:152,247; records.py:223,270,523-525; contracts.py:30-32,202-239 — the schema-7 fields 026/027/030/031/034 claim are present"},
      {"what": "grep -n 'unmeasured' src/agentmarshal/journal/report.py", "result": "report.py:949 (Cost line, unmeasured_without_cost), 1005 (task line), 1038 (Summary) — 044's three-line claim and the 'a cost still sums' clause hold"},
      {"what": "grep -n 'upstream' CHANGELOG.md", "result": "line 855 (inside 0.2.0, headings at 713/876): 'init creates .agentmarshal/upstream/ with a README stating the convention'; line 613 (inside 0.4.0): 'the generated upstream outbox says it is not evidence' — basis of ADV-023-release-attribution"},
      {"what": "ls docs/adr/ | grep -E '0009|0013|0015|0018|0021|0022'; ls docs/proposals/", "result": "every ADR and proposal file the new links name exists; all relative links in the diff resolve"},
      {"what": "grep -rn 'not shipped|undecided|not yet shipped|to be written|pending' docs/proposals/*.md excluding the files the diff touches", "result": "only 043 (lines 99-127) and 038 — both of which docs/proposals/README.md:154 and :157 also record as not shipped; AC3's coverage is complete"},
      {"what": "sed -n '443,470p' tests/test_record_text_safety.py", "result": "test_a_failure_while_encoding_leaves_no_file asserts UnicodeEncodeError and 'not journal_root.exists()' — the test behind AC1"}
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-243/contract.md",
      "CHANGELOG.md (0.6.0 section, 0.4.0 and 0.2.0 entries)",
      "README.md:30-60",
      "src/agentmarshal/journal/records.py (write_record, schema field sets)",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/journal/review.py (_keep_accepted_output, prose level handling)",
      "src/agentmarshal/journal/submit_review.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/complete.py",
      "src/agentmarshal/cli.py (complete's pre-gate-stop path, outbox/--index, --if-missing)",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/steps.py",
      "src/agentmarshal/outbox.py",
      "templates/github/agentmarshal-governance.yml",
      "templates/journal-transaction.sh",
      "docs/proposals/README.md",
      "docs/proposals/009, 016, 019, 023, 038, 042, 043",
      "docs/adr/ADR-0009, ADR-0013, ADR-0015, ADR-0018, ADR-0022",
      "tests/test_capture.py, tests/test_review_capture.py, tests/test_record_text_safety.py, tests/test_unmeasured_session_usage.py, tests/test_review_links_and_classes.py, tests/test_status_schema_7_lines.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "this read-only review environment refused the tool invocations (command approval denied); the coordinator states the full sequence passed on 4e1be0fbb5a04eb99229393d8d5002cf10047c63, so AC4's 'the suite and the full CI sequence pass' is taken from that statement rather than from my own run"}
    ]
  },
  "evidence": {
    "ADV-016-dated-note-postdated": "docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:68-78 — the note headed '## Later — 2026-09-18' now reads 'since 0.5.0 it is kept under the clone's local state, announced by a review-prose event', post-dating a dated note with no amendment marker; contrast docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md:107 ('- 2026-10-26: the rest shipped in 0.6.0 …') and 042's pre-existing 'Amended the same day:' convention, and 016's own new '## Where' (lines 80-86) which already states the same move",
    "ADV-023-release-attribution": "docs/proposals/023-upstream-outbox-has-no-transaction.md:71-72 attributes 'the README init writes into the outbox states the convention' to 0.4.0, but CHANGELOG.md:855 places it in 0.2.0 ('init creates .agentmarshal/upstream/ with a README stating the convention for sending findings upstream') while CHANGELOG.md:613 shows 0.4.0 added only 'the generated upstream outbox says it is not evidence'; docs/proposals/012-upstream-feedback-channel.md:39-40 in the same diff says 0.2.0 for the same artifact"
  }
}
AGENTMARSHAL_VERDICT_END
