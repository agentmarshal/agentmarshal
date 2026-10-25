Проверку закончил. Ниже — прозой по каждому критерию и по двум advisory-находкам.

## Критерий 1 — обещание CHANGELOG о write-time fix

Выполнен. Новый текст в `CHANGELOG.md:245-251` говорит ровно то, что держит код: `write_record` сериализует и кодирует запись в байты (`records.py:2113-2117`) до `_create_exclusive(path)` (`records.py:2120`), поэтому падение на этом шаге не оставляет файла, а падение внутри `with record_file: record_file.buffer.write(body)` ничем не откатывается — в функции нет cleanup-ветки. Прежняя формулировка «a failed write leaves no empty or partial record behind» убрана. Демонстрирует это `tests/test_record_text_safety.py::test_a_failure_while_encoding_leaves_no_file` (строка 444): непарный surrogate в свободнотекстовом `outcome` проходит валидацию, падает на encode, и тест утверждает `not journal_root.exists()`.

## Критерий 2 — README про capture policy

Выполнен. `README.md:43-54`: фраза «They remain inactive in 0.6.0» убрана, review-класс назван как shipped, нешипнутое названо отдельно. Каждое утверждение сходится с кодом: `capture.overrides.reviews` читается через `capture.py:250-259` → `level_for(CaptureClass.REVIEWS)`, вызовы только в `cli.py:694` и `review.py:1780`; `commit` пинит прозу как journal artifact (`review.py:1595`), `hash` — default пресета `attested` (`capture.py:78`) и кладёт байты в local state с событием `review-prose` (`review.py:711-742`), `off` не хранит ничего (`review.py:1621-1622`); `economics` и `sessions` действительно не читаются — `resolve_session_disposition`/`may_commit_session_publicly` не имеют вызывающих в `src/`; `attestation.py:21` сам говорит «it emits no Statement». Демонстрируют: `tests/test_review_capture.py::test_by_default_the_prose_stays_out_of_the_journal`, `::test_commit_keeps_todays_behaviour`, `::test_off_keeps_nothing`, плюс `tests/test_capture.py::test_preset_resolved_levels`.

## Критерий 3 — статусные строки proposals

Выполнен. Диффом закрыты все перечисленные в контракте (012, 024, 025, 026, 027, 028, 029, 030, 031, 032, 034, 036, 037, 039, 040, 041, 042, 044, 045) плюс 009, 018, 020, 023, 035 — «at least» это допускает. Каждое новое Where я сверял и с `docs/proposals/README.md`, и с кодом: `advisory_dispositions` в `complete` (`cli.py:366-379`, `complete.py:112-152`) и открытые deferrals в `status` (`status_view.py:584-601`) для 027; `check`-запись, «gate ничего из неё не решает» (в `gate.py` нет чтения `check`-записей) и `report` по `failed`/`error` (`report.py:437-448`), `brief`'s «Last failing check» (`brief.py:75-96`) для 028; `verification` для 030 (`records.py:1166-1183`); contract-hash всегда пишется в `opened`/`amendment` (`open_task.py:400-411`, `cli.py:1310-1312`) и есть `agentmarshal agree` (`agree.py`, `cli.py:534`) для 031; lead time и фазы в `report` (`report.py:363-366,700`) и «branches per task» (`templates/journal-transaction.sh:115-116`, он же всё ещё `git switch` — как 040 и говорит) для 032/035/040; словарь outcome'ов для 041/042/034 — ровно пять значений в `ADR-0022` §4 (строки 176-184); `Reviewed commit <sha7>: implementer session <id>` и `Records absent from <base>` (`cli.py:1530`) и warning `candidate adds opened/amendment records of other tasks` (`gate.py:2312`) для 036/035; `tokens=unmeasured` (`status_view.py:297-298`) для 044; `SENT` и `skipped as sent: <n>` (`outbox.py:65,772`) для 045. Текст findings нигде не переписан — правки только в Where/дисположных хвостах; в 042 выброшенный из Where абзац про Apache-2.0-маршрут сохранён выше, в самой дисположции (строки 164-174). Отдельных тестов на прозу proposals в репозитории нет; поведение, на которое ссылаются Where, покрывают `tests/test_advisory_dispositions.py`, `test_complete_dispositions.py`, `test_status_count_deferrals.py`, `test_brief_last_failing_check.py`, `test_review_verification_and_evidence.py`, `test_contract_hash.py`, `test_agree.py`, `test_acknowledge.py`, `test_report_lead_time.py`, `test_journal_transaction.py`, `test_status_candidate_session.py`, `test_status_base.py`, `test_steps.py`, `test_unmeasured_session_usage.py`, `test_outbox.py`.

## Критерий 4 — прочее

Файлы диффа — только `CHANGELOG.md`, `README.md`, `docs/proposals/*` — все внутри scope. Все добавленные ссылки разрешаются: `docs/adr/ADR-0013/0015/0018/0021/0022` существуют, как и `023-…`, `029-…`, `033-…`. Полную CI-последовательность я не запускал (read-only review); по заявлению координатора она прошла на этом коммите.

## Advisory-находки

`ADV-records-write-comment-overclaim` — комментарий в `src/agentmarshal/journal/records.py:2114-2116` всё ещё несёт ту самую расширенную формулировку, которую дифф сузил в CHANGELOG: «so an exclusive create can never leave an empty or partial record behind». Падение внутри `buffer.write`/закрытия оставляет частичный файл, так что в исходнике сужения нет — только в release-документации. `src/` вне scope контракта, так что это follow-up/departure, а не правка здесь.

`ADV-016-hash-prose-location-stale` — датированная заметка «Later — 2026-09-18» в `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:68-74` до сих пор пишет, что на уровне `hash` вывод остаётся «in a local temporary file whose path the command prints». С 0.5.0 (`CHANGELOG.md:414-416`) проза живёт в local state с событием `review-prose`, а temp-файл — только fallback (`review.py:711-742`); этим же диффом README начинает описывать это по-новому, так что 016 теперь ему противоречит. Под букву критерия 3 не попадает (строка не говорит «pending»), файл в scope — потому advisory.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "1952617a1386647ee04f46bd06b0fbce69eb3779",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-records-write-comment-overclaim",
    "ADV-016-hash-prose-location-stale"
  ],
  "classes": {
    "ADV-records-write-comment-overclaim": "claim-accuracy",
    "ADV-016-hash-prose-location-stale": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 80 src/agentmarshal/journal/records.py", "result": "encode at 2113-2117 precedes _create_exclusive at 2120; no cleanup around buffer.write — CHANGELOG's narrowed claim holds"},
      {"what": "grep -rn 'level_for|CaptureClass\\.|review_capture_level_from_journal' --include=*.py src/", "result": "level_for reached only for REVIEWS (capture.py:259) from cli.py:694 and review.py:1780; resolve_session_disposition/may_commit_session_publicly have no callers in src/"},
      {"what": "grep -n 'CaptureLevel.OFF|COMMIT|HASH' src/agentmarshal/journal/review.py", "result": "1595 commit pins prose; 1619 hash -> _keep_accepted_output (local state + review-prose event); 1621 off -> 'reviewer prose was not kept'"},
      {"what": "grep -n 'Statement' src/agentmarshal/journal/attestation.py", "result": "line 21: 'This module owns the declaration; it emits no Statement.'"},
      {"what": "grep -rn 'not shipped yet|Nothing here is shipped|to be written|not yet decided' docs/proposals/*.md", "result": "remaining occurrences are inside historical Disposition sections only; 038/043 Where legitimately pending per the index"},
      {"what": "sed -n '176,205p' docs/adr/ADR-0022-...md", "result": "section 4 lists provider-limit, output-limit, stalled, safety-limit, time-limit — matches proposals 041/042/034"},
      {"what": "grep -rn 'records of other tasks|absent from' src/agentmarshal/journal/gate.py src/agentmarshal/cli.py", "result": "gate.py:2312 'WARN: candidate adds opened/amendment records of other tasks'; cli.py:1530 'Records absent from {base}:' — proposal 035's quoted strings are exact"},
      {"what": "grep -n 'SENT|skipped as sent|--index' src/agentmarshal/outbox.py", "result": "_SENT='SENT' (65), 'skipped as sent: {skipped}' (772), --index on check/send/status — proposal 045 accurate"},
      {"what": "sed -n '444,470p' tests/test_record_text_safety.py", "result": "test_a_failure_while_encoding_leaves_no_file asserts UnicodeEncodeError and not journal_root.exists()"},
      {"what": "grep -n 'def test_' tests/test_review_capture.py", "result": "tests for hash default, commit, off — the three README levels"},
      {"what": "ls docs/adr/ and docs/proposals/", "result": "every ADR and proposal target added by the diff exists (ADR-0013/0015/0018/0021/0022, 023, 029, 033)"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0, 0.5.0, 0.4.0, 0.2.0 sections)",
      "README.md:28-67",
      "docs/proposals/README.md",
      "docs/proposals/009, 012, 016, 019, 029, 033, 038, 042, 043",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/journal/review.py (prose keeping, launch paths)",
      "src/agentmarshal/journal/report.py, brief.py, status_view.py, complete.py, gate.py (targeted sections)",
      "src/agentmarshal/cli.py (subparsers, complete flags, status --base)",
      "src/agentmarshal/outbox.py, steps.py, agree.py registration",
      "templates/journal-transaction.sh",
      "docs/adr/ADR-0022 sections 4 and 5, ADR-0009 decision headings"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; the coordinator states the full sequence passed on this commit"},
      {"what": "repo-wide markdown link resolution script", "why": "python execution was not approved in this session; the links the diff adds were checked individually against docs/adr/ and docs/proposals/ listings"}
    ]
  },
  "evidence": {
    "ADV-records-write-comment-overclaim": "src/agentmarshal/journal/records.py:2114-2116 — 'Encode before the file exists: ... so an exclusive create can never leave an empty or partial record behind.' contrasted with records.py:2123-2124 (`with record_file: record_file.buffer.write(body)`, no rollback) and the narrowed CHANGELOG.md:247-250",
    "ADV-016-hash-prose-location-stale": "docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:68-74 ('in a local temporary file whose path the command prints') vs CHANGELOG.md:414-416 ('At capture level `hash` a review's prose and diagnostics are kept under the local state and announced by `review-prose`/`review-diagnostics` events instead of sitting in temporary files', 0.5.0) and src/agentmarshal/journal/review.py:711-742"
  }
}
AGENTMARSHAL_VERDICT_END
