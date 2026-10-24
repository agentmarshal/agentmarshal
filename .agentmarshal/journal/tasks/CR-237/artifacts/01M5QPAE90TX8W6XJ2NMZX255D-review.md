Прочитал дифф, оба изменённых модуля, их status-аналог, спеку и новые тесты. Ниже проза по находкам и по каждому acceptance-критерию.

## Находки

**REP-WRITER-FORMAT-MISSING-NEWLINE (blocking, correctness).** В `src/agentmarshal/journal/report.py:454` формат git — `--format=%an%n%ae%n%cn%ce` — не содержит `%n` между `%cn` и `%ce`, тогда как status-аналог в `src/agentmarshal/journal/status_view.py:58` использует `%an%n%ae%n%cn%n%ce`. Из-за этого имя и e-mail коммиттера склеиваются в один токен («Committercommitter@x.invalid») и `_declared_commit_writers` в `report.py` возвращает **не тот** набор, что в `status`: для любого коммита, где коммиттер отличается от автора (rebase, cherry-pick, squash-merge, `--author`, amend оператором — ровно тот случай, который ADR-0007 решение 4 называет главным: агент пишет код под git-identity оператора, оператор коммитит и сам же принимает), acceptance от коммиттера `status` помечает `self-accepted`, а `report` печатает строку без метки. Это противоречит ADR-0007 решению 4 («every surface that reports the task says so»), формулировке добавленного требования в `openspec/specs/operator-acceptance/spec.md:313-318` («the case-insensitive comparison the surface already makes») и делает ложным сам docstring `report.py:443-445` («The same query and the same reading of it `status` makes»). Ложных «self-accepted» баг не даёт — только пропуски метки, то есть ошибка всегда в сторону сокрытия самопринятия. Сам git я здесь выполнить не смог (sandbox отклонил запуск), находка получена чтением двух строк исходников; что `%n` — это именно перевод строки, на который опирается `splitlines()`-разбор, видно из обоих модулей.

**TEST-NO-DISTINCT-COMMITTER (advisory, test-gap).** Ни одна фикстура не создаёт коммит, у которого коммиттер отличается от автора: `tests/test_self_acceptance_on_every_surface.py:60-78` коммитит через `-c user.name=Test -c user.email=test@example.invalid`, `tests/test_gate.py:42,99` — через `_WRITER`, `tests/test_journal.py:66-75` — так же. Поэтому паритет метки с `status`, который требует критерий 1, не демонстрируется ни одним тестом, и находка выше проходит через весь suite незамеченной.

**REP-UNCHECKED-COLLAPSED (advisory, correctness).** `TaskReport.self_accepted` — `bool` (`report.py:139`, `_self_accepted` в `report.py:483-500`), поэтому «git не смог ответить» и «не самопринятие» в `report` печатаются одинаково, тогда как `status` различает три состояния и печатает `self-acceptance-unchecked`; docstring `status_view.py:71-77` прямо предупреждает, что неотвечаемый запрос, показанный как «not self-accepted», «quietly lose exactly that». Решение задокументировано в `design.md` («An unanswerable check prints no mark on `report`») и покрыто сценарием спеки, поэтому это advisory, а не блок; но именно оно делает пропуски метки из первой находки визуально неотличимыми от законной непомеченной строки.

## Acceptance-критерии

1. **Метка на обеих поверхностях.** Gate: `gate.py:1785-1811` — набор writer-эмейлов поднят выше verdict-блока и переиспользован проверкой независимости (`gate.py:1903`), условие и текст метки совпадают со спекой; демонстрируют `test_the_gates_acceptance_line_marks_a_self_acceptance` (параметризован по регистру) и `test_an_acceptance_by_another_party_prints_unmarked`. Report: `report.py:880-884` плюс `_writers_repository`/`_self_accepted`, демонстрирует `test_reports_task_line_marks_a_self_acceptance`. Критерий выполнен для gate и выполнен для `report` **только** на коммитах, где автор совпадает с коммиттером — см. REP-WRITER-FORMAT-MISSING-NEWLINE.
2. **Решение по binding завершённой записи.** `report.py:516-570`: `completed_commit`/`completed_finding` выбирают ключи `reviewed_*`/`accepted_*`, approved побеждает, иначе последний acceptance с `findings`, привязанный к тому же binding; задача без `completed` сохраняет прежнее правило. Демонстрируют `test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved`, `test_a_commit_completed_over_findings_reports_accepted_over_findings`, `test_a_finding_completed_over_findings_reports_accepted_over_findings`, `test_an_acceptance_bound_to_another_commit_leaves_no_decision`, `test_a_task_with_no_completed_record_keeps_todays_decision_rule`. Выполнен.
3. **Дельта и архив.** `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/` содержит proposal/design/tasks/specs; MODIFIED-требование «Readers keep acceptance over findings to the acceptances that carry findings» перенесено с заголовком байт-в-байт и всеми шестью сценариями — сверил с `openspec/specs/operator-acceptance/spec.md:119-168`; других требований этой capability с byte-for-byte-клаузой по выводу, которых касается метка, нет (требование у `spec.md:281-315` — про поведение `accept`, не про вывод). Два ADDED-требования и все восемь их сценариев названы в docstring-ах тестов `tests/test_self_acceptance_on_every_surface.py`. Выполнен; сам `openspec archive` и `openspec validate` я не запускал (read-only, snapshot — не git-репозиторий), проверял результат по содержимому.
4. **Неизменность сегодняшнего вывода и escaping.** Метка gate добавляется только при совпадении, метка `report` — только при решающем self-acceptance; единственный изменённый пин, `test_every_output_for_an_acceptance_over_findings_is_unchanged` (`tests/test_pause_and_operational_acceptance.py:683-714`), переведён на сторону «op» синхронно с суженным WHEN сценария, а пины self-accepted-вывода `status` остались в `tests/test_pause_and_operational_acceptance.py:591-600,640-649`, `tests/test_status_view.py:262-286` и `tests/test_acceptance.py:185-229`. Новая метка — литерал инструмента, `accepted_by` интерполируется там же, где и раньше, escaping не менялся. Полную CI-последовательность и pytest я здесь не выполнял (read-only; snapshot вне git) — опираюсь на твою заметку о прохождении на a71228f. Выполнен.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "a71228fffb8477c5c45e77835ea6c46770ef90bc",
  "verdict": "changes_required",
  "findings": ["REP-WRITER-FORMAT-MISSING-NEWLINE"],
  "advisory_findings": ["TEST-NO-DISTINCT-COMMITTER", "REP-UNCHECKED-COLLAPSED"],
  "classes": {
    "REP-WRITER-FORMAT-MISSING-NEWLINE": "correctness",
    "TEST-NO-DISTINCT-COMMITTER": "test-gap",
    "REP-UNCHECKED-COLLAPSED": "correctness"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"_declared_commit_writers|%an|%ae|%cn|%ce\" src/ tests/", "result": "report.py:454 '--format=%an%n%ae%n%cn%ce' vs status_view.py:58 '--format=%an%n%ae%n%cn%n%ce'"},
      {"what": "grep -rn \"build_report|\\.decision|accepted-over-findings\" --include=*.py src/", "result": "only cli.py:1392 consumes build_report; no other surface derives the decision"},
      {"what": "grep -n \"resolved_commit = |merge_base = \" src/agentmarshal/journal/gate.py", "result": "assigned once at 1184/1186 — hoisting _range_emails above the verdict block cannot change the set"},
      {"what": "grep -n \"print_task_detail|host_root\" src/agentmarshal/cli.py", "result": "cli.py:1525 passes placement.host_root to status — same root report._writers_repository resolves"},
      {"what": "grep -rn \"self-accept|self_accept\" tests/", "result": "status's marks still pinned in test_status_view.py:262-286, test_pause_and_operational_acceptance.py:591-649, test_acceptance.py:185-229"},
      {"what": "grep -n \"byte|unchanged|identical\" openspec/specs/operator-acceptance/spec.md", "result": "only the MODIFIED requirement at 119-168 carries an output byte-for-byte clause the mark touches"},
      {"what": "grep -n \"_validate_binding\" -A 35 src/agentmarshal/journal/records.py", "result": "accepted_commit is validated as exactly 40 lowercase hex on read — no option-injection into git show"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py:400-650,820-930",
      "src/agentmarshal/journal/gate.py:470-520,1680-1940",
      "src/agentmarshal/journal/status_view.py:40-170,772-800",
      "src/agentmarshal/journal/placement.py:48-95",
      "src/agentmarshal/journal/records.py:1824-1853,2027-2041",
      "openspec/specs/operator-acceptance/spec.md:108-172,270-320",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/ (proposal.md, design.md, tasks.md, specs/operator-acceptance/spec.md)",
      "docs/adr/ADR-0007-operator-acceptance.md:104-188",
      "tests/test_self_acceptance_on_every_surface.py",
      "tests/test_pause_and_operational_acceptance.py:560-715",
      "tests/test_gate.py:36-308",
      "tests/test_quickstart.py:120-170",
      "docs/quickstart.md:477-486"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review and the snapshot is not a git repository; relying on the coordinator's note that the sequence passed on a71228f"},
      {"what": "a git repo reproducing a commit whose committer differs from its author, to print both format strings side by side", "why": "the sandbox refused the git/mkdir commands and the script run; the divergence is shown by report.py:454 against status_view.py:58 instead"},
      {"what": "openspec validate / openspec archive", "why": "read-only review, no node/openspec invocation attempted; the archived delta and the updated spec were compared by reading"}
    ]
  },
  "evidence": {
    "REP-WRITER-FORMAT-MISSING-NEWLINE": "src/agentmarshal/journal/report.py:454 `[\"git\", \"show\", \"-s\", \"--format=%an%n%ae%n%cn%ce\", commit]` — no %n between %cn and %ce, so the committer name and email land on one line and the set parsed at report.py:464 holds their concatenation; src/agentmarshal/journal/status_view.py:58 `--format=%an%n%ae%n%cn%n%ce` is the comparison report.py:443-445 and openspec/specs/operator-acceptance/spec.md:313-318 claim it makes",
    "TEST-NO-DISTINCT-COMMITTER": "tests/test_self_acceptance_on_every_surface.py:60-78 commits with `-c user.name=Test -c user.email=test@example.invalid`; tests/test_gate.py:42 `_WRITER = [\"-c\", \"user.name=Worker\", \"-c\", \"user.email=worker@test.invalid\"]` used at tests/test_gate.py:99; tests/test_journal.py:66-75 likewise — author and committer coincide in every fixture",
    "REP-UNCHECKED-COLLAPSED": "src/agentmarshal/journal/report.py:139 `self_accepted: bool = False` and report.py:494-500 return False both for `repository is None`/no `accepted_commit` and for an unanswerable `git show`; status_view.py:71-84 returns `bool | None` and status_view.py:170 prints the `self-acceptance not checked` form instead"
  }
}
AGENTMARSHAL_VERDICT_END
