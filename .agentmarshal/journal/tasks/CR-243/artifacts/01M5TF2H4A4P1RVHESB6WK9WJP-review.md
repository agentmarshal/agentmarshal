Проверил весь diff против кода, ADR'ов, CHANGELOG'а и индекса пропозалов. Итог: все три содержательных критерия выполнены, блокирующих находок нет; три advisory-замечания.

**По критериям приёмки**

- **AC1 (CHANGELOG, write-time fix)** — выполнен. `CHANGELOG.md:247-251` теперь обещает ровно то, что держит код: `src/agentmarshal/journal/records.py:2107-2125` делает `json.dumps` + `.encode()` до `_prepare_record_directory`/`_create_exclusive`, а запись в уже созданный файл (`with record_file: record_file.buffer.write(body)`) не откатывается — именно это и сказано. Демонстрирует `tests/test_record_text_safety.py::test_a_failure_while_encoding_leaves_no_file` (непарный сурrogate в `outcome` → `UnicodeEncodeError`, `assert not journal_root.exists()`). Орфография `serialization` совпадает с остальным CHANGELOG (строка 62).
- **AC2 (README, capture policy)** — выполнен. Фраза «They remain inactive in 0.6.0» убрана; review-класс назван отработавшим, а неотгруженное (`economics`, `sessions`, приватный store, attestation-проекция) названо отдельно. Проверено: `review_capture_level_from_journal` — единственный читатель политики (`src/agentmarshal/journal/capture.py:250-259`), вызывается из `src/agentmarshal/cli.py:694` и `src/agentmarshal/journal/review.py:1780`; ветки уровней — `review.py:1595` (commit → артефакт журнала через `submit_review.py:144 write_artifact`), `1619` (hash → local state + событие `review-prose`, `review.py:715-743`), `1621` (off → ничего); `resolve_session_disposition`/`may_commit_session_publicly`/`level_for` вне capture.py не вызываются нигде, т.е. `economics`/`sessions` действительно не читаются; `attestation.py:21` — «it emits no Statement». Демонстрирует `tests/test_review_capture.py` (`test_by_default_the_prose_stays_out_of_the_journal`, `test_commit_keeps_todays_behaviour`, `test_off_keeps_nothing`, `test_a_sidecar_keeps_the_prose_in_the_journal_repositorys_local_state`).
- **AC3 (Where-строки пропозалов)** — выполнен. Обновлены все требуемые (012, 024–032, 034, 036, 037, 039–042, 044, 045) плюс 009, 016, 018, 020, 023, 035; исходный текст находок нигде не переписан — правки только в секциях «Where»/датированных заметках, а «Accepted; not shipped yet» остались как исторические диспозиции, что соответствует конвенции репозитория. Все заявления сверены с кодом/ADR: `Records absent from <base>` (`cli.py:1530`, тест `tests/test_status_base.py`), `candidate adds opened/amendment records of other tasks` (`gate.py:2312`, `tests/test_gate.py`), `skipped as sent: <n>` и манифест `SENT` (`outbox.py:65,772`, `tests/test_outbox.py`), `tokens=unmeasured`/`unmeasured=<n>` (`status_view.py:298`, `report.py:949-964,1038`, `tests/test_unmeasured_session_usage.py`), `advisory_dispositions` (`complete.py:120-152`, `tests/test_complete_dispositions.py`), `previous_review`/`classes`/`report --findings` (`review.py:1404`, `report.py:232-234,1061-1077`, `tests/test_review_links_and_classes.py`), `verification` с `executed/read/not_run` (`records.py:277-280`, `tests/test_review_verification_and_evidence.py`), хэш контракта в `opened`/`amendment` и `agentmarshal agree` (`records.py:523-525`, `agree.py:59`, `tests/test_contract_hash.py`, `tests/test_agree.py`), `report_ready`/`cli_session`/`resets_at` (`session.py:124-129`, `tests/test_session.py`), `Reviewed commit <sha7>: implementer session <id>` + `(did not end 'implemented')` (`status_view.py:665,673`, `tests/test_status_candidate_session.py`), «the gate decides nothing from a `check` record» (ADR-0017 решение 2), `step-started`/`step-ended` (`steps.py:199`, `tests/test_steps.py`), транзакционный хелпер ветвится и всё ещё переключает рабочее дерево (`templates/journal-transaction.sh:115-116`), `pre-gate`/`post-gate`/режимы (`stages.py:209-213`, ADR-0013 A.2–A.4), вокабуляр `output-limit/stalled/safety-limit/time-limit` — только документация (ADR-0022 §4: «`outcome` still accepts any non-empty string»), `agentmarshal next` и plan-файл отсутствуют в CLI. Строка 012 про скаффолд в 0.2.0 подтверждается `CHANGELOG.md:855` и текстом самой 029. Противоречий с ADR-0009 нет.
- **AC4 (ничего лишнего, ссылки, CI)** — выполнен в части, которую можно проверить чтением: diff трогает только `CHANGELOG.md`, `README.md`, `docs/proposals/`; все новые относительные ссылки существуют (`docs/adr/ADR-0013/0015/0018/0021/0022`, `023-…`, `029-…`, `033-…`). Полную CI-последовательность я не запускал (read-only снапшот без git); по заявлению координатора она зелёная на d22abe79.

**Advisory-находки**

- `ADV-readme-capture-preset` — в `README.md:44-47` сказано, что читается `capture.overrides.reviews`, а `hash` назван «the default»; на самом деле уровень берётся из таблицы пресетов (`capture.py:68-87`: `attested`→hash, `full`→commit, `minimal`→off), а override лишь перебивает её (`capture.py:140-151`). Читатель, выставивший `preset = "full"` без override, из README не поймёт, что проза начнёт коммититься в журнал.
- `ADV-045-index-command` — в `docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:107-109` пропуск уже отправленных файлов приписан «the index `outbox status` takes», но пропуск читает индекс в `check`/`send` (`outbox.py:122-137` — `--index` у `check` и `send`; `CHANGELOG.md:191-193`), а индекс самого индекса пропозалов говорит «an index passed to `check`, `send` or `status`»; формулировка осталась от исходного плана, но теперь подана как отгруженный факт.
- `ADV-changelog-wrap` — в `CHANGELOG.md:251` после правки остался недоперенесённый обрывок строки «And the reviewer output kept on a refused» (~41 символ при общей ширине абзаца ~66); абзац стоило перевернуть заново, как остальной файл.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "d22abe79214e9480369dbab3eb51d89e7208b154",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-readme-capture-preset", "ADV-045-index-command", "ADV-changelog-wrap"],
  "classes": {
    "ADV-readme-capture-preset": "claim-accuracy",
    "ADV-045-index-command": "claim-accuracy",
    "ADV-changelog-wrap": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 80 src/agentmarshal/journal/records.py", "result": "lines 2107-2125: validate, json.dumps, f-string .encode() all precede _prepare_record_directory/_create_exclusive; the write inside `with record_file:` has no unlink on failure — CHANGELOG's narrowed promise matches"},
      {"what": "grep -rn 'REVIEWS|level_for|ECONOMICS|SESSIONS' src/agentmarshal --include=*.py (excluding capture.py)", "result": "no hits — level_for is reached only through review_capture_level_from_journal(CaptureClass.REVIEWS); economics and sessions are not read"},
      {"what": "grep -rn 'resolve_session_disposition|may_commit_session_publicly|capture_policy_from_project|allow_public_sessions' src/agentmarshal --include=*.py (excluding journal/capture.py)", "result": "no hits"},
      {"what": "grep -n 'CaptureLevel' src/agentmarshal/journal/review.py", "result": "1595 commit->prose artifact, 1619 hash->_keep_accepted_output (review-prose event, local state), 1621 off->'reviewer prose was not kept'"},
      {"what": "grep -rn 'Records absent from|candidate adds opened/amendment|skipped as sent|tokens=unmeasured|cli_session|report_ready|advisory_dispositions|resets_at|previous_review|step-started' src/agentmarshal", "result": "all present: cli.py:1530, gate.py:2312, outbox.py:772, status_view.py:298, session.py:124-129, complete.py:152, review.py:1404, steps.py:199"},
      {"what": "grep -n 'changes_required' src/agentmarshal/journal/gate.py src/agentmarshal/journal/status_view.py", "result": "gate.py:2440-2452 and status_view.py:524-556 both print the count — 026 and 039 hold"},
      {"what": "grep -n '^## ' CHANGELOG.md plus greps for cli_session/report_ready/step start/undecodable/review-prose/resets_at/Reviewed commit/coordination/init creates .agentmarshal/upstream", "result": "0.6.0=11-279, 0.5.0=280-482, 0.4.1=483-518, 0.4.0=519-625, 0.2.0=713-875; hits at 379/408/416/442/377 (0.5.0), 165/191/198 (0.6.0), 601 (0.4.0), 855 (0.2.0) — every release attribution in the diff lands in the right section"},
      {"what": "grep -n '^### ' docs/adr/ADR-0022-...md; grep -n 'output-limit|stalled|safety-limit|time-limit' on it", "result": "section 4 is 'The session outcome vocabulary' at line 176; 181-182 list the values and state outcome still accepts any non-empty string — the proposals' wording ('stands in the vocabulary the ADR documents') is exact"},
      {"what": "grep -n 'The gate decides nothing from a `check` record' docs/adr/ADR-0017-...md", "result": "line 69 — proposal 028's claim confirmed"},
      {"what": "grep -n 'automates no per-finding status' docs/adr/ADR-0016-...md", "result": "line 201 — proposal 026's wording confirmed"},
      {"what": "sed -n 60,82p docs/adr/ADR-0013-...md; grep -n 'pre-gate' src/agentmarshal/stages.py", "result": "ADR A.2-A.4 give pre-gate/post-gate as stages and pre-gate-warn/pre-gate-stop as modes; stages.py:212-213 and the CLI choices (284) agree — 'after open' is a candidate awaiting an adopter, no pre-complete"},
      {"what": "grep -n 'add_parser(' across src/agentmarshal", "result": "agree, acknowledge, outbox new/check/send/status, record-check, step start/end, stage run, extension ... — no `next` subcommand, matching proposal 041"},
      {"what": "grep -n 'checkout|switch|branch' templates/journal-transaction.sh", "result": "git switch -c \"journal/$task-$slug\" at 115-116 — proposals 032 and 040 are both right (branches per task, still switches the tree)"},
      {"what": "ls docs/adr/ docs/proposals/ and matching of every relative link target in the diff", "result": "ADR-0013/0015/0018/0021/0022 and 023/029/033 proposal files all exist; no broken target among the diff's links"},
      {"what": "grep -rln for the claimed output strings in tests/", "result": "tests/test_status_base.py, tests/test_outbox.py, tests/test_unmeasured_session_usage.py, tests/test_gate.py, tests/test_review_capture.py, tests/test_record_text_safety.py pin the behaviours the new prose describes"},
      {"what": "sed -n 240,258p CHANGELOG.md | cat -A", "result": "line 251 'And the reviewer output kept on a refused' is ~41 chars inside a ~66-char-wrapped paragraph — the orphan line of ADV-changelog-wrap"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 and 0.5.0 sections, 0.4.0/0.2.0 attributions)",
      "README.md (design-docs bullet list and Status section)",
      "docs/proposals/README.md (full index, every Where column cited by the diff)",
      "docs/proposals/009, 012, 016, 019, 023, 029, 042, 045 (full bodies)",
      "src/agentmarshal/journal/records.py (write_record, _minimum_schema, verification/contract field rules)",
      "src/agentmarshal/journal/capture.py (presets, CapturePolicy, review_capture_level_from_journal)",
      "src/agentmarshal/journal/review.py (_keep_accepted_output, capture-level branching)",
      "src/agentmarshal/journal/submit_review.py (prose artifact pin)",
      "src/agentmarshal/journal/report.py (_cost_lines, findings report, lead time)",
      "src/agentmarshal/journal/complete.py, status_view.py, brief.py, gate.py (cited lines)",
      "src/agentmarshal/outbox.py (parser, SENT manifest), steps.py, stages.py, agree.py, cli.py",
      "docs/adr/ADR-0009, ADR-0013, ADR-0015, ADR-0016, ADR-0017, ADR-0018, ADR-0022 (cited sections)",
      "templates/journal-transaction.sh, templates/github/agentmarshal-governance.yml",
      "tests/test_record_text_safety.py, tests/test_review_capture.py (test names and the encoding-failure test body)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "read-only review of a non-git snapshot; the coordinator states the full sequence passed on d22abe79214e9480369dbab3eb51d89e7208b154, and nothing in this docs-only diff touches code"}
    ]
  },
  "evidence": {
    "ADV-readme-capture-preset": "README.md:44-47 names only `capture.overrides.reviews` and calls `hash` 'the default'; src/agentmarshal/journal/capture.py:68-87 (_PRESETS: attested->HASH, full->COMMIT, minimal->OFF), :88 DEFAULT_PRESET='attested', :140-151 level_for falls back to the preset when no override exists",
    "ADV-045-index-command": "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:107-109 ('or by the index `outbox status` takes') vs src/agentmarshal/outbox.py:122-137 (--index on `check` and `send`, which is where the skip is decided) and CHANGELOG.md:191-193 ('`outbox check --index <file>` treats the `Source:` digests ... the same way'); docs/proposals/README.md row 045 says 'an index passed to `check`, `send` or `status`'",
    "ADV-changelog-wrap": "CHANGELOG.md:251 — `sed -n 240,258p CHANGELOG.md | cat -A` shows 'And the reviewer output kept on a refused$' (~41 chars) inside a paragraph wrapped at ~66 chars"
  }
}
AGENTMARSHAL_VERDICT_END
