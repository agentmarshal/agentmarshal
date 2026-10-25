Проверка закончена. Ниже прозаическая часть, затем verdict-блок.

## Что проверено по критериям

**AC1 (CHANGELOG, write-failure) — выполнено.** Новый текст в `CHANGELOG.md:247-250` обещает ровно то, что держит код: `write_record` кодирует запись в байты (`src/agentmarshal/journal/records.py:2113-2117`) до `_create_exclusive(path)`, значит сбой кодирования/сериализации не оставляет файла, а сбой при записи или закрытии уже созданного файла не откатывается — в коде действительно нет ни temp-файла, ни `unlink` в обработчике. Демонстрирующий тест: `tests/test_record_text_safety.py:444` `test_a_failure_while_encoding_leaves_no_file` (unpaired surrogate в `outcome` → `UnicodeEncodeError`, `assert not journal_root.exists()`); обратного теста на откат записи после создания файла нет, что согласуется с новой формулировкой.

**AC2 (README, capture policy) — выполнено.** `README.md:43-55` больше не называет политику неактивной: `capture.overrides.reviews` действительно читается (`journal/capture.py:250-260` → `level_for(CaptureClass.REVIEWS)`), `commit` пинит прозу как journal artifact (`journal/submit_review.py:144-145` через `write_artifact`), `hash` — дефолт (`DEFAULT_PRESET = "attested"`, `capture.py:70-86`) и кладёт байты в local state с событием `review-prose` (`journal/review.py:709-741`, `journal/review.py:1619-1621`), `off` не хранит ничего (`review.py:1621`). Непоставленное названо отдельно и верно: `CaptureClass.ECONOMICS`/`SESSIONS` нигде вне `capture.py` не читаются (grep по `src/` пуст), `attestation.py:21` сам говорит «it emits no Statement». Демонстрирующие тесты: `tests/test_review_capture.py:195` (`by_default_the_prose_stays_out_of_the_journal`), `:225` (`commit_keeps_todays_behaviour`), `:248` (`off_keeps_nothing`), `:350` (sidecar → local state).

**AC3 (Where-секции проposals) — выполнено.** Все 19 названных файлов (012, 024, 025, 026, 027, 028, 029, 030, 031, 032, 034, 036, 037, 039, 040, 041, 042, 044, 045) плюс 009, 016, 018, 020, 023, 035 обновлены, и каждое утверждение сходится с кодом: `resets_at` допускается только на `provider-limit` (`records.py:909-911`); `contract` на `opened`/`amendment`/`agreement` (`records.py:523-525`); `verification`/`classes`/`evidence`/`previous_review` в вердикте (`review.py:93`, `records.py:270`); `advisory_dispositions` в `completed` и открытые deferrals в `status` (`complete.py:152`, `status_view.py:588-601`); `report --findings` (`cli.py:485-489`), счёт `changes_required` в `status` и в gate-выводе (`status_view.py:524`, `gate.py:2440-2452`); `record-check` и подсчёт упавших проверок (`cli.py:1916`, `report.py:437`), `brief` с «Last failing check» и позднейшим прошедшим прогоном (`brief.py:76-121`); `step-started`/`step-ended` с deadline и показ просрочки в `status`/`doctor` (`steps.py:199,230`, `status_view.py:867-883`, `doctor.py:915-954`); `cli_session`/`report_ready` (`session.py:124-125`); `implementers`/`reviewers`/`independence` и проверки gate (`status_view.py:463-469`, `gate.py:1620-1646`); `agentmarshal next` действительно отсутствует (grep по `cli.py` пуст), поэтому «не поставлено» верно; словарь outcome-значений (`output-limit`, `stalled`, `safety-limit`, `time-limit`) и правда живёт только в `ADR-0022:181-182`, а не в коде — осторожная формулировка «stand in the vocabulary … documents» точна; `git switch -c` в `templates/journal-transaction.sh:116` подтверждает «still switches the working tree» в 040; warning гейта дословно есть (`gate.py:2312`), `Records absent from <base>` — `cli.py:1530`; 012-я привязка скаффолда к 0.2.0 подтверждается `CHANGELOG.md:855-856` внутри секции 0.2.0. Демонстрирующие тесты: `tests/test_status_candidate_session.py:105` (`Reviewed commit <sha7>: implementer session …` для 036), `tests/test_outbox.py:1292,1316` (`skipped as sent: N` для 045), `tests/test_unmeasured_session_usage.py` (`tokens=unmeasured`, `unmeasured=<n>` для 044), `tests/test_review_capture.py` (016). Исторические дисposition-абзацы и Apache-2.0-провенанс в 042 сохранены (042:160-190), оригинальный текст findings не переписан.

**AC4 (прочее) — выполнено с одной оговоркой.** Диф не выходит за `CHANGELOG.md`, `README.md`, `docs/proposals/`. Все относительные ссылки из изменённых файлов существуют: `ADR-0013/0015/0018/0021/0022` и перекрёстные `0NN-*.md` проверены через `ls`. Полную CI-последовательность я не запускал (read-only review) — опираюсь на ноту координатора о прохождении на `d22abe79`; тесты документацию-прозу не ассертят (в `tests/` фигурируют только фикстурные `CHANGELOG.md`), так что текстовые правки суиту сломать не могут.

## Advisory-находки

- `ADV-045-index-attribution` — в `docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:107-108` пропуск уже отправленных файлов приписан «the index `outbox status` takes», тогда как пропуском управляет индекс, переданный в `check`/`send` (`src/agentmarshal/outbox.py:126-137`, `CHANGELOG.md:191` — `outbox check --index <file>`), а `docs/proposals/README.md` (строка 045) говорит «an index passed to `check`, `send` or `status`»; формулировка унаследована, но правилась в этом дифе.
- `ADV-changelog-wrap` — в `CHANGELOG.md:251` осталась короткая «сиротская» строка («And the reviewer output kept on a refused») внутри абзаца, свёрнутого по ~66-69 символов: абзац после вставки не перезавёрнут; на рендер не влияет, только косметика.
- `ADV-records-comment-overpromise` — то же переобещание, что правил AUD-docs-claims-1-1, осталось в комментарии кода `src/agentmarshal/journal/records.py:2115` («an exclusive create can never leave an empty or partial record behind»); файл вне scope этого контракта, поэтому только как follow-up, не как требование к этому дифу.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "d22abe79214e9480369dbab3eb51d89e7208b154",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-045-index-attribution",
    "ADV-changelog-wrap",
    "ADV-records-comment-overpromise"
  ],
  "classes": {
    "ADV-045-index-attribution": "claim-accuracy",
    "ADV-changelog-wrap": "style",
    "ADV-records-comment-overpromise": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'def write_record' -A 60 src/agentmarshal/journal/records.py", "result": "encode at :2113-2117 precedes _create_exclusive at :2120; no rollback after creation — CHANGELOG's narrowed claim holds"},
      {"what": "grep for CaptureLevel/_PRESETS/review_capture_level_from_journal in src/agentmarshal/journal/capture.py", "result": "DEFAULT_PRESET='attested' → reviews=hash; overrides parsed; ECONOMICS/SESSIONS levels unused outside capture.py"},
      {"what": "grep -rn 'review-prose' src/ and grep 'Statement' src/agentmarshal/journal/attestation.py", "result": "review.py:727 writes review-prose event; attestation.py:21 'it emits no Statement'"},
      {"what": "grep for user-facing strings claimed by the proposals (tokens=unmeasured, unmeasured=, skipped as sent, 'candidate adds opened/amendment records of other tasks', 'Records absent from', 'Reviewed commit', step-started/step-ended, report --findings, --if-missing, deadline)", "result": "all present: status_view.py:298,665,673,883; report.py:437,949,1005,1038; outbox.py:772; gate.py:2312; cli.py:1530,465,485; steps.py:199,230; doctor.py:954"},
      {"what": "grep -rn for resets_at, cost keys, contract field, implementers/reviewers/independence, cli_session, report_ready, advisory_dispositions, verification/classes/previous_review", "result": "records.py:318,523-525,909; status_view.py:463-469; gate.py:1620-1646; session.py:124-125; complete.py:152; review.py:93"},
      {"what": "grep -rn 'add_parser(\"next\"' src/agentmarshal/cli.py", "result": "no match — 'agentmarshal next' correctly described as not shipped (041)"},
      {"what": "ls of every relative link target added by the diff (docs/adr/ADR-0009/0012/0013/0014/0015/0018/0020/0021/0022, docs/proposals/0NN-*.md)", "result": "all exist — no broken link"},
      {"what": "grep -n '^## ' CHANGELOG.md plus grep -n 'upstream|coordination|Reviewed commit|skipped as sent|unmeasured' CHANGELOG.md", "result": "version boundaries 0.6.0@11, 0.5.0@280, 0.4.1@483, 0.4.0@519, 0.3.0@626, 0.2.0@713, 0.1.0@876 — the diff's version attributions (init upstream scaffold @855 in 0.2.0, coordination @601 in 0.4.0, Reviewed commit @165 and outbox SENT @188-193 and unmeasured @195-204 in 0.6.0) all land in the claimed sections"},
      {"what": "grep -rn 'serializ|serialis' CHANGELOG.md README.md docs/", "result": "repo prose uses 'serialized/serialization'; the diff's spelling matches house style"}
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-243/contract.md",
      "CHANGELOG.md:230-280, 840-876",
      "README.md:30-70",
      "docs/proposals/README.md",
      "docs/proposals/009-lifecycle-extension-points.md:55-95",
      "docs/proposals/012-upstream-feedback-channel.md",
      "docs/proposals/019-journal-transactions-assume-direct-commits.md:55-85",
      "docs/proposals/038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md:115-120",
      "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md:118-205",
      "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:95-112",
      "src/agentmarshal/journal/records.py (write_record, schema/outcome/cost/contract validation)",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/journal/review.py:660-760, 1480-1630",
      "src/agentmarshal/journal/submit_review.py",
      "src/agentmarshal/outbox.py:100-150, 560-680, 772",
      "src/agentmarshal/stages.py:1-290",
      "src/agentmarshal/cli.py:150-175, 300-370, 478-492, 675-715, 1520-1540",
      "templates/journal-transaction.sh (git switch -c at :116)",
      "tests/test_record_text_safety.py:444-469",
      "tests/test_review_capture.py (test list)",
      "tests/test_outbox.py:1290-1400",
      "tests/test_status_candidate_session.py:100-330",
      "docs/adr/ADR-0017-evidence-of-reviews-and-checks.md:84",
      "docs/adr/ADR-0018-governing-the-contract.md:33",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md:175-190"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "read-only review; the coordinator reports the full sequence passed on the reviewed commit, and no test asserts repository documentation prose (tests use fixture CHANGELOG/README files), so the docs-only diff cannot change those results"},
      {"what": "a scripted markdown link-resolution sweep (python3 script in the scratchpad)", "why": "interpreter execution was not permitted in this sandbox; every link target added by the diff was instead verified individually with ls/grep"}
    ]
  },
  "evidence": {
    "ADV-045-index-attribution": "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:106-109 'known by the `SENT` manifest `send` writes, or by the index `outbox status` takes' vs src/agentmarshal/outbox.py:122-137 (--index on both check_parser and send_parser), CHANGELOG.md:191 '`outbox check --index <file>` treats the `Source:` digests a passed index names the same way', and docs/proposals/README.md 045 row 'an index passed to `check`, `send` or `status`'",
    "ADV-changelog-wrap": "CHANGELOG.md:248-252 — lines 248-250 run 66-69 chars, line 251 'And the reviewer output kept on a refused' is 41 chars mid-paragraph; the paragraph was not re-wrapped after the insertion",
    "ADV-records-comment-overpromise": "src/agentmarshal/journal/records.py:2114-2116 '# Encode before the file exists: a value UTF-8 cannot encode fails / here, so an exclusive create can never leave an empty or partial / record behind.' — grep -rn 'empty or partial' over CHANGELOG.md README.md docs/ src/ UPGRADING.md returns this one site only; it is outside this contract's scope (CHANGELOG.md, README.md, docs/proposals/)"
  }
}
AGENTMARSHAL_VERDICT_END
