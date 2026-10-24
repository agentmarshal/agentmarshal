Я прочитал diff против файлов снапшота, прошёл по `gate.py`, `report.py`, `status_view.py`, `placement.py`, `records.py`, `cli.py`, обе версии спеки `operator-acceptance` и затронутые тесты. Запустить `pytest`/`ruff`/`mypy` здесь не удалось (`uv` в снапшоте нет, sandbox не даёт выполнить python) — все утверждения о прохождении проверок беру из записки координатора и помечаю как непроверенные.

**Findings**

`report-comment-claims-one-derivation` — комментарий в `src/agentmarshal/journal/report.py:480-481` («One lookup and one comparison — gate, report and status mark the same identities the same way») не соответствует коду: gate сравнивает `accepted_by` только с **email'ами** всех коммитов candidate range (`_range_emails`, `git log --format=%ae%n%ce`, `gate.py:501-505`, вызов на `gate.py:1791-1798`), а report и status — с **именами и email'ами** автора и committer'а одного accepted commit (`_declared_commit_writers`, `git show -s --format=%an%n%ae%n%cn%n%ce`, `status_view.py:48-68`). Собственный тест диффа `tests/test_self_acceptance_on_every_surface.py:263` параметризует party значением `"Committer"` — именем, которого в множестве gate'а не может быть ни при каком коммите, — так что тесты в этом же диффе опровергают комментарий.

`unchecked-mark-breaks-byte-identity-carveout` — исправленная оговорка в `openspec/specs/operator-acceptance/spec.md:129-133` обещает byte-identity вывода «for an acceptance that is not a self-acceptance», но ADDED requirement на `:321-323` и сценарий `:344-350` требуют печатать ` self-acceptance-unchecked`, когда writers accepted commit'а прочитать нельзя, — а такая acceptance как раз «is not a self-acceptance». Случай достижим и уже воспроизводится существующим тестом: в `tests/test_report.py:386-437` CR-001 держит acceptance от `operator` на `"a"*40`, которого в репозитории нет, и его строка теперь `CR-001\topen\treviews=1\ttokens=0\tdecision=accepted-over-findings\tself-acceptance-unchecked`; тест проходит лишь потому, что проверяет подстрокой (`in output`). То есть criterion 4 («a journal with no self-acceptance and no earlier acceptance prints exactly what it prints today, which the existing … report … tests demonstrate unchanged») на этом журнале не выполняется, а просто не детектируется — реально это меняет вывод `report` для любого чтения журнала вне репозитория с accepted commit'ами (shallow checkout, архивный журнал, sidecar с неподмонтированным host'ом). Нужно либо расширить carve-out в MODIFIED requirement на unchecked-случай, либо ограничить новый mark, либо назвать это departure от criterion 4.

`gate-and-report-compare-different-identities` (advisory) — criterion 1 просит «the same mark» от обеих поверхностей по «the identities the gate's independence check already reads», но множества расходятся в обе стороны: party, назвавшаяся именем (`Committer`), помечается в `report` (`tests/test_self_acceptance_on_every_surface.py:263`) и не помечается в gate; party, писавшая только более ранний коммит range'а, помечается в gate (`merge_base..commit`) и не помечается в `report` (`git show <accepted_commit>`). Расходятся и формулировки qualification: gate — `accepting party is a declared writer of the candidate`, status — `accepting party is a declared author or committer`. Компромисс осознанный (у `report` нет merge base, а status менять — non-goal, см. design.md), и спека его фиксирует («the comparison the surface already makes»), но ADR-0007 decision 4 в первом направлении остаётся не закрытым.

**По критериям приёмки**

1. **Mark на gate и report** — выполнен: `gate.py:1791-1811` поднимает writer-emails выше verdict-блока (условие `latest is not None` то же, что у independence-check на `gate.py:1902-1906`, `merge_base`/`resolved_commit` между ними не переназначаются) и добавляет qualification; `report.py:458-484` + `866-874` + tri-state `TaskReport.self_accepted` (`report.py:145`) несут метку на строке задачи. Демонстрируют: `tests/test_self_acceptance_on_every_surface.py:160` (email и регистр), `:181` (committer-email), `:238` и `:264` (report, email и имя), `:206` (сторонняя party — обе поверхности без метки). Оговорка — advisory-finding выше.
2. **Decision по binding'у completed-записи** — выполнен: `report.py:500-556` читает latest review и findings-acceptance ровно по `completed_commit`/`completed_finding`, иначе сохраняет сегодняшнее правило. Демонстрируют `:330` (approved после acceptance на раннем коммите), `:364` (commit over findings), `:394` (findings lane, метка не выводится — у записи нет `accepted_commit`, `report.py:474-475`), `:453` (acceptance на другом коммите → поля `decision` нет), `:474` (нет completed-записи). Проверил, что нормальный путь не ломается: `complete.py:69-75` пишет `completed_commit = report.resolved_commit`, то есть тот же коммит, к которому привязаны review и acceptance.
3. **Delta и архив** — выполнен: MODIFIED requirement в `openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/specs/operator-acceptance/spec.md` несёт heading и все шесть сценариев, совпадающие с `openspec/specs/operator-acceptance/spec.md:119-168` (сравнил чтением обоих файлов, не байтовым diff'ом), два ADDED requirement'а с 4+5 сценариями легли на `:316-387`; архив лежит по шаблону соседних change'ей (`design.md`, `proposal.md`, `tasks.md`, `specs/<capability>/spec.md`), в `openspec/changes/` ничего не осталось. Каждый из девяти новых сценариев назван в docstring теста (`:160`/`:181`, `:238`/`:264`, `:206`, `:296`, `:330`, `:364`, `:394`, `:453`, `:474`); шесть MODIFIED-сценариев сохраняют тесты в `tests/test_pause_and_operational_acceptance.py` (в т.ч. `:653` и `:710`). Других requirement'ов с byte-identity-оговоркой, которые задевает mark, в `operator-acceptance` нет; «A default run is unchanged» в `gate-lanes:47` по принятой в репозитории конвенции feature-относительная (ср. `leak-scan:696`), так что её не трогать — правильно.
4. **Неизменный вывод, escaping, CI** — выполнен частично: escaping в порядке (новые токены — литералы, `say()` escape'ит строку целиком, `gate.py:1156-1161`; `report` новых значений не печатает), transcript-фикстуры в диффе не менялись, `tests/test_display.py:252` сохраняет пин экранирования. Но byte-identity на unchecked-случае не держится — см. blocking-finding выше. Отдельно отмечу (не finding): пин `tests/test_pause_and_operational_acceptance.py:710` сам изменён (party `test@example.invalid` → `op`), поэтому покрытие status-метки оттуда ушло; оно остаётся в `tests/test_acceptance.py:185` и `:205`. Прохождение `pytest`/`ruff`/`ruff format`/`mypy`/`validate` я не проверял.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4bf45b5982cad1bfda0fea77acc97fc254df5cf6",
  "verdict": "changes_required",
  "findings": [
    "unchecked-mark-breaks-byte-identity-carveout",
    "report-comment-claims-one-derivation"
  ],
  "advisory_findings": [
    "gate-and-report-compare-different-identities"
  ],
  "classes": {
    "unchecked-mark-breaks-byte-identity-carveout": "contract-mismatch",
    "report-comment-claims-one-derivation": "claim-accuracy",
    "gate-and-report-compare-different-identities": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"_is_self_accepted|_declared_commit_writers\" src/ tests/", "result": "one derivation in status_view.py:48-84; report.py:482 imports it at call time; no copy elsewhere"},
      {"what": "grep -n \"_range_emails|_range_commits\" -A 5 src/agentmarshal/journal/gate.py", "result": "gate.py:501-505 formats only %ae%n%ce over merge_base..commit — emails of the whole range, no names"},
      {"what": "grep -n \"merge_base = |resolved_commit = \" src/agentmarshal/journal/gate.py", "result": "assigned once at 1184-1188, so the hoisted writer_emails at 1791 reads the same values the check at 1902 read"},
      {"what": "grep -rn \"create_completed_record\" src/", "result": "complete.py binds report.resolved_commit; migrate.py:409-411 binds Merged-Commit or Reviewed-Commit and writes no acceptance records, so the new binding rule loses no migrated decision"},
      {"what": "grep -rn \"_task_report\" src/ tests/", "result": "only build_report and tests/test_display.py:254 — the new parameter has no other caller"},
      {"what": "grep -rn \"byte for byte|byte-identical\" openspec/specs/", "result": "operator-acceptance:129-133 is the only clause the mark touches; gate-lanes:47 and leak-scan:696 are feature-relative by convention"},
      {"what": "ls openspec/changes/ and openspec/changes/archive/", "result": "no unarchived change dir; 2026-10-25-self-acceptance-on-every-surface present with the sibling layout"}
    ],
    "read": [
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/gate.py (141-230, 1150-1210, 1640-1960)",
      "src/agentmarshal/journal/status_view.py (1-210, 772-841)",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/records.py (2027-2041, 2485-2544, 2725-2756)",
      "src/agentmarshal/journal/complete.py (40-100)",
      "src/agentmarshal/journal/acceptance.py (grep)",
      "src/agentmarshal/journal/attestation.py (50-155)",
      "src/agentmarshal/cli.py (1375-1400, 1490-1550, 749-793)",
      "src/agentmarshal/migrate.py (395-435)",
      "openspec/specs/operator-acceptance/spec.md",
      "openspec/changes/archive/2026-10-25-self-acceptance-on-every-surface/{design.md,proposal.md,tasks.md,specs/operator-acceptance/spec.md}",
      "docs/adr/ADR-0007-operator-acceptance.md",
      "docs/threat-model.md (95-110)",
      "docs/quickstart.md (465-500)",
      "docs/sidecar.md:335",
      "tests/test_self_acceptance_on_every_surface.py",
      "tests/test_pause_and_operational_acceptance.py (534-745)",
      "tests/test_report.py (30-45, 370-437)",
      "tests/test_acceptance.py (175-230)",
      "tests/test_gate.py (42-300)",
      "tests/test_journal.py (44-70)",
      "tests/test_display.py (240-260)",
      "pyproject.toml ([tool.ruff])",
      "AGENTS.md",
      ".agentmarshal/journal/tasks/CR-237/contract.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "uv is not installed in this snapshot and the sandbox refused to run python/pytest; all claims about these checks rest on the coordinator's statement and are unverified here"},
      {"what": "byte-level diff of the delta's MODIFIED block against openspec/specs/operator-acceptance/spec.md", "why": "no python or process-substitution available; the two blocks were read and compared by eye instead"}
    ]
  },
  "evidence": {
    "report-comment-claims-one-derivation": "src/agentmarshal/journal/report.py:478-484 claims 'gate, report and status mark the same identities the same way'; gate's set is emails only (src/agentmarshal/journal/gate.py:501-505 'git log --format=%ae%n%ce', used at gate.py:1791-1806) while report/status use names and emails of one commit (src/agentmarshal/journal/status_view.py:56-68 'git show -s --format=%an%n%ae%n%cn%n%ce'); tests/test_self_acceptance_on_every_surface.py:263 parametrizes party=\"Committer\" (a name) and expects report to mark it",
    "unchecked-mark-breaks-byte-identity-carveout": "openspec/specs/operator-acceptance/spec.md:129-133 ('SHALL be unchanged byte for byte for an acceptance that is not a self-acceptance') versus :321-323 and :344-350 (' self-acceptance-unchecked' where the writers cannot be read); reachable in tests/test_report.py:424-437 — acceptance by 'operator' on commit \"a\"*40 in an embedded repo (tests/test_report.py:30-39) makes report.py:552-556 yield self_accepted=None and report.py:871-874 append '\\tself-acceptance-unchecked', which the assertion at tests/test_report.py:436-437 only tolerates because it tests a substring; tests/test_self_acceptance_on_every_surface.py:296-328 pins that same shape as intended",
    "gate-and-report-compare-different-identities": "gate: src/agentmarshal/journal/gate.py:1791-1806 over _range_emails(merge_base..resolved_commit) (gate.py:501-505); report: src/agentmarshal/journal/report.py:474-484 delegating to status_view._is_self_accepted on record['accepted_commit'] alone (status_view.py:71-84); qualification texts differ at gate.py:1803-1804 versus status_view.py:807-810; the name-match direction is demonstrated by tests/test_self_acceptance_on_every_surface.py:263-294"
  }
}
AGENTMARSHAL_VERDICT_END
