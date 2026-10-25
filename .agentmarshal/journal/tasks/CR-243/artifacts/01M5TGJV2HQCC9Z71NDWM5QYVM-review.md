Проверку закончил: прочитал код за каждым утверждением диффа, сверил «Where»-секции с `docs/proposals/README.md` и прошёлся по всем изменённым ссылкам.

**Что найдено (оба — advisory, не блокирующие):**

- **AUD-REV-1** — `docs/proposals/009-lifecycle-extension-points.md:91`: новая «Where» утверждает, что «"After open" and a `pre-complete` remain stages nobody has asked for», но раздел «Proposed» того же файла (строка 19) просит ровно их: «Defined lifecycle hooks (a `post-open` / `pre-complete` boundary)». Соседняя, более ранняя disposition сформулирована аккуратно — «the two boundaries the report names are not among the two stages — "after open" waits on an adopter's request» — а новая строка искажает запись о том, что просил репортёр. 009 не входит в перечень критерия 3, так что это не срыв acceptance, но фраза документирует прошлое неверно.
- **AUD-REV-2** — `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:72`: правка вставлена внутрь датированной заметки «## Later — 2026-09-18» («…at the time in a local temporary file…; since 0.5.0 it is kept under the clone's local state»), и тот же факт затем повторён в новой «## Where» (строка 78). В остальных файлах проекта (019 «Where — 2026-10-24», 035 с датированными bullet'ами) поздние факты дописываются отдельной датированной записью, а не переписывают более раннюю; здесь получилось и изменение датированной заметки, и дубль.

**Критерии приёмки — где дифф их выполняет и чем это показано:**

1. **CHANGELOG, обещание write-time (AUD-docs-claims-1-1)** — выполнен. `CHANGELOG.md:245-251` теперь обещает только «an encoding or serialization failure — leaves no record file behind; a failure while writing or closing the created file is not rolled back», и это ровно то, что делает `src/agentmarshal/journal/records.py:2113-2125`: `json.dumps` + `.encode()` до `_create_exclusive(path)`, а `record_file.buffer.write(body)` после создания файла ничем не откатывается. Демонстрирует тест `tests/test_record_text_safety.py:444` `test_a_failure_while_encoding_leaves_no_file` (непарный surrogate в `outcome` → `UnicodeEncodeError`, `assert not journal_root.exists()`). Более широкого обещания в CHANGELOG/README больше нет (grep по «partial record», «no empty or partial»).
2. **README, capture-политика (AUD-docs-claims-1-2)** — выполнен. Слово «inactive» убрано, и каждое новое утверждение сходится с кодом: таблица presets `src/agentmarshal/journal/capture.py:69-88` даёт `attested→HASH`, `full→COMMIT`, `minimal→OFF` для `REVIEWS`; override читается в `capture.py:250-260` (`level_for(CaptureClass.REVIEWS)`); `commit` пинит прозу артефактом (`review.py:1595` → `submit_review.py:144` `write_artifact`), `hash` кладёт её в local state с событием `review-prose` (`review.py:711-742`), `off` не хранит ничего (`review.py:1621`). Названное как «всё ещё roadmap» тоже верно: `CaptureClass.ECONOMICS`/`SESSIONS` нигде вне `capture.py` не читаются, а `attestation.py:21` сам говорит «This module owns the declaration; it emits no Statement». Демонстрируют `tests/test_review_capture.py:153,195,225,248` (`..._comes_from_the_sidecar_project`, `test_by_default_the_prose_stays_out_of_the_journal`, `test_commit_keeps_todays_behaviour`, `test_off_keeps_nothing`).
3. **Статусы проposals (AUD-docs-claims-1-3)** — выполнен. Все 19 названных файлов (012, 024–032, 034, 036, 037, 039–042, 044, 045) обновлены, плюс 009, 016, 018, 020, 023, 035 — и каждая новая «Where» совпадает и с индексом, и с кодом: `SENT` + `skipped as sent: <n>` (`outbox.py:15,65,772`, `--index` на `check`/`send`/`status` — `outbox.py:122-146`) → `tests/test_outbox.py`; `tokens=unmeasured` (`status_view.py:298`) и `unmeasured=<n>` на task/Summary/Cost (`report.py:1005,1038,949`) → `tests/test_unmeasured_session_usage.py`; `Records absent from <base>` (`cli.py:1530`) и предупреждение гейта «candidate adds opened/amendment records of other tasks» (`gate.py:2312`) → `tests/test_status_base.py`; строка `Reviewed commit <sha7>: implementer session <id>` с пометкой `(did not end 'implemented')` (`status_view.py:663-676`) → `tests/test_status_view.py`; `advisory_dispositions` и открытые deferral'ы (`CHANGELOG.md:339-349`, `status_view.py:584`) → `tests/test_status_count_deferrals.py`; `report --findings` по классам (`cli.py:486-489`, `report.py:232,802-805`) и счёт `failed`/`error` (`report.py:58,437`) → `tests/test_review_links_and_classes.py`; `brief` с последней упавшей проверкой и «A later check of the same name passed» (`brief.py:76,121`); `resets_at`/`cost {amount,currency,source}`/`cli_session`/`report_ready`/`started_at`/`ended_at` (`CHANGELOG.md:374-383`, `session.py:45-149`); словарь outcome'ов в ADR-0022 §4 (`ADR-0022…md:176-182`) для 034/041/042; helper, который ветвится по задаче и всё ещё переключает рабочее дерево (`templates/journal-transaction.sh:115-116` `git switch -c "journal/$task-$slug"`), что подтверждает и «shipped» в 032, и «не shipped» checkout-free write в 040. Разделение shipped/deferred сохранено, исходные finding-тексты не переписаны, а детали, убранные из «Where» (Apache-2.0 канал в 042, plan-файл и adopter kit в 041, ADR-0010 в 039), остались в их Disposition-секциях и в header-строке disposition. Непокрытых устаревших статусов не осталось: по неизменённым файлам стоят только 043 и 038, и индекс для них тоже говорит «not shipped yet», а 019 уже был актуален («Where — 2026-10-24»).
4. **Прочее (no other file changes; links; CI)** — выполнен в проверяемой части. Дифф трогает только `CHANGELOG.md`, `README.md` и `docs/proposals/` — всё внутри scope. Все новые ссылки существуют: `ADR-0013`, `ADR-0015`, `ADR-0018`, `ADR-0021`, `ADR-0022` в `docs/adr/`, и `023-…`, `029-…`, `033-…` в `docs/proposals/`. Полную CI-последовательность я не запускал (read-only snapshot без git/uv); по заявлению координатора она зелёная на этом коммите, и изменения — только документация, тестов на содержимое CHANGELOG/README/proposals в `tests/` нет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4e1be0fbb5a04eb99229393d8d5002cf10047c63",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["AUD-REV-1", "AUD-REV-2"],
  "classes": {
    "AUD-REV-1": "claim-accuracy",
    "AUD-REV-2": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 70 src/agentmarshal/journal/records.py", "result": "lines 2113-2125: json.dumps then .encode() before _create_exclusive(path); record_file.buffer.write(body) after creation is not rolled back — the narrowed CHANGELOG promise holds"},
      {"what": "sed -n '1,130p' src/agentmarshal/journal/capture.py", "result": "_PRESETS: minimal→OFF, attested→HASH, full→COMMIT for CaptureClass.REVIEWS; DEFAULT_PRESET = 'attested'"},
      {"what": "grep -rn 'CaptureClass.ECONOMICS|CaptureClass.SESSIONS' src/ | grep -v capture.py", "result": "no hits — the economics and sessions classes are read nowhere else, as README now says"},
      {"what": "grep -n 'CaptureLevel' src/agentmarshal/journal/review.py", "result": "1595 COMMIT→prose artifact, 1619 HASH→_keep_accepted_output, 1621 OFF→'reviewer prose was not kept'"},
      {"what": "grep -rn 'review-prose' src/", "result": "review.py:715,727 — event written for the hash level; capture.py:251"},
      {"what": "grep -rn 'Statement|in-toto' src/agentmarshal/journal/attestation.py", "result": "line 21: 'This module owns the declaration; it emits no Statement'"},
      {"what": "grep -n '^## ' CHANGELOG.md", "result": "0.6.0 at 11, 0.5.0 at 280, 0.4.1 at 483, 0.4.0 at 519, 0.3.0 at 626, 0.2.0 at 713 — used to place every 'shipped in X' claim"},
      {"what": "grep -n 'coordination|advisory_dispositions|previous_review|changes_required|resets_at|report_ready|cli_session|started_at|independence|verification|acknowledgement' CHANGELOG.md", "result": "all in the 0.5.0 section (301-444); coordination at 601 → 0.4.0; init's .agentmarshal/upstream/ at 855 → 0.2.0"},
      {"what": "grep -n 'SENT|skipped as sent' src/agentmarshal/outbox.py", "result": "15, 65 (_SENT = 'SENT'), 772 print('skipped as sent: {skipped}'); --index on check/send/status at 122-146"},
      {"what": "grep -rn 'tokens=unmeasured|unmeasured=' src/agentmarshal/journal/{status_view,report}.py", "result": "status_view.py:298 tokens=unmeasured; report.py:949,1005,1038 unmeasured= on Cost, task and Summary lines"},
      {"what": "grep -rn 'Records absent from|records of other tasks|did not end' src/", "result": "cli.py:1530/1538, gate.py:2312, status_view.py:663-676 — 035 and 036 claims confirmed"},
      {"what": "grep -n 'branch|checkout|switch' templates/journal-transaction.sh", "result": "115-116 branch=journal/$task-$slug; git switch -c — branches per task and still switches the working tree (032 and 040)"},
      {"what": "grep -n 'output-limit|safety-limit|time-limit|stalled' docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md and its headings", "result": "lines 181-182 inside '### 4. The session outcome vocabulary' — 034, 041, 042 citations correct"},
      {"what": "ls docs/adr/ | grep -E '0013|0015|0018|0021|0022' and ls docs/proposals/", "result": "every ADR and proposal target the diff links to exists; no broken relative link among the added ones"},
      {"what": "grep -n 'not shipped|not yet|undecided|to be written|pending|will say so in its changelog' over the proposals the diff did not touch", "result": "only 003, 004, 009:49, 019 (dated note followed by a current Where), 038 and 043 — each matching the status docs/proposals/README.md gives, so no stale status was left behind"},
      {"what": "grep -rn 'def test' tests/test_review_capture.py; sed -n '440,470p' tests/test_record_text_safety.py", "result": "test_a_failure_while_encoding_leaves_no_file asserts not journal_root.exists(); capture tests cover hash/commit/off and the sidecar project"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 and 0.5.0 sections, lines 11-280 and 280-450)",
      "README.md (the ADR-0004/0005 roadmap bullet)",
      "docs/proposals/README.md (all batch tables)",
      "docs/proposals/009-lifecycle-extension-points.md",
      "docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md",
      "docs/proposals/019-journal-transactions-assume-direct-commits.md",
      "docs/proposals/043-review-before-integration-makes-every-merge-stale.md",
      "src/agentmarshal/journal/records.py (write_record, _minimum_schema, contract field)",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/journal/review.py (prose capture branches)",
      "src/agentmarshal/journal/submit_review.py (prose pin)",
      "src/agentmarshal/journal/report.py, status_view.py, brief.py",
      "src/agentmarshal/outbox.py, steps.py, stages.py",
      "templates/journal-transaction.sh, templates/github/agentmarshal-governance.yml",
      "docs/adr/ADR-0009-research-findings-lifecycle.md, ADR-0013, ADR-0015, ADR-0018, ADR-0021, ADR-0022",
      "tests/test_record_text_safety.py, tests/test_review_capture.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review of a snapshot without a git repository or a provisioned uv environment; the coordinator states the sequence passed on this commit and the diff is documentation only"},
      {"what": "a link checker script over all docs", "why": "running a local python script was not permitted in this sandbox; the added links were instead checked by listing docs/adr/ and docs/proposals/"}
    ]
  },
  "evidence": {
    "AUD-REV-1": "docs/proposals/009-lifecycle-extension-points.md:91 'nobody has asked for — new stages are added at an adopter's request' against the same file's line 19 'Defined lifecycle hooks (a `post-open` / `pre-complete` boundary)' and line 76 'waits on an adopter's request, and there is no `pre-complete`'",
    "AUD-REV-2": "docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:72 inserts 'since 0.5.0 it is kept under the clone's local state' inside the dated '## Later — 2026-09-18' note (line 65), and lines 78-84 restate the same fact in the new '## Where'; compare docs/proposals/019-journal-transactions-assume-direct-commits.md:60-66 and 035's dated bullet, where later facts are appended as dated entries instead"
  }
}
AGENTMARSHAL_VERDICT_END
