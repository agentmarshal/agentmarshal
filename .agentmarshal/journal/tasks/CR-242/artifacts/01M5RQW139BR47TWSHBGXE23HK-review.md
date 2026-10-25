Разобрался. Прочитал весь изменённый код, ADR-0021, итоговый spec, новые и существующие тесты, граф импортов.

**Что сделано и чем подтверждается**

AC1 выполнен. Общая деривация живёт одна: `src/agentmarshal/journal/report.py:552` `acknowledging_party_is_declared_writer` резолвит `recorded_by` через `_actor_git_identities` плюс само записанное имя и прогоняет каждую identity через `accepting_party_is_declared_writer` (`report.py:534`) — второй копии сравнения нет, а `status_view._is_self_acknowledged` (`status_view.py:85`) теперь просто вызывает её, так что `status` и марки выводятся из одного кода. Писательские множества разные по проекту: gate берёт диапазон (`gate.py:2382-2387`, `_range_writer_identities` над `merge_base..resolved_commit`), `leak-scan` — только сканируемый коммит (`cli.py:1802`, `declared_commit_writers`). Демонстрируют: `test_the_standalone_command_marks_a_self_acknowledgement`, `test_the_gate_marks_a_self_acknowledgement_over_the_candidate_range`, `test_the_commits_committer_marks_a_self_acknowledgement`, `test_a_declared_actors_resolved_identity_marks_a_self_acknowledgement`, `test_the_writer_check_folds_case`. Оба условия требование формулирует явно — `openspec/specs/leak-scan/spec.md:819-824`.

Ленивый lookup в gate корректен: `not writer_identities` перечитывает диапазон только тогда, когда verdict-блок вернул `(set(), set())`, то есть когда git-вызова там вообще не было (`gate.py:1926-1929`) — диапазон действительно читается один раз. `GateError` ловится, а `_run_git_bytes` заворачивает в неё и `OSError`, и `UnicodeDecodeError`, так что сбой lookup не роняет gate.

AC2 выполнен. Дельта несёт ADDED-требование и два MODIFIED с полным текущим текстом — диff `openspec/specs/leak-scan/spec.md` показывает только задуманные правки прозы, ни один сценарий не потерян (перечень заголовков спеки это подтверждает). Все восемь сценариев ADDED-требования имеют по тесту, чей докстринг их называет, в `tests/test_self_acknowledgement_mark.py`. Изменение заархивировано командой: `openspec/changes/archive/2026-10-25-self-acknowledgement-mark/` с `specs/leak-scan/spec.md`, рабочая директория `openspec/changes/` пуста кроме `archive`.

AC3 выполнен. Чужая подтверждающая сторона печатается как раньше — `test_an_acknowledgement_by_another_party_prints_unmarked` (точное посимвольное сравнение обеих строк); неотвечаемый git-lookup не метит ничего — `test_a_check_git_cannot_answer_marks_nothing` (gate'овый `_range_writer_identities` поднимает `GateError`, CLI'шный `declared_commit_writers` отдаёт `None`). Рефакторинг `status` поведение не меняет: старое `not identities.isdisjoint(writers)` над уже casefold'ленными identity эквивалентно `any(accepting_party_is_declared_writer(...))`, единственная разница — `record.get("recorded_by")` вместо `record["recorded_by"]`, что только убирает KeyError. Транскриптные фикстуры не содержат ни одной метки подтверждения (`grep "acknowledged by" tests/fixtures/` пуст), а все существующие тесты подтверждают от имени `an-operator`, который писателем не является, — поэтому ни один байт существующего вывода не переключается на `self-acknowledged`.

**Advisory-находка**

ADV-cli-writer-lookup-guard — комментарий в `src/agentmarshal/cli.py:1793-1801` утверждает «The lookup runs only where an acknowledgement could be qualified, as the gate's guard does», но охрана в CLI — это `if acknowledgements:` (`cli.py:1801`), тогда как у gate охрана строго уже: `if leak_hits:` снаружи и `if acknowledgements and not writer_identities:` внутри (`gate.py:2358, 2382`). При чистом скане, но непустом журнале подтверждений CLI всё равно тратит `git show -s`, хотя `hits` посчитаны выше (`cli.py:1756`) и доступны для охраны. На вывод это не влияет — только лишний git-вызов и неточное утверждение в комментарии.

Полную CI-последовательность здесь прогнать не удалось: в снапшоте нет `.venv`, а `uv sync --locked` требует сети; по словам координатора на этом коммите она зелёная.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "3e735da29faf7866e4d028bf3b296cfa98c86031",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-cli-writer-lookup-guard"],
  "classes": {
    "ADV-cli-writer-lookup-guard": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"acknowledged by\" tests/fixtures/", "result": "no output — no committed transcript fixture carries an acknowledgement mark, so none can flip to self-acknowledged"},
      {"what": "grep -rn AGENTMARSHAL_ACTOR tests/test_leak_scan_acknowledgements.py tests/test_gate_marks_acknowledged_hits.py", "result": "every existing acknowledgement test records as 'an-operator', '<marker>' or 'op\\nera\\u202etor' — none is a declared writer of the test commits (committer worker@test.invalid / test@example.invalid), so existing expected output is unchanged"},
      {"what": "grep -rn _acknowledgement_mark --include=*.py .", "result": "only cli.py:1830 and gate.py:2390 call it; both pass the new keyword-only predicate, no caller left on the old signature"},
      {"what": "grep -n '^from agentmarshal' on records.py/capture.py/report.py", "result": "records.py:30 imports capture, report.py:16 imports records, capture.py imports only agentmarshal.project — confirms capture stands under report, so the predicate must be injected; report->actors adds no cycle"},
      {"what": "grep -n 'merge_base\\s*=\\|resolved_commit\\s*=' src/agentmarshal/journal/gate.py", "result": "each assigned exactly once in run_gate (1277, 1279) — the verdict block's lookup and the advisory's lazy lookup cover the identical range, so reuse is sound"},
      {"what": "grep -n '_project_root_for|_actor_git_identities' src/agentmarshal/journal/status_view.py", "result": "_project_root_for still used at lines 108 and 553, so dropping the _actor_git_identities import leaves no unused import"},
      {"what": "grep -n '^### Requirement|^#### Scenario' openspec/specs/leak-scan/spec.md", "result": "both MODIFIED requirements keep every scenario they had; the ADDED requirement lands at line 819 with all 8 scenarios"},
      {"what": "find openspec/changes/archive/2026-10-25-self-acknowledgement-mark -type f; ls openspec/changes/", "result": "proposal.md, design.md, tasks.md, specs/leak-scan/spec.md present under archive; openspec/changes/ holds only 'archive'"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py (declared_commit_writers, accepting_party_is_declared_writer, acknowledging_party_is_declared_writer, _self_accepted)",
      "src/agentmarshal/journal/capture.py (_acknowledgement_mark, _acknowledgement_identification, scan_diff_for_leaks)",
      "src/agentmarshal/journal/gate.py (run_gate: 1479 init, 1900-1940 verdict block, 2320-2410 advisory leak-scan, _range_writer_identities, _run_git_bytes)",
      "src/agentmarshal/cli.py (_run_leak_scan, 1690-1850)",
      "src/agentmarshal/journal/status_view.py (_is_self_accepted, _is_self_acknowledged, _is_declared_recorder)",
      "src/agentmarshal/journal/actors.py (_actor_git_identities, resolve_recorded_by, _actors_table)",
      "src/agentmarshal/journal/records.py (create_acknowledgement_record, write_record)",
      "docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md (decisions 2, 3, 5)",
      "openspec/specs/leak-scan/spec.md (requirements at 640, 713, 819)",
      "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/{proposal,design,tasks}.md and specs/leak-scan/spec.md",
      "tests/test_self_acknowledgement_mark.py (all 8 tests)",
      "tests/test_gate.py helpers (_gate_repo, _implement, _approve, _run, _WRITER, _commit_all)",
      "tests/test_leak_scan_acknowledgements.py helpers (_git, _repo, _add_file, _head, _open, _write_acknowledgement, _GITHUB_TOKEN)",
      "tests/test_gate_marks_acknowledged_hits.py (test_the_mark_is_the_one_the_standalone_command_prints)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the review snapshot has no .venv and no uv/network available, so the CI sequence could not be executed here; the coordinator reports it green on this commit"}
    ]
  },
  "evidence": {
    "ADV-cli-writer-lookup-guard": "src/agentmarshal/cli.py:1793-1802 — comment claims the lookup 'runs only where an acknowledgement could be qualified, as the gate's guard does', but the guard is `if acknowledgements:` alone; the gate's equivalent is `if leak_hits:` (src/agentmarshal/journal/gate.py:2358) enclosing `if acknowledgements and not writer_identities:` (gate.py:2382). `hits` is already computed at cli.py:1756, before the acknowledgement block, so a clean scan with acknowledgements in the journal still issues `git show -s` that the gate would skip."
  }
}
AGENTMARSHAL_VERDICT_END
