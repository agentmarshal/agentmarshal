Прочитал diff, обе поверхности, общую derivation и все тесты. Запустить проверки тут нельзя (snapshot без git и без venv), так что о падениях инструментов ничего не утверждаю.

## Acceptance criteria

**Критерий 1 — выполнен.** Общая derivation одна: `report.acknowledging_party_is_declared_writer` (`src/agentmarshal/journal/report.py:554`) раскладывает `recorded_by` через тот же `_actor_git_identities`, что использовал `status`, плюс само записанное имя, и держит каждую identity против единственного сравнения `accepting_party_is_declared_writer` (`report.py:536`) — второй копии нет, и diff удаляет локальную копию из `status_view` вместе с её импортом `_actor_git_identities`, оставив `_is_self_acknowledged` вызовом общей функции (`status_view.py:81-90`). Gate сравнивает по candidate range — ленивый `_range_writer_identities` по `merge_base..resolved_commit`, переиспользующий lookup verdict-блока (`gate.py:1479`, `gate.py:2382-2398`; verdict-блок пишет в ту же переменную на `gate.py:1926`); это демонстрируют `test_the_gate_marks_a_self_acknowledgement_over_the_candidate_range` и `test_a_writer_of_an_earlier_range_commit_marks_at_the_gate_alone`. `leak-scan` сравнивает по сканируемому коммиту через `declared_commit_writers(scan_root, resolved_commit)` (`cli.py:1800`); это демонстрируют `test_the_standalone_command_marks_a_self_acknowledgement`, `test_the_commits_committer_marks_a_self_acknowledgement`, `test_a_declared_actors_resolved_identity_marks_a_self_acknowledgement` и `test_the_writer_check_folds_case`. Оба условия названы в самом требовании (`openspec/specs/leak-scan/spec.md:804-809`). Цикла импортов нет: `records.py:30` импортирует `capture`, поэтому `capture` принимает проверку как predicate (`capture.py:409`) — утверждение в его docstring проверяемо и верно.

**Критерий 2 — выполнен.** Delta — `ADDED Requirements` на capability `leak-scan`, восемь сценариев, у каждого ровно один тест, чей docstring называет сценарий дословно (standalone / gate over range / committer / resolved identity / earlier range commit / another party / check git cannot answer / folds case) — все восемь в `tests/test_self_acknowledgement_mark.py`. Результат соответствует работе archive-команды: change лежит под `openspec/changes/archive/2026-10-25-self-acknowledgement-mark/`, а текст требования дословно дописан в `openspec/specs/leak-scan/spec.md:804-855`; саму команду я переигрывать не могу, так что это вывод из получившейся раскладки, а не из её запуска.

**Критерий 3 — выполнен.** Чужая acknowledgement печатается как раньше: `test_an_acknowledgement_by_another_party_prints_unmarked` пинит обе строки целиком, а `self_acknowledged` в `_acknowledgement_mark` — keyword-only с дефолтом `None`, так что вызов без predicate даёт сегодняшнюю метку. Все существующие ожидания метки (`tests/test_leak_scan_acknowledgements.py`, `tests/test_gate_marks_acknowledged_hits.py`) записаны на `an-operator`, который declared writer'ом не является, поэтому остаются `acknowledged by`. Транскрипт-фикстуры `tests/fixtures/gate/*` слова `acknowledged` не содержат вовсе — менять их нечему. Вывод `status` не меняется: рефактор сохраняет все три ноги tri-state (`identities` уже strip+casefold, `any(... in writers)` тождественно прежнему `not isdisjoint`), и они по-прежнему пинятся `tests/test_status_schema_7_lines.py:519`, `:589`, `:622`.

## Findings (все advisory)

**ADV-design-non-goal** — `openspec/changes/archive/2026-10-25-self-acknowledgement-mark/design.md:27` объявляет Non-Goal: «The merge boundary's line — it carries no acknowledgement marks». Но «merge boundary's line» в этой capability — это как раз advisory leak-scan строка gate'а (`openspec/specs/leak-scan/spec.md:55` «the merge boundary reports the same detail» и `:702` «the merge boundary's line carries no mark yet» — оба про `the gate's added-content scan`), и она метки несёт (требование `openspec/specs/leak-scan/spec.md:719`), и именно её это изменение правит, что тот же документ ставит себе Goal'ом на `design.md:15-19`. Non-Goal противоречит Goal'у того же документа и спецификации; поведение кода при этом верное.

**ADV-leak-scan-eager-writer-lookup** — `src/agentmarshal/cli.py:1800` вызывает `declared_commit_writers` (отдельный `git show`) всегда, когда placement разрешился, даже если `hits` пуст или acknowledgements нет — хотя `hits` к этому моменту уже посчитан (`cli.py:1744`). Gate ту же цену платит под условием (`gate.py:2382`: `if acknowledgements and not writer_identities`). Вывод и exit code это не меняет, но каждый чистый `leak-scan` в репозитории с журналом теперь тратит лишний git-процесс.

**ADV-gate-lookup-failure-untested** — `src/agentmarshal/journal/gate.py:2387` (`except GateError: writer_identities = None`) ни одним тестом не проходится. Единственный тест на неотвеченный lookup, `test_a_check_git_cannot_answer_marks_nothing`, подменяет `gate_module._range_writer_identities` на `lambda *args: ({"worker@test.invalid"}, None)` — настоящая функция такого не возвращает никогда (её тип `tuple[set[str], set[str]]`, а на отказе git она поднимает `GateError`, `gate.py:538-540`). То есть нога «a lookup failure leaving the mark unmarked», которую `tasks.md` 2.3 отмечает проверенной через pytest, демонстрируется невозможным возвращаемым значением, а не реальным режимом отказа; поведение при реальном `GateError` (и в lane'ах journal-only / operational, где verdict-блок lookup не делал вовсе) остаётся непокрытым. Сам сценарий спеки при этом демонстрируется — для команды через настоящий `None` от `declared_commit_writers`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "3d54e73601eacb9879828e5f8254ce69febc2202",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-design-non-goal",
    "ADV-leak-scan-eager-writer-lookup",
    "ADV-gate-lookup-failure-untested"
  ],
  "classes": {
    "ADV-design-non-goal": "claim-accuracy",
    "ADV-leak-scan-eager-writer-lookup": "style",
    "ADV-gate-lookup-failure-untested": "test-gap"
  },
  "verification": {
    "executed": [
      {"what": "grep -n writer_identities src/agentmarshal/journal/gate.py", "result": "declared at 1479, assigned by the verdict block at 1926, reused/looked up lazily at 2382-2388, passed to the predicate at 2396 — the reuse the comment claims is real"},
      {"what": "grep -n '^from|^import' src/agentmarshal/journal/records.py and capture.py", "result": "records.py:30 imports capture._LEAK_PATTERNS; capture imports no journal module at top level — capture cannot import report, so the caller-supplied predicate is required as documented"},
      {"what": "grep -n '^from|^import' src/agentmarshal/journal/actors.py", "result": "actors imports only agentmarshal.project — report.py's new import of _actor_git_identities adds no cycle"},
      {"what": "grep -rn 'acknowledged by' tests/ (excluding the new file)", "result": "every existing expectation names 'an-operator' or '[masked: private-marker]', never a declared writer — existing marks unchanged"},
      {"what": "grep -rln acknowledged tests/fixtures/", "result": "no match — the gate transcript fixtures carry no acknowledgement, so none can change"},
      {"what": "grep -n '_project_root_for' src/agentmarshal/journal/status_view.py", "result": "still used at 108 and 553, so the kept import is not dead after _actor_git_identities was dropped"},
      {"what": "grep -n 'merge boundary' openspec/specs/leak-scan/spec.md docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md src/", "result": "spec.md:55 and :702 and ADR-0021:8,:188 all name the gate's added-content scan the merge boundary — the basis of ADV-design-non-goal"},
      {"what": "grep -n 'def _range_writer_identities' -A40 src/agentmarshal/journal/gate.py", "result": "returns tuple[set[str], set[str]] or raises GateError — it never returns None, the basis of ADV-gate-lookup-failure-untested"},
      {"what": "grep -n 'def declared_commit_writers' -A40 src/agentmarshal/journal/report.py", "result": "returns None on a non-zero git exit, OSError or undecodable field — the None leg the new predicate treats as unchecked"},
      {"what": "grep -n 'def create_acknowledgement_record' -A40 and resolve_recorded_by in actors.py", "result": "recorded_by/recorded_by_source are derived at write_record time from AGENTMARSHAL_ACTOR (SOURCE_OVERRIDE), so the new tests' monkeypatched actor really lands in the record"},
      {"what": "grep -n '_WRITER' tests/test_gate.py and tests/test_leak_scan_acknowledgements.py", "result": "worker@test.invalid and test@example.invalid are the committing identities the new tests compare against — the self-acknowledged assertions are reachable"},
      {"what": "grep -n 'self-acknowledged|not checked' tests/test_status_schema_7_lines.py", "result": "all three status legs (marked at 519 and 622, not-checked at 283/589) stay pinned, demonstrating status's output is unchanged"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py (declared_commit_writers, accepting_party_is_declared_writer, acknowledging_party_is_declared_writer, _self_accepted)",
      "src/agentmarshal/journal/capture.py:405-460 (_acknowledgement_mark)",
      "src/agentmarshal/journal/gate.py:1460-1500, 1900-1945, 2330-2412",
      "src/agentmarshal/cli.py:1690-1850 (_run_leak_scan)",
      "src/agentmarshal/journal/status_view.py:60-100",
      "src/agentmarshal/journal/actors.py:88-140",
      "src/agentmarshal/journal/records.py:2027-2040, 2587-2626",
      "docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md:114-200 (decisions 3-5 and What this revises)",
      "openspec/specs/leak-scan/spec.md:25-70, 640-725, 801-856",
      "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/{proposal,design,tasks}.md and specs/leak-scan/spec.md",
      "tests/test_self_acknowledgement_mark.py (all eight tests)",
      "tests/test_gate.py helpers (_gate_repo, _implement, _approve, _run, _commit_all)",
      "tests/test_leak_scan_acknowledgements.py helpers (_repo, _add_file, _open, _write_acknowledgement)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the review snapshot has no virtualenv and no network, so no check could be executed; the coordinator reports the full sequence green on the reviewed commit and I make no claim against it"},
      {"what": "OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.15.0 archive self-acknowledgement-mark --yes", "why": "cannot re-run the archive command here; criterion 2's archive leg is assessed from the resulting file layout and the verbatim spec text only"},
      {"what": "git show / git log on the reviewed commit", "why": "the snapshot is not a git repository, so the diff supplied in the task was the only history available"}
    ]
  },
  "evidence": {
    "ADV-design-non-goal": "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/design.md:27 ('- The merge boundary's line — it carries no acknowledgement marks.') against openspec/specs/leak-scan/spec.md:55 ('Scenario: the merge boundary reports the same detail' / 'WHEN the gate's added-content scan finds a hit'), spec.md:702 ('Scenario: the merge boundary's line carries no mark yet' / 'WHEN the gate's added-content scan reports a hit no acknowledgement of the task names'), spec.md:719 ('Requirement: the gate marks an acknowledged hit on its leak-scan line') and the same design.md:15-19 Goal ('the gate over the candidate range')",
    "ADV-leak-scan-eager-writer-lookup": "src/agentmarshal/cli.py:1800 `ack_writers = declared_commit_writers(scan_root, resolved_commit)` runs inside the `else:` of the acknowledgement read with no guard on `hits` (computed at cli.py:1744) or on `acknowledgements`; contrast src/agentmarshal/journal/gate.py:2382 `if acknowledgements and not writer_identities:`",
    "ADV-gate-lookup-failure-untested": "src/agentmarshal/journal/gate.py:2387 `except GateError: writer_identities = None` has no exercising test; tests/test_self_acknowledgement_mark.py monkeypatches `gate_module._range_writer_identities` with `lambda *args: ({\"worker@test.invalid\"}, None)`, a shape src/agentmarshal/journal/gate.py:538-540 (`-> tuple[set[str], set[str]]`, raising GateError on git failure per gate.py:577-578) never produces"
  }
}
AGENTMARSHAL_VERDICT_END
