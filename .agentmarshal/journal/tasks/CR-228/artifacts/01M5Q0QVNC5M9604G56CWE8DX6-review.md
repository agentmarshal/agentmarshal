Разобрал контракт, дельту, итоговый spec и код. Запускать ничего не могу — в этом снапшоте нет git-репозитория, а выполнение `python3`/`uv` не разрешено, так что всё проверено чтением файлов; результат CI беру из записки координатора.

## Как выполнены acceptance criteria

**AC1 (change, delta, архивирование).** Выполнен. `openspec/changes/archive/2026-10-24-outbox-skips-sent/` содержит `proposal.md`, `design.md`, `tasks.md` и `specs/outbox/spec.md` — структура та же, что у `2026-10-03-outbox-send-and-status`. MODIFIED-блок требования «`outbox check` names what each draft lacks» совпадает с `openspec/specs/outbox/spec.md:56-90` байт в байт (diff чистый, заголовок и все пять сценариев на месте). В итоговом spec семь требований, каждое ровно один раз (`openspec/specs/outbox/spec.md:12,56,91,174,262,331,388`). Все десять новых сценариев имеют тест, чей docstring их называет: `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`, `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`, `test_the_sent_manifest_is_not_a_draft`, `test_an_unreadable_sent_manifest_refuses_the_check`, `test_send_refuses_when_every_file_is_already_sent`, `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_a_refused_send_leaves_the_manifest_as_it_was` (+ вариант `test_a_refused_send_removes_a_manifest_it_wrote`).

**AC2 (skip по манифесту и по `--index`, строка `skipped as sent`).** Выполнен. Чтение `SENT` и отказ при нечитаемом манифесте — `src/agentmarshal/outbox.py:491-508`; переиспользование парсера `Source:` через общий `_index_claims` — `outbox.py:509-515` и `outbox.py:927-954`; сам skip — `outbox.py:561-563`; строка `skipped as sent: <n>` — `outbox.py:623-624`. Демонстрируют три теста выше плюс `test_check_index_refuses_an_unreadable_index`.

**AC3 (`send` дописывает хэши в том же batch-коммите; изменённый после отправки файл проверяется).** Выполнен. `manifest_new` считается в проверке и пинится тем же `hash-object --stdin --path` (`outbox.py:606-622`), `send` пишет ровно эти байты перед `add` (`outbox.py:850-856`), сверка пинов — `outbox.py:871`. Аннотация `changed after sending` — `outbox.py:564-565`, не ставит `refused`. Тесты: `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`.

**AC4 (нерегулярная запись, README, «ведёт себя ровно как сегодня»).** Выполнен частично — см. A3. Первая половина в порядке: нерегулярная запись по-прежнему одна строка и не draft (`outbox.py:539-544`), что демонстрирует неизменённый `test_an_entry_that_is_not_a_regular_file_is_named_as_not_checked` (каталог `bundled` и symlink), README по-прежнему не draft (`outbox.py:551`, `test_the_readme_init_writes_is_not_a_draft`).

**AC5 (escaping, leak scan, никакая другая команда не меняется).** Выполнен частично — см. A1. Каждое новое печатаемое значение проходит `safe_path` (`outbox.py:605`, `620-621`, `897`); skip не выводит файл из leak scan — `test_a_skipped_file_still_goes_through_the_leak_scan`; `status` сохранил поведение, вынос парсера в `_index_claims` только переместил код, тесты `status` не тронуты; `--index` добавлен только `check` и `send` внутри `register()` (`outbox.py:107-122`), `cli.py` не менялся.

Противоречий с ADR-0020 не нашёл: решение 4 говорит «stages only the outbox», а `SENT` лежит внутри outbox; решение 5 про `status --index` не затронуто.

## Findings

**A1-sent-manifest-not-scanned-at-send** (advisory, unconfirmed): `send` стейджит и коммитит `.agentmarshal/upstream/SENT` с содержимым `result.manifest_new` (`src/agentmarshal/outbox.py:852`), которое проверка в этом прогоне в leak scan не передавала — сканировалось только прежнее содержимое `SENT`; AC5 требует, чтобы скан покрывал каждый файл, который стейджит `send`. Практический сценарий: сигнатура `authorization-header` (`src/agentmarshal/journal/capture.py:287`) — `authorization:\s*(?:bearer|basic)\s+\S+`, а `scan_for_leaks` ищет по всему тексту (`capture.py:456-458`), так что `\s+` съедает перевод строки; draft с именем `authorization: bearer` сам по себе хит не даёт (после «bearer» нет `\S+`), но строка манифеста `<digest>  authorization: bearer\n<digest>  zz.md\n` даёт — и следующий `check` будет отказывать постоянно, пока `SENT` не поправят руками.

**A2-manifest-line-injection-via-newline-in-name** (advisory, unconfirmed): `_manifest_next` подставляет в строку манифеста `_shown_name(entry.name)` как есть (`src/agentmarshal/outbox.py:455`), а `_shown_name` экранирует только недекодируемые байты, не управляющие символы (`outbox.py:201-213`), поэтому имя файла с переводом строки записывает в `SENT` больше одной строки — включая произвольную `<sha256>  <name>`, которую `_SENT_LINE` (`outbox.py:56`) потом разберёт как отправленный digest, и будущий `check` пропустит файл, который ни разу не судил по пяти полям (`outbox.py:561-563`). Порог срабатывания высокий — нужен файл с таким именем в собственном outbox оператора, — но манифест теперь машинно разбираемый файл, а не только отчёт.

**A3-rename-after-send-and-the-unchanged-tests-claim** (advisory): AC4 утверждает, что outbox без манифеста и без `--index` «ведёт себя ровно как сегодня, что демонстрируют неизменённые существующие тесты outbox», но `tests/test_outbox.py:935-948` пришлось изменить — первый batch теперь коммитится руками, и docstring сам объясняет почему: после настоящего `send` переименованный уже отправленный draft попадает под skip, `result.drafts` пуст (`src/agentmarshal/outbox.py:818`) и `send` отказывает «no drafts to send», оставив `git mv` в индексе. Поведение сознательное (non-goal «Rewriting or moving files already sent») и неизбежное при AC3, то есть AC3 и AC4 в контракте в натяжке друг с другом, — но буквально AC4 не выполнен, и в отчёте это стоит называть departure.

**A4-design-says-matching-never-uses-the-name** (advisory): `openspec/changes/archive/2026-10-24-outbox-skips-sent/design.md:46` утверждает «matching never uses it, only the digest does» про имя в строке манифеста, тогда как следующий же bullet того же файла (строки 47-53) и код (`src/agentmarshal/outbox.py:508`, `564`) сопоставляют именно имя, чтобы поставить `changed after sending`. По контексту «matching» значит только определение «уже отправлено», но как написано — это неверное утверждение о коде в названном документе change.

Блокирующих дефектов не нашёл: путь восстановления после отказа корректен (`outbox.py:885-899`: `manifest_wrote` выставляется до записи, так что частичная запись тоже откатывается; `manifest_old is None` → `unlink`), пин `SENT` после цикла перезаписывает пин того же пути из цикла (одинаковый ключ `os.fsencode`), а проверка «batch == [SENT]» ловит пустой batch, потому что `manifest_new` отличается от `manifest_old` всегда, когда `drafts` непуст.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "84447dfab7e07734398254e91fe45aa24b325539",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "A1-sent-manifest-not-scanned-at-send",
    "A2-manifest-line-injection-via-newline-in-name",
    "A3-rename-after-send-and-the-unchanged-tests-claim",
    "A4-design-says-matching-never-uses-the-name"
  ],
  "classes": {
    "A1-sent-manifest-not-scanned-at-send": "contract-mismatch",
    "A2-manifest-line-injection-via-newline-in-name": "security",
    "A3-rename-after-send-and-the-unchanged-tests-claim": "contract-mismatch",
    "A4-design-says-matching-never-uses-the-name": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "diff of the delta's MODIFIED requirement block (changes/archive/2026-10-24-outbox-skips-sent/specs/outbox/spec.md lines 3-43) against openspec/specs/outbox/spec.md lines 56-90", "result": "identical apart from the delta's own '## MODIFIED Requirements'/'## ADDED Requirements' headers — the requirement heading, full text and all five scenarios match byte for byte"},
      {"what": "grep -n '^### Requirement:' openspec/specs/outbox/spec.md", "result": "7 headings at lines 12, 56, 91, 174, 262, 331, 388 — each requirement exactly once"},
      {"what": "ls -R of the archived change vs 2026-10-03-outbox-send-and-status", "result": "same structure: proposal.md, design.md, tasks.md, specs/outbox/spec.md; openspec/changes/ holds only archive/"},
      {"what": "grep for SENT / 'skipped as sent' outside src/agentmarshal/outbox.py", "result": "no other module references them; cli.py only registers and dispatches the group"},
      {"what": "grep -rn 'outbox check|outbox send|outbox status|outbox new' CONTRIBUTING.md docs/quickstart.md docs/sidecar.md README.md CHANGELOG.md", "result": "only CHANGELOG.md:152-157 (the released 0.5.0 entry); no user doc documents the flags, so no in-scope doc went stale"},
      {"what": "grep -n of the leak-scan signature table in src/agentmarshal/journal/capture.py", "result": "all nine signatures are prefix-anchored; none can match a bare 64-hex digest, but 'authorization-header' at capture.py:287 can match across a newline, which is A1's scenario"}
    ],
    "read": [
      "src/agentmarshal/outbox.py (whole file)",
      "tests/test_outbox.py (imports, lines 253-270, 460-490, 640-760, 930-970, 1258-1592)",
      "openspec/specs/outbox/spec.md (whole file)",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/{proposal.md,design.md,tasks.md,specs/outbox/spec.md}",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/threat-model.md lines 140-200 and 380-425",
      "src/agentmarshal/journal/capture.py lines 265-300 and 446-466",
      "src/agentmarshal/project.py lines 225-300 (the outbox README init writes)",
      "CONTRIBUTING.md lines 103-140, CHANGELOG.md lines 1-60"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "command execution is not permitted in this review session and the snapshot is not a git repository; the coordinator states the sequence passed on this commit"},
      {"what": "an executed reproduction of A1 and A2", "why": "both are reasoned from the code paths and the signature table, not run, hence advisory and marked unconfirmed"}
    ]
  },
  "evidence": {
    "A1-sent-manifest-not-scanned-at-send": "src/agentmarshal/outbox.py:852 writes result.manifest_new and outbox.py:859 stages it, while the only scan calls are outbox.py:543 and outbox.py:600 over the entries read before that write; src/agentmarshal/journal/capture.py:287 is re.compile(r\"(?i)authorization:\\s*(?:bearer|basic)\\s+\\S+\") and capture.py:456-458 runs pattern.search over the whole text, so the pattern can span the manifest's newline",
    "A2-manifest-line-injection-via-newline-in-name": "src/agentmarshal/outbox.py:455 — added = b\"\".join(f\"{digest}  {name}\\n\".encode() ...) with name from outbox.py:538 (_shown_name); outbox.py:201-213 escapes only undecodable bytes via backslashreplace, so 0x0A passes through; outbox.py:56 _SENT_LINE matches any line of the form <64 hex>\\s+<name>, and outbox.py:507 feeds every match into sent_digests, which outbox.py:561-563 uses to skip a file without checking it",
    "A3-rename-after-send-and-the-unchanged-tests-claim": "tests/test_outbox.py:940-948 — the docstring now reads \"The first batch is committed by hand — a `send` would list the draft's hash in the sent manifest, and the renamed file would skip as already sent\", and the body replaces main([\"outbox\",\"send\"]) with _git(repo, \"add\", ...)/_git(repo, \"commit\", ...); the refusal path is src/agentmarshal/outbox.py:818-820, reached before _staged_paths at outbox.py:822 so the staged rename is left in the index",
    "A4-design-says-matching-never-uses-the-name": "openspec/changes/archive/2026-10-24-outbox-skips-sent/design.md:45-46 (\"matching never uses it, only the digest does\") against the same file's lines 47-53 and src/agentmarshal/outbox.py:508 (manifest_names.add(match.group(2))) and outbox.py:564 (elif is_draft and name in manifest_names)"
  }
}
AGENTMARSHAL_VERDICT_END
