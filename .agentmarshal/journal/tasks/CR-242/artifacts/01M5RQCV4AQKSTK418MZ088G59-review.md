Разобрался. Ниже — прозаическая часть, потом verdict-блок.

## Находки (все advisory, ничего блокирующего)

**ADV-design-scans-one-commit** — обоснование в архивированном design-доке неточно: `openspec/changes/archive/2026-10-25-self-acknowledgement-mark/design.md:39-41` говорит «`leak-scan` scans one commit, so it compares over that commit's declared writers», но команда сканирует добавления диапазона `merge-base..commit` — базу она получает явным `--base` (`src/agentmarshal/cli.py:1721`, диапазон читается в `1748`). То есть сравнение только по сканируемому коммиту — это выбор контракта (критерий 1 его прямо предписывает), а не следствие того, что команда не знает базы; формулировка «сканирует один коммит» это обоснование подменяет. Расхождение двух поверхностей в спеке описано честно (`openspec/specs/leak-scan/spec.md:655-660`, `727-733`), поэтому это только про точность утверждения в доке.

**ADV-report-docstring-callers** — два docstring в `report.py` перечисляют вызывающих и после диффа устарели: `src/agentmarshal/journal/report.py:495` утверждает «The one writer lookup `report` and `status` share: `status_view` calls this function for the accepted commit», хотя третьим вызывающим стал `cli._run_leak_scan` (`src/agentmarshal/cli.py:1801`); `src/agentmarshal/journal/report.py:538` называет `accepting_party_is_declared_writer` «The one self-acceptance comparison — gate, report and status», хотя теперь это ещё и поэлементное сравнение внутри `acknowledging_party_is_declared_writer` (`report.py:586-588`), то есть основа acknowledgement-ветки. Файл в scope, правка чисто текстовая.

**ADV-mark-wording-duplicated** — слово самой марки набрано дважды: `src/agentmarshal/journal/capture.py:449` («self-acknowledged») и `src/agentmarshal/journal/status_view.py:262` (« self-acknowledged»). Для аналогичной acceptance-марки проект завёл одну константу именно против такого расхождения — `SELF_ACCEPTED_MARK` в `report.py:41-49` с комментарием «so the wording is one constant rather than a phrase each surface retypes». Критерий 1 требует «says self-acknowledged in the terms status already uses», и сейчас эта общность держится только на двух совпадающих литералах в модулях, которые спека объявляет неспособными разойтись.

## Критерии приёмки

**Критерий 1 — выполнен.** Вывод один и общий: `report.acknowledging_party_is_declared_writer` (`report.py:554-591`) резолвит `recorded_by` через тот же `_actor_git_identities`, что и status, плюс само имя, и прогоняет каждую identity через `accepting_party_is_declared_writer` — второй копии нет, а `status_view._is_self_acknowledged` теперь просто делегирует туда (`status_view.py:86-90`), импорт `_actor_git_identities` из него удалён. Gate сравнивает по диапазону кандидата, переиспользуя лукап verdict-блока и делая ленивый, где тот не сработал (`gate.py:1479`, `2382-2398`); `leak-scan` — по сканируемому коммиту через `declared_commit_writers` (`cli.py:1801`, `1830-1842`). Демонстрируют: `test_the_standalone_command_marks_a_self_acknowledgement`, `test_the_gate_marks_a_self_acknowledgement_over_the_candidate_range`, `test_the_commits_committer_marks_a_self_acknowledgement` (комиттер, не автор), `test_a_declared_actors_resolved_identity_marks_a_self_acknowledgement` (actors-таблица), `test_the_writer_check_folds_case`, `test_a_writer_of_an_earlier_range_commit_marks_at_the_gate_alone`. Оба условия требование называет прямо: «a declared author or committer … of any commit in the candidate range for the gate» (`openspec/specs/leak-scan/spec.md:819-824`).

**Критерий 2 — выполнен.** Дельта несёт ADDED-требование и два MODIFIED с полным текущим текстом; я сверил дельту (`openspec/changes/archive/2026-10-25-self-acknowledgement-mark/specs/leak-scan/spec.md:58-237`) с архивированной спекой (`openspec/specs/leak-scan/spec.md:640-871`) построчно — заголовки и все сценарии совпадают байт в байт, ни один сценарий не потерян. Все восемь сценариев ADDED-требования закрыты по одному тесту, docstring каждого называет сценарий дословно (`tests/test_self_acknowledgement_mark.py`), а изменённый сценарий «the mark is the one the standalone command prints» по-прежнему держится тестом, который его называет (`tests/test_gate_marks_acknowledged_hits.py:141`), плюс новым тестом про ранний коммит диапазона. Архив применён: дельта лежит под `openspec/changes/archive/2026-10-25-self-acknowledgement-mark/`, в `openspec/changes/` остался только `archive`, текст приехал в `openspec/specs/leak-scan/spec.md`; сам факт запуска именно `openspec archive` 1.15.0 проверить нечем (npx в песочнице нет) — результат в дереве согласован.

**Критерий 3 — выполнен в проверяемой части.** Чужая сторона печатается как сегодня: `test_an_acknowledgement_by_another_party_prints_unmarked` пинит обе поверхности целиком («acknowledged by an-operator»), а `test_a_check_git_cannot_answer_marks_nothing` — неотвечаемый лукап на обеих ветках (`GateError` в gate, `None` в команде), то есть `None` никогда не превращается в марку; это же гарантирует `verb` в `capture.py:448-452`, который требует ровно `is True`. Старые assertion'ы не ломаются по построению: все существующие тесты leak-scan и gate пишут актора `an-operator` (`grep -rn "acknowledged by" tests/`), который не совпадает ни с одним объявленным писателем. Вывод status не меняется — делегация эквивалентна прежнему `not identities.isdisjoint(writers)`, и это пинят существующие `tests/test_status_schema_7_lines.py:519`, `:589`, `:622`. Ни один файл фикстур в диффе не тронут. Прогон полного CI-сиквенса мной не выполнен — в снапшоте нет uv/venv, запуск python/pytest песочница отклонила; беру результат из записки координатора по 3e735da.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "3e735da29faf7866e4d028bf3b296cfa98c86031",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-design-scans-one-commit",
    "ADV-report-docstring-callers",
    "ADV-mark-wording-duplicated"
  ],
  "classes": {
    "ADV-design-scans-one-commit": "claim-accuracy",
    "ADV-report-docstring-callers": "claim-accuracy",
    "ADV-mark-wording-duplicated": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn '_acknowledgement_mark' src/ tests/", "result": "two printing callers only — cli.py:1830 and gate.py:2390, both now pass the self_acknowledged predicate; capture.py:404 is the single builder; no third surface prints the mark (attestation.py only registers the record type)"},
      {"what": "grep -rn 'self-acknowledged|acknowledged by' src/", "result": "capture.py:449 and status_view.py:262 each hold the wording as a literal; no shared constant, unlike SELF_ACCEPTED_MARK at report.py:47"},
      {"what": "grep -rn 'acknowledged by' tests/", "result": "every pre-existing leak-scan/gate assertion uses actor 'an-operator', which matches no declared writer, so today's unmarked text still holds"},
      {"what": "grep -n 'writer_identities' src/agentmarshal/journal/gate.py", "result": "1479 init to None, 1926 verdict-block assignment, 2382-2388 lazy lookup guarded by 'acknowledgements and not writer_identities' — one function scope, advisory block strictly after the verdict block, so the range is read once"},
      {"what": "grep -n '_project_root_for|_actor_git_identities' src/agentmarshal/journal/status_view.py src/agentmarshal/journal/report.py src/agentmarshal/journal/actors.py", "result": "status_view no longer imports _actor_git_identities but still uses _project_root_for at 108/553 (no dead import); report.py imports actors, which imports only agentmarshal.project — no cycle with records/capture"},
      {"what": "line-by-line comparison of the delta's MODIFIED/ADDED requirements against openspec/specs/leak-scan/spec.md", "result": "headings and all scenarios identical; spec holds exactly one copy of each requirement heading"}
    ],
    "read": [
      "docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md",
      "openspec/specs/leak-scan/spec.md:630-871",
      "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/specs/leak-scan/spec.md",
      "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/design.md",
      "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/proposal.md",
      "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/tasks.md",
      "src/agentmarshal/cli.py:1690-1850",
      "src/agentmarshal/journal/capture.py:360-460",
      "src/agentmarshal/journal/gate.py:520-600, 1470-1500, 1880-1960, 2320-2430",
      "src/agentmarshal/journal/report.py:1-40, 480-620",
      "src/agentmarshal/journal/status_view.py:55-130, 240-270",
      "src/agentmarshal/journal/actors.py:60-140",
      "src/agentmarshal/journal/records.py:2027-2130, 2587-2626",
      "tests/test_self_acknowledgement_mark.py",
      "tests/test_gate.py (helpers _gate_repo/_implement/_approve/_run)",
      "tests/test_leak_scan_acknowledgements.py (helpers _repo/_git/_add_file/_write_acknowledgement)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the snapshot carries no uv or virtualenv and the sandbox denied running python/pytest; the CI result is taken from the coordinator's note on 3e735da"},
      {"what": "OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.15.0 validate / archive", "why": "no node/npx available in the sandbox; the archive's effect was checked in the tree instead"}
    ]
  },
  "evidence": {
    "ADV-design-scans-one-commit": "openspec/changes/archive/2026-10-25-self-acknowledgement-mark/design.md:39-41 ('`leak-scan` scans one commit, so it compares over that commit's declared writers') against src/agentmarshal/cli.py:1721 (merge-base resolved from the explicit --base) and src/agentmarshal/cli.py:1748 (leak_scan_diff(scan_root, merge_base, args.commit) — the scan is over the range's additions)",
    "ADV-report-docstring-callers": "src/agentmarshal/journal/report.py:495 ('The one writer lookup `report` and `status` share: `status_view` calls this function…') vs the new third caller src/agentmarshal/cli.py:1801 (declared_commit_writers(scan_root, resolved_commit)); src/agentmarshal/journal/report.py:538 ('The one self-acceptance comparison — gate, report and status') vs its new use inside acknowledging_party_is_declared_writer at report.py:586-588",
    "ADV-mark-wording-duplicated": "src/agentmarshal/journal/capture.py:449 ('self-acknowledged') and src/agentmarshal/journal/status_view.py:262 (' self-acknowledged'), against the stated precedent at src/agentmarshal/journal/report.py:41-49 — SELF_ACCEPTED_MARK 'lives here … so the wording is one constant rather than a phrase each surface retypes'"
  }
}
AGENTMARSHAL_VERDICT_END
