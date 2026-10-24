Проверил diff против контракта, кода и названных решений. Вот что нашёл.

**Разбор по acceptance criteria**

1. **AC1 (digest 044)** — выполнен: `docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:3` несёт reporter-строку в форме существующих digest'ов (сравнил с `026:3` и `043:3`), Source `sha256:816c7ff8…e57b0d`, «Observed on: 0.4.1, rechecked on 0.5.0», секции Finding / Proposed / Disposition / Where как у 041, 043. Disposition разделён ровно так, как требует контракт: reading side в 0.6.0, write side со следующей record schema в 0.7.0 (`044:67`, `044:91-96`). Автоматического теста на содержимое digest'ов в репозитории нет — на `docs/proposals/` ссылается только `tests/test_project.py:31-44`, и то про README проекта; критерий демонстрируется самим файлом, фактические утверждения я проверил по коду (`cli.py:407-411`, `journal/records.py:2313-2331`, `records.py:778-791`, `report.py:363-366`).
2. **AC2 (digest 045)** — выполнен: `045:3` даёт Source `sha256:a819341c…411008` и «Observed on: 0.5.0», disposition в `045:72-83` — `outbox check` и `outbox send` пропускают уже отправленные файлы (по манифесту, который пишет `send`, либо по index-файлу `outbox status`) в 0.6.0. Описание механизма сверено с `src/agentmarshal/outbox.py:433-456` (каждый regular file кроме `README.md` — draft; не-regular entry даёт `not a draft, not checked` и отказ), `outbox.py:655-712` (`_run_send` гоняет тот же `_check`, затем `git add --force -- .agentmarshal/upstream`), `outbox.py:99-112, 764` (`status --index` по `Source:`-строкам). Утверждение «нет флага или конфиг-ключа, меняющего набор проверяемых файлов» тоже верно: `check` регистрируется без аргументов (`outbox.py:100-102`). Теста нет по той же причине.
3. **AC3 (индекс README)** — выполнен: `docs/proposals/README.md:72-90`, батч вставлен новейшим сверху (перед 2026-10-03), таблица той же пятиколоночной формы, что у батчей 2026-10-03 и 2026-09-24. Тестов нет.
4. **AC4 (без идентификаторов адоптера, English only, ссылки резолвятся)** — выполнен: ULID'ов, номеров задач, имён людей/провайдера/продукта в обоих файлах нет; не-ASCII только `—` и `·`, как в соседних digest'ах; единственная добавленная ссылка `../adr/ADR-0020-the-outbox-command-group.md` существует, как и оба файла, на которые ссылается README.
5. **AC5 (никаких других файлов; CI)** — diff трогает ровно три файла из scope. CI я не запускал (read-only review); по заметке координатора последовательность прошла на cbc38d2.

**Блокирующая находка**

`F1-usage-absence-is-documented` — `docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:19-21` утверждает, что отсутствующий объект `usage` — «the only trace that the figures were not reported, **and nothing documents that reading**». Это прямо опровергается собственной документацией проекта: `docs/quickstart.md:548-550` («Omit both usage flags when the provenance is unavailable; the report calls those counts unrecorded rather than silently treating them as provider-reported») и `CHANGELOG.md:552-553` (`usage=reported|measured|unrecorded|mixed`), а сам код это чтение уже реализует — `report.py:174-186` отображает сессию без `usage` как `unrecorded`. Та же неточность тянется в Disposition (`044:69-75`), где «the only signal» для старых записей сводится к трём нулям и отсутствию `usage`, а в качестве «уже существующей формы такого чтения» назван `sessions_without_cost`, хотя ближайшая существующая форма — именно `usage=unrecorded` в том же `report`; и в README (`docs/proposals/README.md:75-77`: «indistinguishable in the journal»). Digest публичный и не отзывается, а это проверяемое читателем утверждение о документации самого проекта — поэтому блокирую: достаточно переписать фразу (например: отсутствие `usage` документировано как неизвестная provenance, но не как отсутствие самих счётчиков) и упомянуть `usage=unrecorded` в reading side.

**Advisory**

`A1-skip-vs-leak-scan` — в `045:72-79` принятое решение сформулировано как «check и send пропускают уже отправленные файлы», без оговорки, что пропускается именно проверка пяти полей, а не leak scan. ADR-0020 decision 3 (`docs/adr/ADR-0020-the-outbox-command-group.md:82-88`) требует, чтобы `check` гонял leak scan «over what would be sent», и код сканирует каждый entry, включая `README.md` и не-draft'ы, ровно по этой причине (`outbox.py:447-455`, комментарий «nothing in the outbox passes in silence», и `outbox.py:672-674, 708-710` — `send` всё равно стейджит весь каталог через `git add --force`). Буквальная реализация «skip» вынесла бы часть байтов, которые `send` по-прежнему стейджит, из-под сканирования. Это не фактическая ошибка digest'а, а недосказанность в диспозиции — одной фразы хватит, чтобы зафиксировать границу пропуска.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "cbc38d2a0a8da6d9fb07608e9aac195e42a71747",
  "verdict": "changes_required",
  "findings": ["F1-usage-absence-is-documented"],
  "advisory_findings": ["A1-skip-vs-leak-scan"],
  "classes": {
    "F1-usage-absence-is-documented": "claim-accuracy",
    "A1-skip-vs-leak-scan": "correctness"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'input-tokens|usage-method' src/agentmarshal/cli.py", "result": "cli.py:407-411 — --input-tokens/--output-tokens/--cache-tokens default=0; --usage-method choices ('reported','measured')"},
      {"what": "sed -n '2313,2331p' src/agentmarshal/journal/records.py", "result": "create_session_record always writes tokens {input,output,cache}; usage object only when usage_provider is not None"},
      {"what": "sed -n '778,791p' src/agentmarshal/journal/records.py", "result": "session-tokens rule: tokens must be a dict with exactly input/output/cache, each int >= 0"},
      {"what": "grep -n 'tokens|sessions_without_cost|_usage_provenance' src/agentmarshal/journal/report.py", "result": "report.py:363-366 sums every session record's tokens; report.py:174-186 renders a session without 'usage' as 'unrecorded'; report.py:106,663 sessions_without_cost"},
      {"what": "grep -n 'unrecorded' docs/quickstart.md CHANGELOG.md", "result": "docs/quickstart.md:550 and CHANGELOG.md:552-553 document the absent-usage reading as 'unrecorded'"},
      {"what": "sed -n '406,530p;655,712p' src/agentmarshal/outbox.py", "result": "_check treats every regular file but README.md as a draft, prints 'not a draft, not checked' for others and refuses; _run_send runs _check then git add --force -- .agentmarshal/upstream"},
      {"what": "grep -n 'check|status|--index' register() in src/agentmarshal/outbox.py", "result": "outbox.py:100-112 — 'check' takes no arguments; 'status' requires --index"},
      {"what": "link resolution for every added link", "result": "docs/adr/ADR-0020-the-outbox-command-group.md, 044-*.md and 045-*.md all exist"},
      {"what": "grep -nP '[^\\x00-\\x7F]' over both digests", "result": "only em dash and middle dot, as in the existing digests; no ULIDs, task numbers, URLs or adopter paths"}
    ],
    "read": [
      "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md",
      "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md",
      "docs/proposals/README.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/adr/ADR-0009-research-findings-lifecycle.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/quickstart.md (record-session section)",
      "CHANGELOG.md (0.5.0 entry)",
      "UPGRADING.md (0.5.0 section)",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/cli.py (record-session parser)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review; the snapshot is not a git checkout and the coordinator states the sequence passed on cbc38d2a"}
    ]
  },
  "evidence": {
    "F1-usage-absence-is-documented": "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:19-21 ('the only trace ... and nothing documents that reading') vs docs/quickstart.md:548-550 ('Omit both usage flags when the provenance is unavailable; the report calls those counts unrecorded ...'), CHANGELOG.md:552-553 ('usage=reported|measured|unrecorded|mixed') and src/agentmarshal/journal/report.py:174-186 (_usage_provenance returns 'unrecorded' for a session record without 'usage'); compounded at docs/proposals/044-...md:69-75 and docs/proposals/README.md:75-77",
    "A1-skip-vs-leak-scan": "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md:72-79 accepts skipping already-sent files without bounding the skip; docs/adr/ADR-0020-the-outbox-command-group.md:82-88 requires check to run the leak scan over what would be sent; src/agentmarshal/outbox.py:447-455 scans every entry ('nothing in the outbox passes in silence') and outbox.py:708-710 stages the whole directory with git add --force"
  }
}
AGENTMARSHAL_VERDICT_END
