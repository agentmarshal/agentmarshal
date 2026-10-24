Проверил diff против контракта, прочитал код, на который ссылаются оба дайджеста.

## Findings

**ADV-README-EVERY-FILE-IS-A-DRAFT** — `docs/proposals/README.md:82` в аннотации батча пишет, что outbox не проходит `check`, «because every file it holds is judged as a draft». Это противоречит и самому дайджесту (`045:21-22` — «`README.md` is skipped, as designed»), и коду: `src/agentmarshal/outbox.py:456` (`is_draft = entry.name != _README`) выводит README из field-check, а `outbox.py:451` сообщает про не-regular запись `not a draft, not checked` — то есть отказ происходит не потому, что драфтом признан каждый файл. Мелкая неточность в сводке, не в дайджесте; поэтому advisory, не блокер.

**ADV-044-ZERO-SIGNAL-AMBIGUITY** — `docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:77-79` объявляет для 0.6.0 правило чтения старых записей по сигналу «три счётчика в нуле и нет объекта `usage`», хотя тот же файл на строках 33-34 утверждает обратное: «the zero cannot be told apart from a measured zero later». `docs/quickstart.md:547-550` прямо предписывает опускать оба usage-флага всегда, когда provenance недоступен, так что сессия с настоящим измеренным нулём и без флагов попадёт под тот же сигнал и будет показана как `unmeasured`. Остаточная неоднозначность в disposition не оговорена. Advisory: это рассуждение о будущем релизе, а не утверждение о текущем поведении.

## Acceptance criteria

**AC1 (дайджест 044)** — выполнен. Source-строка `sha256:816c7ff8…57b0d` совпадает с контрактом побайтно (`044:3`), «Observed on: 0.4.1, rechecked on 0.5.0» на месте, форма совпадает с существующими дайджестами A (`025:3`, `026:3` — тот же reporter-line «Adopter A (Python web service on Linux)», разделы Finding / Proposed / Disposition / Where). Disposition разнесён ровно так, как требует контракт: reading side в 0.6.0, write side со следующей record schema в 0.7.0 (`044:73-103`). Фактические утверждения проверены по коду: `cli.py:407-411` (дефолты `0`, `--usage-method` только `reported|measured` в паре с `--usage-provider`), `journal/records.py:2313-2330` (`tokens` пишется всегда), `journal/records.py:778-794` (правило `session-tokens` требует ровно три неотрицательных int), `journal/report.py:173-180` (`unrecorded`), `journal/report.py:364-365` (сумма `tokens` по всем session-записям), `journal/report.py:291-335` (`sessions_without_cost` считается отдельно, нулём не усредняется), `docs/quickstart.md:547-550` (указание опускать usage-флаги). Теста, демонстрирующего этот критерий, в репозитории нет: `grep -rl proposals tests/` даёт единственный файл `tests/test_project.py`, и он проверяет scaffold-README из `project.py`, а не дайджесты.

**AC2 (дайджест 045)** — выполнен. Source-строка `sha256:a819341c…11008` совпадает с контрактом, «Observed on: 0.5.0», disposition — пропуск уже отправленных файлов в `check`/`send` по sent-манифесту или индексу `outbox status`, в 0.6.0 (`045:76-111`). Механика проверена по коду: `outbox.py:410-520` (`_check` обходит все записи, пять полей `_FIELDS` как точные `## <Field>` через `_HEADING = ^## (.+?)\s*$`), `outbox.py:451` (`not a draft, not checked` и отказ), `outbox.py:655-710` (`_run_send` запускает тот же `_check` и делает `git add --force -- .agentmarshal/upstream`, где `_OUTBOX_DIR_SPEC` — ровно этот путь), `outbox.py:767-833` (`status` хеширует файлы sha256 и сверяет с `Source:`-строками индекса из `--index`), `CHANGELOG.md:150-158` (группа действительно вышла в 0.5.0). Противоречия с ADR-0020 нет: disposition сохраняет правило решения 3 (`docs/adr/ADR-0020…:85-87` — leak scan по тому, что уйдёт) и освобождение манифеста согласуется с существующим исключением README. Теста нет — по той же причине, что и у AC1.

**AC3 (индекс)** — выполнен. Секция «Batch of 2026-10-24» вставлена перед «Batch of 2026-10-03», порядок «новые сверху» сохранён, строки таблицы в том же формате `| # | Theme | Reporter | Disposition | Where |`, что и батчи 2026-10-03 / 2026-10-01 / 2026-09-24. Теста нет; косвенно индекс затрагивает `tests/test_project.py::test_outbox_readme_says_how_a_sent_finding_is_matched` (он требует, чтобы scaffold-README ссылался на `docs/proposals/README.md` и на раздел «Tracking what happened to yours») — ни то, ни другое diff не ломает.

**AC4 (приватность и язык)** — выполнен. Идентификаторов репозитория адоптера нет: ни номеров задач, ни ULID, ни путей его journal/скриптов, ни имён людей, провайдерского аккаунта или продукта. Единственные пути — `.agentmarshal/upstream/` и `src/agentmarshal/outbox.py`, оба принадлежат AgentMarshal. Текст полностью английский — скан не-ASCII даёт только `—` и `·`, как в соседних дайджестах. Все добавленные ссылки резолвятся: `../adr/ADR-0020-the-outbox-command-group.md`, `025-validate-refused-records-an-earlier-release-wrote.md`, `026-reviewer-facts-round-convergence-and-two-gaps.md`, `044-…md`, `045-…md` — проверил `ls`, все существуют; в 044 ссылок нет вовсе. Теста нет.

**AC5 (нет других изменений; CI зелёный)** — выполнен по предоставленному diff: тронуты ровно три файла из scope. Прогон CI я не делал (read-only, запуск pytest в этой сессии недоступен) — опираюсь на утверждение координатора о зелёной последовательности на `b13db0d`; markdown-линтера в `gitflic-ci.yaml` нет, так что изменённые `.md` ни одним шагом CI и не проверяются. Отдельного теста, демонстрирующего этот критерий, нет — его демонстрирует сам полный прогон `pytest`.

Блокирующих находок нет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b13db0dfbf9b9ce9b5877733b8420512c2ac603b",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-README-EVERY-FILE-IS-A-DRAFT",
    "ADV-044-ZERO-SIGNAL-AMBIGUITY"
  ],
  "classes": {
    "ADV-README-EVERY-FILE-IS-A-DRAFT": "claim-accuracy",
    "ADV-044-ZERO-SIGNAL-AMBIGUITY": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'input-tokens|output-tokens|cache-tokens|usage-method|usage-provider' src/agentmarshal/cli.py", "result": "cli.py:407-411 — all three token flags default=0; --usage-method choices=('reported','measured'); --usage-provider free text; cli.py:1296-1306 pairs them"},
      {"what": "read src/agentmarshal/journal/records.py:2272-2332 (create_session_record)", "result": "record always carries tokens={input,output,cache}; usage added only when usage_provider is not None"},
      {"what": "read src/agentmarshal/journal/records.py:778-794 (@_rule('session-tokens'))", "result": "tokens must be a dict with exactly keys {input,output,cache}, each type int and >= 0 — no shape for an absent/null tokens object"},
      {"what": "grep -rn 'unrecorded|sessions_without_cost' src/agentmarshal/ and read report.py:173-180, 291-335, 364-365", "result": "report.py:178 renders absent usage as 'unrecorded'; report.py:364-365 sums the tokens object of every session record; report.py:291-335 counts sessions carrying no cost apart as sessions_without_cost"},
      {"what": "read docs/quickstart.md:530-560", "result": "line 547-550: 'Omit both usage flags when the provenance is unavailable; the report calls those counts unrecorded rather than silently treating them as provider-reported.'"},
      {"what": "read src/agentmarshal/outbox.py:396-520 (_is_regular, _check) and :315-349 (_field_bodies, _missing_unfilled), :57 (_FIELDS), :80 (_HEADING)", "result": "iterates every sorted entry; non-regular -> prints '<name>: not a draft, not checked' and sets refused; is_draft = entry.name != 'README.md'; five fields Symptom/Measurements/Version/Environment/Expected matched by ^## (.+?)\\s*$"},
      {"what": "read src/agentmarshal/outbox.py:655-750 (_run_send) and :51-52 (_OUTBOX_DIR_SPEC)", "result": "_run_send calls _check(pin=True) and refuses on non-zero; stages with _git(project_root, ['add','--force','--','.agentmarshal/upstream'])"},
      {"what": "read src/agentmarshal/outbox.py:758-833 (_SOURCE_LINE, _run_status)", "result": "status sha256-hashes each regular outbox file and matches it against Source: sha256 lines of the --index file"},
      {"what": "read docs/adr/ADR-0020-the-outbox-command-group.md:60-135", "result": "decision 3 — check names the missing field per non-conforming draft and runs the merge boundary's leak scan over what would be sent; decision 5 — status hashes outbox files against an index's Source: lines. The digest's disposition preserves the leak-scan rule it cites"},
      {"what": "grep -n outbox CHANGELOG.md; sed -n 150,158p CHANGELOG.md", "result": "'### The outbox is a command group (CR-150, CR-156)' under the 0.5.0 — 2026-10-23 heading: new/check/send/status shipped in 0.5.0, as 045 states"},
      {"what": "ls of every relative link target added by the diff (../adr/ADR-0020-the-outbox-command-group.md, 025-*.md, 026-*.md, 044-*.md, 045-*.md)", "result": "all five exist; 044 adds no links"},
      {"what": "grep -nP '[^\\x00-\\x7F]' on both new digests, excluding lines whose only non-ASCII are em dash / middot", "result": "no output — the files are English with only the typographic characters the existing digests use"},
      {"what": "grep -o 'sha256:[0-9a-f]{64}' on both new digests", "result": "044 -> 816c7ff8e0ad09bd1bc55f0030897758eba0a539c0da556744de745a76e57b0d; 045 -> a819341cbe9022523a08b200c6ee92e687335c6b83fd4b12a88b22b35a411008 — both identical to the contract's"},
      {"what": "grep -rln proposals tests/", "result": "only tests/test_project.py, which asserts the init-scaffolded outbox README text (project.py:232-277), not the digest files — no test covers docs/proposals content"},
      {"what": "grep -n '^#|^- \\*\\*Reporter' on 025, 026, 041, 043", "result": "same reporter-line shape and the Finding / Proposed / Disposition / Where section order the new digests follow; 025/026 carry the identical 'Adopter A (Python web service on Linux)' profile"}
    ],
    "read": [
      "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md",
      "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md",
      "docs/proposals/README.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/adr/ADR-0019-accounting-time-quota-resets-money.md (decisions 3-5 and the 'how it works today' list)",
      "docs/quickstart.md:530-565",
      "UPGRADING.md:65-85",
      "CHANGELOG.md:1-60 and :145-165",
      "CONTRIBUTING.md (grep for outbox)",
      "gitflic-ci.yaml",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/project.py:232-331",
      "src/agentmarshal/cli.py:400-420, 1290-1310",
      "src/agentmarshal/journal/records.py:770-812, 2272-2335",
      "src/agentmarshal/journal/report.py:165-190, 291-340, 360-470, 640-730",
      "tests/test_project.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "read-only review and command execution was not permitted in this session; relying on the coordinator's statement that the full sequence passed on b13db0dfbf9b9ce9b5877733b8420512c2ac603b, and noting that no CI step lints Markdown, so the three changed files are not exercised by it"},
      {"what": "git status / git diff to confirm no file outside the contract's scope changed", "why": "the snapshot is not a git repository; the 'no other file changes' criterion is judged from the supplied diff, which touches exactly the three scoped paths"}
    ]
  },
  "evidence": {
    "ADV-README-EVERY-FILE-IS-A-DRAFT": "docs/proposals/README.md:82 ('because every file it holds is judged as a draft') contradicted by docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:21-22 ('`README.md` is skipped, as designed') and by src/agentmarshal/outbox.py:456 ('is_draft = entry.name != _README') together with src/agentmarshal/outbox.py:451 (print(f\"{safe_path(name, markers)}: not a draft, not checked\"))",
    "ADV-044-ZERO-SIGNAL-AMBIGUITY": "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:77-79 ('the signals are the ones the finding names — the three counts at zero and no `usage` object') against the same file's 044:33-34 ('because the zero cannot be told apart from a measured zero later') and docs/quickstart.md:547-550 ('Omit both usage flags when the provenance is unavailable'), which together make a genuinely measured-zero session carry exactly that signal"
  }
}
AGENTMARSHAL_VERDICT_END
