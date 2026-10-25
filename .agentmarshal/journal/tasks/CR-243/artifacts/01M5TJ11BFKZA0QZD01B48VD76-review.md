Проверку закончил. Ниже — прозаическая часть, затем verdict-блок.

**Проверка критериев приёмки**

- **AC1 (CHANGELOG, CR-236)** — выполнен. Новый текст (`CHANGELOG.md:245-251`) обещает ровно то, что делает код: `write_record` кодирует байты до `_create_exclusive` (`src/agentmarshal/journal/records.py:2113-2125`), а отката при сбое записи/закрытия уже созданного файла там нет. Демонстрирует это `tests/test_record_text_safety.py:444` `test_a_failure_while_encoding_leaves_no_file` (непарный суррогат в `outcome` проходит валидацию, падает на encode, `journal_root` не создан).
- **AC2 (README)** — выполнен. Пресеты совпадают с таблицей `_PRESETS` (`src/agentmarshal/journal/capture.py:71-88`: `attested`→`hash` по умолчанию, `full`→`commit`, `minimal`→`off`), путь override — `capture.overrides.reviews` (`capture.py:209-237`), `commit` пинит прозу артефактом журнала (`submit_review.py:137-144`), `hash` кладёт её в local state с событием `review-prose` (`review.py:709-740`), `off` не хранит ничего (`review.py:1621`). Непоставленное названо верно: `CaptureClass.ECONOMICS`/`SESSIONS` нигде вне `capture.py` не читаются, `attestation.py:21` прямо говорит «emits no Statement». Тесты: `tests/test_review_capture.py` (`test_by_default_the_prose_stays_out_of_the_journal`, `test_commit_keeps_todays_behaviour`, `test_off_keeps_nothing`, `test_local_state_that_cannot_be_used_falls_back_to_a_temporary_file`).
- **AC3 (proposals)** — выполнен. Все перечисленные в контракте файлы (012, 024–032, 034, 036, 037, 039–042, 044, 045) обновлены, плюс 009, 016, 018, 020, 023, 035. Каждое утверждение я сверял с кодом, а не с индексом: `resets_at` только у `provider-limit` (`session.py:84`), `advisory_dispositions` в `complete.py:152`, `verification`/`classes`/`previous_review` в `records.py:270`, `contract`-хеш в `records.py:223`, `report --findings` (`cli.py:486`), `_rejected_commits` считает `failed`/`error` (`report.py:436-442`), `brief` про последний упавший check и более поздний прошедший (`brief.py:76-121`), stage-набор ровно `pre-gate`/`post-gate` без `pre-complete` (`stages.py:212`), отсутствие `agentmarshal next` в CLI при существующем ADR-0023, `SENT`-манифест и `skipped as sent: <n>` (`outbox.py:65, 772`), `Records absent from <base>` (`cli.py:1530`), предупреждение гейта (`gate.py:2312`), `Reviewed commit <sha7>` и `(did not end 'implemented')` (`status_view.py:665-673`), `tokens=unmeasured` и `unmeasured=<n>` на task/Summary/Cost при том, что неизмеренная сессия с `cost` всё равно суммируется (`status_view.py:298`, `report.py:108-126, 949, 1005, 1037`), отсутствие способа узнать полосу гейта короче полного прогона (шаблон `templates/github/agentmarshal-governance.yml:77-80` гоняет весь gate). Тесты, демонстрирующие заявленное поведение: `tests/test_outbox.py`, `tests/test_unmeasured_session_usage.py`, `tests/test_status_base.py`, `tests/test_status_candidate_session.py`, `tests/test_gate.py`. Исторический текст находок и дат нигде не переписан — снятые из «Where» 039 и 042 подробности (отказ по ADR-0010, маршрут Apache-2.0) остаются в секциях Disposition выше.
- **AC4** — выполнен в проверяемой мне части: диффом затронуты только `CHANGELOG.md`, `README.md` и `docs/proposals/`; все относительные ссылки в изменённых файлах разрешаются (проверил каждую цель, включая ADR-0013/0015/0018/0021/0022 и перекрёстные ссылки на 023/029/033). CI я не запускал — в этой сессии выполнение pytest/uv требует подтверждения; полагаюсь на заявление координатора о прохождении на 5797c88.

**ADV-012-stale-disposition-line** (не блокирующее): в `docs/proposals/012-upstream-feedback-channel.md:34-36` абзац Disposition по-прежнему утверждает в настоящем времени «`agentmarshal init` does not scaffold the outbox directory or say anything about it», хотя скаффолд работает с 0.2.0 (`src/agentmarshal/project.py:322-340`, `CHANGELOG.md:855`); исправляет это только новая секция «Where» ниже, без маркера supersede. Это соответствует общей практике репозитория (024, 025, 044, 045 тоже оставляют старую фразу над «Where»), но здесь формулировка — прямое описание текущего поведения, а не «Accepted; not shipped yet», поэтому читатель до «Where» встречает ложное утверждение.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "5797c883853b3534cda3d42194f2b198d1a21637",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-012-stale-disposition-line"],
  "classes": {
    "ADV-012-stale-disposition-line": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 80 src/agentmarshal/journal/records.py", "result": "encode at line 2117 precedes _create_exclusive at 2120; no unlink/rollback around the write — CHANGELOG's narrowed promise holds"},
      {"what": "sed -n 60,90p src/agentmarshal/journal/capture.py", "result": "_PRESETS: minimal→OFF, attested→HASH, full→COMMIT for REVIEWS; DEFAULT_PRESET='attested' — matches README"},
      {"what": "grep -rn 'CaptureClass\\.(ECONOMICS|SESSIONS|REVIEWS)' src/ | grep -v journal/capture.py", "result": "no hits — economics and sessions classes are not read, as README states"},
      {"what": "grep -rn 'review-prose' src/", "result": "review.py:727 writes the event; review.py:709-740 keeps prose under local state with a temporary file as fallback"},
      {"what": "grep -n 'add_parser' src/ -r", "result": "outbox new/check/send/status, step start/end, stage run, agree, acknowledge, record-check present; no 'next' subcommand — proposal 041's claim holds"},
      {"what": "grep -rn 'skipped as sent|Records absent from|opened/amendment records of other tasks|tokens=unmeasured|Reviewed commit' src/", "result": "outbox.py:772, cli.py:1530, gate.py:2312, status_view.py:298, status_view.py:665 — all literal strings quoted by the proposals exist"},
      {"what": "grep -n 'output-limit|safety-limit|time-limit|stalled' docs/adr/ADR-0022-...md and its section headings", "result": "lines 181-182 inside '### 4. The session outcome vocabulary' — the 'section 4' citation in proposals 034 and 041 is exact"},
      {"what": "link check: every relative target in CHANGELOG.md, README.md and docs/proposals/*.md listed and tested with ls", "result": "all targets exist; no broken link"},
      {"what": "grep -rn 'not shipped|Nothing here is shipped|undecided|Not yet done' docs/proposals/*.md", "result": "remaining occurrences are historical disposition prose or genuinely unshipped items (038, 043); no proposal with a shipped feature left without a current Where"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 and 0.5.0 sections, 0.4.x entries)",
      "README.md (design-docs bullet)",
      "docs/proposals/README.md (all batch tables)",
      "docs/proposals/009,012,016,018,019,020,023,024,025,026,027,028,029,030,031,032,034,035,036,037,039,040,041,042,044,045",
      "src/agentmarshal/journal/records.py, capture.py, review.py, submit_review.py, complete.py, report.py, status_view.py, brief.py, gate.py, session.py",
      "src/agentmarshal/stages.py, steps.py, outbox.py, cli.py, doctor.py, project.py",
      "templates/journal-transaction.sh, templates/github/agentmarshal-governance.yml",
      "docs/adr/ADR-0009, ADR-0018, ADR-0022, ADR-0023; docs/quickstart.md (contract guidance)",
      "tests/test_record_text_safety.py:444, tests/test_review_capture.py (test names)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "command execution requires approval in this non-interactive read-only session; the coordinator states the sequence passed on 5797c88"}
    ]
  },
  "evidence": {
    "ADV-012-stale-disposition-line": "docs/proposals/012-upstream-feedback-channel.md:34-36 says 'Not yet done: `agentmarshal init` does not scaffold the outbox directory or say anything about it', while src/agentmarshal/project.py:322-340 creates `.agentmarshal/upstream/` with its README and CHANGELOG.md:855 records it under 0.2.0; the new '## Where' section below is the only correction and carries no supersession marker"
  }
}
AGENTMARSHAL_VERDICT_END
