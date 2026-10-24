Проверил диффы против кода и документов репозитория.

**Что проверено по критериям приёмки**

- **Критерий 1 (044).** `docs/proposals/044-unmeasured-usage-is-written-as-zeros.md` несёт ровно ту форму, что и существующие digest'ы Adopter A (ср. `025`, `026`): строка reporter'а с `Reporter/Observed on/Source/Disposition`, затем `Finding`, `Proposed`, `Disposition`, `Where`. Source-хеш совпадает с контрактом байт в байт (`816c7ff8…57b0d`), «Observed on: 0.4.1, rechecked on 0.5.0» на месте, релиз для write side не назван — только «with the next record schema». Все факты о коде в тексте сходятся с источником: `cli.py:407-409` (три флага с `default=0`), `records.py:2320-2325` (`create_session_record` всегда пишет `tokens`), `records.py:778-793` (правило `session-tokens` требует ровно три неотрицательных int), `records.py:2308` и `cli.py:411,1306-1313` (`usage` опционален, `--usage-method` только `reported|measured` в паре с `--usage-provider`), `report.py:174-186` (отсутствие `usage` читается как `unrecorded`, печатается как `usage=…` на `report.py:691,716`), `report.py:364-365` (сумма `tokens` по всем session-записям), `report.py:106,663` (`sessions_without_cost` считается отдельно), `docs/quickstart.md:547-550` (quickstart велит опускать флаги именно при неизвестном provenance). Теста, который это демонстрирует, нет и быть не может: изменение документационное, а read side ещё не реализован (в `src/` слова `unmeasured` нет; сопутствующая задача CR-229 не начата — `openspec/changes/` содержит только `archive`), так что «не отгружено» — правда.
- **Критерий 2 (045).** Source-хеш (`a819341c…11008`) и «Observed on: 0.5.0» совпадают с контрактом; диспозиция — пропуск уже отправленных файлов по манифесту `send` или по индексу `outbox status` в 0.6.0 — записана и в файле, и в индексе. Механика описана верно: `outbox.py:439-456` (обход всех записей, draft = любой обычный файл кроме `README.md`), `outbox.py:451` (`not a draft, not checked` и отказ батча), `outbox.py:80` + `57` + `338-350` (пять полей как `## <Field>`), `outbox.py:659-662,708-710` (`_run_send` запускает тот же check и делает `git add --force -- .agentmarshal/upstream`), `outbox.py:767-825` (`status --index` хеширует файлы и сверяет с `Source:`-строками), у `check` нет ни флага, ни ключа конфигурации (`outbox.py:100-112`, в `.agentmarshal/project.json` ничего про outbox). «0.5.0 отгрузила группу» подтверждается `CHANGELOG.md:150-157`, `UPGRADING.md:75`; текущая версия `0.6.0.dev0` (`pyproject.toml:3`), так что «ещё не отгружено» верно. Противоречия с ADR-0020 нет: его решение 3 требует, чтобы leak scan шёл «по тому, что будет отправлено», и диспозиция это прямо сохраняет. ADR-0009 digest'ы не затрагивают. Теста, демонстрирующего критерий, нет — документация.
- **Критерий 3 (README).** Обе строки стоят в таблице с тем же заголовком `| # | Theme | Reporter | Disposition | Where |`, что у батчей 2026-10-03 и 2026-10-01, секция вставлена в обратно-хронологическом порядке перед 2026-10-03, вводная проза и «shared theme» повторяют формат соседей. Теста нет (единственный тест, упоминающий `docs/proposals`, — `tests/test_project.py:31-44`, он про шаблон outbox-README и не затронут).
- **Критерий 4 (без идентификаторов).** `grep -nE "CR-[0-9]+|[0-9A-HJKMNP-TV-Z]{26}"` по обоим файлам — ни одного попадания; из не-ASCII только `—` и `·`, как в существующих digest'ах; NBSP/узких пробелов нет (важно после 025); имён людей, продукта, аккаунта провайдера нет, путь `.agentmarshal/upstream/` — собственная конвенция проекта, опубликованная в `docs/proposals/README.md` и ADR-0020, а не путь адоптера. Все три добавленные ссылки резолвятся: `docs/adr/ADR-0020-the-outbox-command-group.md`, `docs/proposals/025-…md`, `docs/proposals/026-…md`, плюс две новые ссылки индекса на сами файлы. Приватных маркеров в `project.json` нет, так что leak scan тут нечему срабатывать.
- **Критерий 5 (прочие файлы, проверки).** Дифф трогает только три файла из scope. Полную последовательность CI я **не запускал и не могу**: в снапшоте нет `uv` и это не git-репозиторий (`git rev-parse HEAD` → «not a git repository»), а часть фикстур требует git. Утверждение координатора о зелёном прогоне на 2f97fed принимаю как данность; доковых проверок в `gitflic-ci.yaml` нет, md-файлы `ruff`/`mypy`/`validate` не трогают.

**Advisory-находки**

- **CR230-A1** (`docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:75`): фраза «`status` and `report` show a session … as unmeasured rather than folding its zeros into the totals» приписывает `status` поведение, которого у него нет — `status` сегодня вообще не печатает счётчики токенов (слова `tokens` нет ни в `status.py`, ни в `status_view.py`; строка сессии — `status_view.py:406-424` — показывает actor/vendor/model/fallback_reason), так что «сворачивать нули в итоги» может только `report`. Критерий контракта требует именно такой формулировки, поэтому это не блокирует, но в публичном документе проекта, который «описывает, что делает», противопоставление для `status` неточно.
- **CR230-A2** (`docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:90`): диспозиция перечисляет единственное место, где манифест отправленных хешей должен быть исключением — «the field check already exempts the `README.md`». Второго места она не называет: `_run_send` в `outbox.py:674` считает draft'ом любую запись с именем, отличным от `README.md`, поэтому манифест в outbox'е сам по себе снимет защиту «no drafts to send» и позволит коммит батча из одного манифеста. Как принятое решение это описание неполно для того, кто будет его реализовывать.

Блокирующих находок нет: все утверждения digest'ов о коде, которые можно проверить, сошлись с файлами, форма и индекс соответствуют существующим, идентификаторов адоптера нет, ссылки резолвятся.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "2f97fedc5434eb0ac089c06808236a423e9f8f3f",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["CR230-A1", "CR230-A2"],
  "classes": {
    "CR230-A1": "claim-accuracy",
    "CR230-A2": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n for the three token flags and the usage flags in src/agentmarshal/", "result": "cli.py:407-409 --input-tokens/--output-tokens/--cache-tokens type=int default=0; cli.py:411 --usage-method choices=('reported','measured'); cli.py:1306-1313 the pair is required together"},
      {"what": "read create_session_record and the session-tokens rule", "result": "records.py:2320-2325 always writes tokens{input,output,cache}; records.py:778-793 requires keys == {input,output,cache}, each int >= 0; records.py:2330 usage written only when provider is not None"},
      {"what": "grep -rn 'unrecorded|sessions_without_cost|tokens' src/agentmarshal/journal/report.py", "result": "report.py:174-186 absent usage -> 'unrecorded'; report.py:691,716 printed as usage=<value>; report.py:364-365 sums tokens of every session record; report.py:106,663 sessions_without_cost counted apart"},
      {"what": "grep -rn 'tokens|unmeasured' src/agentmarshal/journal/status.py status_view.py and src/ overall", "result": "no 'tokens' and no 'unmeasured' anywhere in status.py/status_view.py or elsewhere in src/; status_view.py:406-424 session line shows actor/vendor/model/fallback_reason only -- basis for CR230-A1"},
      {"what": "read src/agentmarshal/outbox.py (_check, _run_send, _run_status, constants)", "result": "line 47/51 _README and _OUTBOX_DIR_SPEC='.agentmarshal/upstream'; 57 five fields; 80 _HEADING ^## (.+?)\\s*$; 439-456 every entry iterated, non-regular prints 'not a draft, not checked' and refuses; 456 is_draft = name != README; 659-662 send runs the same check; 674 no-drafts guard counts any non-README entry as a draft (CR230-A2); 708-710 git add --force -- .agentmarshal/upstream; 767-825 status --index sha256-hashes and matches Source: lines"},
      {"what": "grep -n outbox in CHANGELOG.md, UPGRADING.md and version in pyproject.toml", "result": "CHANGELOG.md:150-157 the outbox group shipped in 0.5.0 (2026-10-23); UPGRADING.md:75 names new/check/send/status; pyproject.toml:3 version = 0.6.0.dev0"},
      {"what": "grep -nE 'CR-[0-9]+|[0-9A-HJKMNP-TV-Z]{26}' and grep -nP '[^\\x00-\\x7F]' and a NBSP/narrow-space scan over both new digests and the README", "result": "no task ids and no ULID-class strings; non-ASCII only em dash and middot, as in existing digests; no U+00A0/202F/2009/2007/2060/FEFF"},
      {"what": "resolve every link added by the diff", "result": "docs/adr/ADR-0020-the-outbox-command-group.md, docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md, docs/proposals/026-reviewer-facts-round-convergence-and-two-gaps.md, docs/proposals/044-..., docs/proposals/045-... all exist"},
      {"what": "grep -rln proposals tests/ and read gitflic-ci.yaml", "result": "only tests/test_project.py:31-44 (outbox README template), unaffected; CI runs uv sync/validate/pytest/ruff/ruff format/mypy and no documentation check"},
      {"what": "check for an already-shipped reading side and sibling work", "result": "openspec/changes/ holds only archive/; .agentmarshal/journal/tasks/CR-229/ carries the reading-side contract, not an implementation -- 'not shipped yet' holds"}
    ],
    "read": [
      "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md",
      "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md",
      "docs/proposals/README.md",
      "docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md (header and section headings)",
      "docs/proposals/026-reviewer-facts-round-convergence-and-two-gaps.md (header and section headings)",
      "docs/proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md (header and section headings)",
      "docs/proposals/043-review-before-integration-makes-every-merge-stale.md (header and section headings)",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/adr/ADR-0009-research-findings-lifecycle.md (headings)",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md (context and framing)",
      "docs/quickstart.md:530-560",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/journal/records.py (session rules and create_session_record)",
      "src/agentmarshal/journal/report.py (usage provenance, token and cost sums)",
      "src/agentmarshal/journal/status_view.py:406-424",
      "src/agentmarshal/cli.py (record-session and outbox parsers)",
      "CHANGELOG.md (0.5.0 section)",
      "UPGRADING.md:55-100",
      "gitflic-ci.yaml",
      ".agentmarshal/project.json",
      ".agentmarshal/journal/tasks/CR-229/contract.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "uv is not installed in the review snapshot and the snapshot is not a git repository (git rev-parse HEAD fails), which the package and several fixtures require; the coordinator states the sequence passed on 2f97fedc5434eb0ac089c06808236a423e9f8f3f"},
      {"what": "agentmarshal leak-scan over the diff", "why": "no git repository and no installed package; checked instead that .agentmarshal/project.json declares no private markers and that the new text carries no adopter identifier"}
    ]
  },
  "evidence": {
    "CR230-A1": "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:75 says 'status and report show a session whose usage was not measured as unmeasured rather than folding its zeros into the totals'; grep -rn 'tokens' src/agentmarshal/journal/status.py src/agentmarshal/journal/status_view.py -> no match, and src/agentmarshal/journal/status_view.py:406-424 (_implementer_session_line) prints only actor=, vendor=, model= and fallback_reason=, so status shows no token counts and no totals today",
    "CR230-A2": "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:90 names only the field check as the place that exempts a non-draft entry; src/agentmarshal/outbox.py:674 'if not any(entry.name != _README for entry in outbox.iterdir()):' treats every non-README entry as a draft, so a sent-hash manifest in the outbox would also satisfy the 'no drafts to send' guard at src/agentmarshal/outbox.py:675"
  }
}
AGENTMARSHAL_VERDICT_END
