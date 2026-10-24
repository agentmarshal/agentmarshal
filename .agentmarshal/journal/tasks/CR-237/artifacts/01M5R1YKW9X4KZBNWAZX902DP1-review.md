Проверил контракт, диф и файлы в снапшоте. Ниже — по критериям, потом advisory-находки.

**Критерий 1 (mark на gate и report).** Выполнен. Gate: `src/agentmarshal/journal/gate.py:1841-1857` — одна `git log` по `merge-base..candidate` (`_range_writer_identities`, gate.py:505-551) отдаёт сразу и emails-only множество для reviewer-independence (gate.py:1948-1952, тот же guard `latest is not None`, что и раньше), и names+emails для метки; PASS-строка дописывает `report.SELF_ACCEPTED_MARK`. Демонстрируют `tests/test_self_acceptance_on_every_surface.py::test_the_gates_acceptance_line_marks_a_self_acceptance` (параметризован по email/регистру/имени), `::test_the_gates_acceptance_line_marks_a_committer_self_acceptance` и `::test_an_acceptance_by_another_party_prints_unmarked`. Report: `report.py:609-613` + `report.py:921-930` (`\tself-accepted` после `decision=`, `unmeasured` остаётся последним); демонстрируют `::test_reports_task_line_marks_a_self_acceptance`, `::test_reports_task_line_marks_a_committer_self_acceptance`, `::test_reports_task_line_prints_unmarked_when_the_check_cannot_run`. Repository для lookup — `placement.host_root` (`report.py:453-467`), ровно то, что передаёт status (`cli.py:1525`), так что sidecar-размещение читает writers в host-репозитории.

**Критерий 2 (decision по completed-записи).** Выполнен: `report.py:552-608` берёт последнюю `completed`-запись, режет историю по `records[:completed_index]` и решает по биндингу (`completed_commit`/`completed_finding`) — approving latest review выигрывает, иначе последняя findings-acceptance на том же биндинге. Биндинг валидатор гарантирует ровно одним полем (`records.py:670`), так что `completed["completed_commit"]` без KeyError. Демонстрируют `::test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved`, `::test_a_commit_approved_after_its_own_acceptance_reports_approved`, `::test_a_commit_completed_over_findings_reports_accepted_over_findings`, `::test_a_finding_completed_over_findings_reports_accepted_over_findings`, `::test_an_acceptance_bound_to_another_commit_leaves_no_decision`, `::test_a_review_written_after_the_completion_does_not_change_its_decision`, `::test_a_task_with_no_completed_record_keeps_todays_decision_rule`.

**Критерий 3 (delta + archive).** Выполнен: delta лежит в `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/specs/operator-acceptance/spec.md`; MODIFIED-блок воспроизводит heading и все шесть сценариев требования «Readers keep acceptance over findings…» слово в слово (сверил с `openspec/specs/operator-acceptance/spec.md:119-168`), ADDED-требования приземлились в `spec.md:316-404`, change-директория переехала под `changes/archive/` с датным префиксом. Все 11 ADDED-сценариев названы в docstring-ах нового тестового файла; шесть MODIFIED сохраняют свои тесты в `tests/test_pause_and_operational_acceptance.py` (378/418/493/573/628/656/713). Других требований с byte-for-byte output-клаузой в operator-acceptance нет, и ни один другой spec не фиксирует строку `accepted over findings` или `decision=`.

**Критерий 4 (сегодняшний вывод без self-acceptance).** Выполнен: status считает ту же тристейт-логику через вынесенные функции (`status_view.py:61-66`), а метка в summary — та же константа (`status_view.py:787-790` ≡ прежний литерал); gate при несовпадении даёт `mark = ""`, т.е. прежние байты (`gate.py:1849-1857`); экранирование не изменилось — `say` экранирует всю строку (`gate.py:150`), report экранирует те же значения. Пины: `tests/test_status_view.py:262,283`, `tests/test_pause_and_operational_acceptance.py:713`. Полную CI-последовательность я не запускал (read-only, sandbox не даёт исполнять) — опираюсь на твою записку о прохождении на 9279604c.

Отдельно проверил, что новый `%an%x00%ae%x00%cn%x00%ce%x00`-разбор не уезжает по сетке: `--format` с `%`-плейсхолдерами git трактует как `tformat:`, т.е. терминатор-newline после каждой записи попадает в начало следующего поля-имени (индекс `%4==0`) и срезается `strip()`, а хвостовой элемент после последнего NUL пуст и отбрасывается; пустой range даёт `(set(), set())`.

Advisory-находки:

- `ADV-gate-report-writer-set-divergence`: gate выводит метку из writers всего диапазона `merge-base..candidate` (`gate.py:1841-1842`), а `report`/`status` — только из writers самого accepted-коммита (`report.py:530-536`, `status_view.py:63-66`), поэтому при multi-commit кандидате сторона, написавшая промежуточный коммит но не tip, получает `self-accepted` в транскрипте gate и ничего в `report`/`status` — это расходится с обещанием ADR-0007 decision 4 «every surface that reports the task says so» и с одной условной фразой нового требования `spec.md:316-323`, которая выдаёт одно условие сразу на две поверхности (сценарии ниже, `spec.md:326-338`, формулируют уже два разных). То же расхождение даёт не-UTF-8 имя автора: gate декодирует имена лоссово и метку ставит (`gate.py:535-541`, тест `::test_the_gate_runs_over_an_author_name_that_is_not_utf8`), а `declared_commit_writers` строго декодирует весь вывод и возвращает `None` (`report.py:491-493`), так что report печатает без метки. Для report это неустранимо — запись acceptance называет только коммит, никакого range у него нет, — поэтому находка не блокирующая, но прозу требования стоит привести к двум условиям.
- `ADV-proposal-shared-lookup-claim`: в `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/proposal.md` раздел Impact говорит, что общий «writer lookup and comparison — `declared_commit_writers` и `accepting_party_is_declared_writer`» применяется «by the gate over the candidate's commit range», тогда как gate использует только comparison и держит собственный ридер `_range_writer_identities` (`gate.py:505-551`) с другими правилами декодирования; поправка к контракту («gate, report and status must share one writer lookup and comparison») этим текстом выглядит выполненной сильнее, чем на самом деле — design.md формулирует честнее («One shared comparison, three surfaces»).
- `ADV-finding-lane-mark-test`: тест `::test_a_finding_completed_over_findings_reports_accepted_over_findings` берёт accepting party `"op"`, которая не совпала бы ни с каким writer и при наличии `accepted_commit`, поэтому отличительную половину сценария (`spec.md:384-386`: метки нет именно потому, что у finding-биндинга нет `accepted_commit`) тест не изолирует; рядом нет и теста на ветку «нет `completed`-записи, последняя findings-acceptance — self-acceptance → метка», которую design.md утверждает.

Блокирующих дефектов не нашёл.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9279604c58c939a80af405b6e24963f1456f39a2",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-gate-report-writer-set-divergence",
    "ADV-proposal-shared-lookup-claim",
    "ADV-finding-lane-mark-test"
  ],
  "classes": {
    "ADV-gate-report-writer-set-divergence": "contract-mismatch",
    "ADV-proposal-shared-lookup-claim": "claim-accuracy",
    "ADV-finding-lane-mark-test": "test-gap"
  },
  "verification": {
    "read": [
      "src/agentmarshal/journal/report.py:420-670,900-945",
      "src/agentmarshal/journal/gate.py:150-260,288-340,498-551,1780-1970",
      "src/agentmarshal/journal/status_view.py:50-90,750-795",
      "src/agentmarshal/journal/placement.py:1-100",
      "src/agentmarshal/journal/records.py:2027-2041,660-680,2190-2235",
      "src/agentmarshal/cli.py:1520-1530",
      "openspec/specs/operator-acceptance/spec.md (full requirement list; 119-168 and 316-404 compared against the change's delta line by line)",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/{proposal.md,design.md,tasks.md,specs/operator-acceptance/spec.md}",
      "docs/adr/ADR-0007-operator-acceptance.md:95-190",
      "tests/test_self_acceptance_on_every_surface.py",
      "tests/test_pause_and_operational_acceptance.py (scenario docstrings; 656-745)",
      "tests/test_status_view.py:255-290",
      "tests/test_acceptance.py:195-230"
    ],
    "executed": [
      {
        "what": "grep -rn 'accepted over findings' src/ openspec/specs/",
        "result": "only status_view.py:778, gate.py:220 (findings lane), gate.py:1855 (commit lane); no other capability spec pins the line"
      },
      {
        "what": "grep -rn 'decision=' openspec/specs/ docs/",
        "result": "only operator-acceptance scenarios and the docs/sidecar.md:335 sample line; no other spec pins report's field order"
      },
      {
        "what": "grep -rn '_range_emails|_declared_commit_writers' --include=*.py .",
        "result": "no remaining references anywhere, so the two removals left no caller behind"
      },
      {
        "what": "grep -rn 'self-accepted' tests/",
        "result": "status's record-line and summary marks stay pinned at tests/test_status_view.py:283 and :262 after test_pause_and_operational_acceptance.py dropped its own copies"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "read-only review in a non-git snapshot; the sandbox refused command execution beyond file reads and greps, so I rely on the coordinator's note that the sequence passed on 9279604c"
      },
      {
        "what": "a scripted byte comparison of the delta's MODIFIED requirement against openspec/specs/operator-acceptance/spec.md, and a git probe of the %x00 log format",
        "why": "python execution was denied by the sandbox; both were checked by reading the two texts and by git's documented tformat terminator semantics instead"
      }
    ]
  },
  "evidence": {
    "ADV-gate-report-writer-set-divergence": "src/agentmarshal/journal/gate.py:1841-1842 computes the mark's identities over `merge_base..resolved_commit`, while src/agentmarshal/journal/report.py:530-536 and src/agentmarshal/journal/status_view.py:63-66 compare against `declared_commit_writers(repository, acceptance['accepted_commit'])` alone; openspec/specs/operator-acceptance/spec.md:316-323 states one condition (\"a declared writer of the candidate\") for both surfaces while spec.md:326-338 splits it into range vs accepted commit. Decode divergence: gate.py:535-541 (names decode with errors='replace', so the mark is still derived) vs report.py:491-493 (strict decode of the whole output; UnicodeDecodeError -> None -> no mark), asserted by tests/test_self_acceptance_on_every_surface.py::test_the_gate_runs_over_an_author_name_that_is_not_utf8.",
    "ADV-proposal-shared-lookup-claim": "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/proposal.md, Impact: \"holds the shared writer lookup and comparison - declared_commit_writers and accepting_party_is_declared_writer ... applied by the gate over the candidate's commit range\"; grep -n 'declared_commit_writers' src/agentmarshal/journal/gate.py returns nothing - the gate imports only SELF_ACCEPTED_MARK and accepting_party_is_declared_writer (gate.py:64-68) and reads writers through its own _range_writer_identities (gate.py:505-551).",
    "ADV-finding-lane-mark-test": "tests/test_self_acceptance_on_every_surface.py::test_a_finding_completed_over_findings_reports_accepted_over_findings passes accepted_by=\"op\" with accepted_finding set, so report.py:530 returns False on the missing `accepted_commit` and the party value is never exercised; no test in the file drives the no-completed-record branch (report.py:600-608) with a self-accepting party, which design.md's \"A task with no `completed` record keeps today's rule ... marked when its latest such acceptance is a self-acceptance\" asserts."
  }
}
AGENTMARSHAL_VERDICT_END
