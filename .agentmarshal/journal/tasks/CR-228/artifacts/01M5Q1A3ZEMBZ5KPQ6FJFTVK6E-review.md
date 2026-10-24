Разобрал контракт, диф и реальные файлы в снапшоте. Тесты и линтеры сам не запускал — песочница не даёт запускать `python3`/`pytest`; про зелёный CI на `84447df` опираюсь на записку координатора.

## Где диф выполняет критерии приёмки

**Критерий 1 (артефакты изменения + архив).** Изменение лежит в `openspec/changes/archive/2026-10-24-outbox-skips-sent/` с `proposal.md`, `design.md`, `tasks.md` и дельтой `specs/outbox/spec.md`; `openspec/changes/` больше не содержит рабочей копии — архивирование состоялось. MODIFIED-требование приехало в `openspec/specs/outbox/spec.md:56-89` байт в байт с дельтой: тот же заголовок `### Requirement: outbox check names what each draft lacks`, тот же абзац и все пять прежних сценариев. Каждое требование в спеке встречается ровно один раз (7 заголовков `### Requirement:`, дублей нет). Все десять новых сценариев имеют тест, чей докстринг их называет: `tests/test_outbox.py:1283, 1310, 1333, 1359, 1394, 1417, 1435, 1456, 1483, 1509` (плюс вариант «absent» на `1537`).

**Критерий 2 (пропуск уже отправленного + строка `skipped as sent`).** Чтение манифеста и слияние с `--index` — `src/agentmarshal/outbox.py:486-515`; само решение «не черновик» — `551-568`; печать строки — `623-624`; `--index` зарегистрирован для `check` и `send` в `107-122`. Демонстрируют: `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft` (`1283`, `skipped as sent: 2`), `test_check_index_skips_a_file_a_source_line_claims` (`1310`), `test_send_index_skips_a_file_a_source_line_claims` (`1333`), `test_the_sent_manifest_is_not_a_draft` (`1394`), `test_an_unreadable_sent_manifest_refuses_the_check` (`1417`), `test_check_index_refuses_an_unreadable_index` (`1581`). Парсер `Source:` действительно один на три команды — `_index_claims` (`927-954`), текст отказа `status` сохранён слово в слово.

**Критерий 3 (запись в манифест внутри того же batch-коммита, «changed after sending»).** `_manifest_next` (`445-459`), пин `SENT` по будущему содержимому (`606-622`), запись перед `git add` и восстановление при отказе (`837-899`, `779-795`). Демонстрируют: `test_send_records_the_batch_in_the_sent_manifest` (`1456` — коммит несёт `SENT`, следующий `check` пропускает без индекса), `test_a_manifest_gained_across_batches_appends` (`1483`), `test_a_refused_send_leaves_the_manifest_as_it_was` (`1509`) и `test_a_refused_send_removes_a_manifest_it_wrote` (`1537`). Изменённый после отправки файл проверяется как черновик с аннотацией, не отказом — `564-565`, тест `1359`.

**Критерий 4 (нерегулярная запись, README, поведение без манифеста).** Ветка нерегулярной записи не тронута (`539-544`), по-прежнему одна строка и не инкремент `checked` — тест `461`. README остаётся не черновиком (`551`), тест `253`. Для `check` без манифеста и без `--index` поведение действительно прежнее; для `send` — нет, см. ADV-1.

**Критерий 5 (экранирование, leak scan, прочие команды).** Все печатаемые имена идут через `_shown_name` + `safe_path` как раньше; пропущенный файл всё равно сканируется — `600` и тест `test_a_skipped_file_still_goes_through_the_leak_scan` (`1555`), который требует и `skipped as sent: 1`, и хит `old-one.md: private-marker #1`, и отсутствие самого маркера в выводе. `status` поведенчески не изменился, `cli.py` не тронут. Полную последовательность CI я не запускал.

## Замечания (все несблокирующие)

**ADV-1** — `src/agentmarshal/outbox.py:818` вместе с `561`: после настоящего `send` переименование уже отправленного черновика больше не уезжает с батчем. Хэш переименованного файла лежит в `SENT`, файл пропускается как отправленный, `result.drafts` пуст, и `send` отказывает с «no drafts to send» — раньше это был коммит-rename. Видно по самому дифу тестов: существующий `test_a_draft_renamed_since_the_last_batch_is_sent_as_a_rename` (`tests/test_outbox.py:935-948`) пришлось переписать — первый батч теперь коммитится руками, и докстринг прямо это объясняет. Тем самым критерий 4 («an outbox with no sent manifest and no `--index` behaves exactly as today, which the existing outbox tests demonstrate unchanged») буквально не выполнен для `send`, и новое поведение ни спекой, ни тестом не закреплено. Критерии 3 и 4 здесь противоречат друг другу, выбор в пользу 3 разумен — но departure стоит назвать, а поведение зафиксировать тестом или строкой требования.

**ADV-2** — `src/agentmarshal/project.py:234` и `openspec/specs/outbox/spec.md:4` обещают адоптеру аутбокс «one file per finding»; теперь `send` сам создаёт и коммитит `SENT`, который находкой не является, и ни одно обращённое к адоптеру место этого не упоминает. `project.py` вне scope контракта, а Purpose капабилити править руками запрещает AGENTS.md и дельта-формат его не меняет — значит это departure для отчёта, а не правка.

**ADV-3** — `openspec/changes/archive/2026-10-24-outbox-skips-sent/design.md:36-44`: решение 1 утверждает про имя в строке манифеста «matching never uses it, only the digest does», а решение 3 того же файла и код (`src/agentmarshal/outbox.py:564`, `name in manifest_names`) сопоставляют именно по имени, чтобы выдать «changed after sending». Две фразы в одном документе противоречат друг другу.

**ADV-4** — `src/agentmarshal/outbox.py:600` против `852`: leak scan в прогоне `check` видит прежние байты `SENT` (`manifest_old`), а `send` стейджит и коммитит `manifest_new`, которые в этом прогоне не сканировались. Критерий 5 («the leak scan still covers every file `send` stages») выполняется только производно: добавляемые строки — это sha256 (под текущие сигнатуры ничего не матчит, `journal/capture.py:273-287` — ни одной generic-hex сигнатуры) плюс имя, каждое из которых уже просканировано `_name_hits`, так что маркер в имени отказывает батч до записи. Дефектом по существу я это не считаю, но формулировку критерия диф не покрывает буквально.

Блокирующих находок нет: пины, восстановление индекса и манифеста, порядок проверок (отказ по «staged outside» происходит до записи `SENT`, поэтому там на диске ничего не остаётся) и совместимость с существующими тестами `send` я прошёл по коду отдельно.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "84447dfab7e07734398254e91fe45aa24b325539",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1", "ADV-2", "ADV-3", "ADV-4"],
  "classes": {
    "ADV-1": "correctness",
    "ADV-2": "claim-accuracy",
    "ADV-3": "claim-accuracy",
    "ADV-4": "contract-mismatch"
  },
  "verification": {
    "read": [
      "src/agentmarshal/outbox.py",
      "tests/test_outbox.py",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/design.md",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/proposal.md",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/tasks.md",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/specs/outbox/spec.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "src/agentmarshal/project.py (outbox README scaffold)",
      "src/agentmarshal/journal/capture.py (leak signatures)",
      "CHANGELOG.md (release-scoped, no Unreleased section)"
    ],
    "executed": [
      {"what": "grep -n 'Requirement:' openspec/specs/outbox/spec.md", "result": "7 requirement headings, each exactly once; the two ADDED ones at lines 331 and 388"},
      {"what": "grep -n 'Scenario:' tests/test_outbox.py", "result": "all ten new scenarios have a test docstring naming them (lines 1283-1537)"},
      {"what": "ls openspec/changes/ openspec/changes/archive/", "result": "changes/ holds only archive/; the change sits at archive/2026-10-24-outbox-skips-sent/"},
      {"what": "grep -rn 'rename' openspec/specs/outbox/spec.md", "result": "no match — the rename behaviour ADV-1 names is pinned by a test docstring only, not by a requirement"},
      {"what": "grep -n 'SIGNATURE|re.compile' src/agentmarshal/journal/capture.py", "result": "no generic hex/entropy signature, so manifest digests cannot trip the scan on a later run"}
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "no uv in the snapshot and the sandbox refuses to execute python3/pytest; the coordinator reports the sequence green on this commit, and no finding here claims a tool failure"},
      {"what": "git history checks", "why": "the review snapshot is not a git repository"}
    ]
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/outbox.py:561 skips a file whose sha256 is in SENT; :818 refuses when result.drafts is empty — so after a real send, a git-mv'd sent draft is the only entry and send prints 'no drafts to send'. tests/test_outbox.py:935-948: the pre-existing rename test now builds its first batch with `_git(repo, 'add'/'commit')` instead of `main(['outbox','send'])`, docstring: 'The first batch is committed by hand — a `send` would list the draft's hash in the sent manifest, and the renamed file would skip as already sent.' No test covers the new refusal.",
    "ADV-2": "src/agentmarshal/project.py:234 'Findings about **AgentMarshal itself** go here — one file per finding —'; openspec/specs/outbox/spec.md:4 'one file per finding, sent as a batch'; src/agentmarshal/outbox.py:852 writes .agentmarshal/upstream/SENT and :859 stages it into the batch commit.",
    "ADV-3": "openspec/changes/archive/2026-10-24-outbox-skips-sent/design.md decision 1: 'matching never uses it, only the digest does' vs decision 3 of the same file and src/agentmarshal/outbox.py:564 `elif is_draft and name in manifest_names: notes.append(\"changed after sending\")`.",
    "ADV-4": "src/agentmarshal/outbox.py:497 reads manifest_old and :600 `hits.extend(_draft_hits(name, text, markers))` scans those bytes, while :852 `sent_path.write_bytes(result.manifest_new)` stages different bytes; mitigation: each added line is a sha256 plus a name already scanned at :543/:600, and grep over src/agentmarshal/journal/capture.py:273-287 shows no signature matching bare hex."
  }
}
AGENTMARSHAL_VERDICT_END
