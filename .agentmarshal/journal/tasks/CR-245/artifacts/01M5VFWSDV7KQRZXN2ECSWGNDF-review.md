Разобрался с контрактом, аудит-файлом, журналом и кодом. Ниже — проза по каждому finding и по каждому acceptance criterion.

## Findings

**`audit-comment-gate-journal-paths-incomplete`** (blocking, claim-accuracy) — `release/audit-0.6.0.toml:6-8`. Комментарий говорит: «gate-journal ran at 15af26e before the freeze by operator decision (its paths changed afterwards only by the fixes CR-235/236/237)». Эта скобка — единственное место, которым файл раскрывает непроверенную поверхность, возникшую из-за аудита области по более старому commit'у, и она неполна. После CR-237 (`completed` в `2026-10-24T23:31:56Z`) пути gate-journal менялись ещё дважды: CR-240, scope `src/agentmarshal/journal/gate.py` + `tests/` (`completed` в `2026-10-25T00:42:55Z`; его правка стоит в `gate.py:89,392-413,1263,2162`), и CR-242, scope `capture.py`, `cli.py`, `gate.py`, `status_view.py`, `report.py` (`completed` в `2026-10-25T05:18:06Z`; `gate.py:2381-2394`). Обе задачи — фиксы *других* областей (whole-project и commands), так что перечисление «только CR-235/236/237» ложно. Альтернативное чтение («между 15af26e и freeze») исключено: фиксы extensions CR-238/CR-239 завершились (`01M5R37P`, `01M5R3D4`) раньше CR-237 (`01M5R43D`), значит freeze предшествует CR-235/236/237, и «afterwards» может значить только «после 15af26e».

**`audit-model-key-covers-fable-audited-area`** (advisory, claim-accuracy, unconfirmed) — `release/audit-0.6.0.toml:3` против `:10-12`. Единственный ключ, который читает gate (`check_release_audit.py` `ALLOWED_MODELS = ("gpt-6-astra",)`), объявляет `model = "gpt-6-astra"`, тогда как собственный комментарий файла говорит, что docs-claims part 2 — источник блокирующих AUD-docs-claims-2-1 и -2-2 — была проаудирована `claude-fable-5-1`, модель вне allowlist'а из CONTRIBUTING.md:150-151. Контракт прямо предписывает `model = "gpt-6-astra"` и предписывает раскрыть Fable в комментарии, так что для implementer'а это не дефект — это процессное отступление для координатора: запись утверждает allowlisted-происхождение для области, у которой его не было. Сами прогоны я проверить не могу, поэтому помечаю unconfirmed.

**`commands-4-5-disposition-uncorroborated`** (advisory, claim-accuracy, unconfirmed) — `release/audit-0.6.0.toml:84-94`. `AUD-commands-4` и `AUD-commands-5` записаны как fixed задачей CR-237, но ни контракт CR-237, ни его Context, ни тесты (`tests/test_self_acceptance_on_every_surface.py:5`), ни код (`report.py:641`) не называют ни одного finding'а области commands — только `AUD-gate-journal-4` и `-5`. Для сравнения, `AUD-commands-3 → CR-242` подтверждается `tests/test_self_acknowledgement_mark.py:3`. Это может быть дубликат, найденный областью commands независимо, и так его мог рассадить координатор — таблицу диспозиций из frame'а я не вижу, поэтому unconfirmed; след в журнале её не подтверждает.

**`readme-capture-line-not-reflowed`** (advisory, style) — `README.md:54`. Строка «reviewer's raw output at any level. Still roadmap: the `economics` and `sessions`» идёт до 83-й колонки, тогда как весь остальной bullet (`:43-58`) обёрнут по ≤78. Артефакт неперевёрстанной правки, содержательно ничего не ломает.

## Acceptance criteria

**AC1 (формат и полнота `release/audit-0.6.0.toml`)** — выполнен с оговоркой finding'а выше. Шапка совпадает с образцом CONTRIBUTING.md:169-184: `version = "0.6.0"`, `audited_commit = "dff244b2df8e8003dad6faa4f7aa2ddd2d25422a"` (ровно 40 hex, префикс совпадает с `dff244b` из Context контракта), `model = "gpt-6-astra"`, `audited_at = 2026-10-26T06:23:00+10:00` — aware offset date-time, который `_is_timestamp` принимает. 22 `[[finding]]`, у каждого `id` + `disposition`; у 21 `fixed` есть `task = "CR-<n>"` под `_TASK_ID`, у единственного `deferred` (`AUD-gate-journal-5-residue`) — непустой `reason`, согласованный с AC1 контракта CR-237 («that residue waits for a record field carrying the base»). Набор id непрерывен по областям и совпадает с тем, что контракты фиксов объявляют блокирующим: AUD-extensions-4/-5 помечены advisory в CR-239 Non-Goals, AUD-commands-6 — advisory в CR-241 Context, AUD-docs-claims-2-3…-8 — advisory в CR-244 Context, поэтому их отсутствие в файле корректно. Комментарий называет требуемое: области и commit'ы, две части docs-claims, и `AUD-whole-project-1` как finding сравнительного аудита Claude Fable. `audited_at` (= `2026-10-25T20:23:00Z`) непротиворечив журналу: CR-244, фикс последней области, открыт в `2026-10-26T02:16:51Z`, то есть после. Теста здесь нет и быть не может — критерий проверяется чтением; механизм, который файл обслуживает, демонстрируют `tests/test_release_audit_check.py`.

**AC2 (`check_release_audit.py v0.6.0` печатает `release audit: passed`)** — проверить не смог: snapshot не git-репозиторий (`Is a git repository: false`), тега `v0.6.0` нет, запуск `python3` в этой песочнице отклонён. Это отчётная обязанность implementer'а. Разбор кода говорит, что проход ожидаем: все 11 задач из `fixed` имеют последним lifecycle-record'ом `completed` (`CR-234` … `CR-244`, по одному `-completed.json` на задачу, без последующих `reopened`/`abandoned`), контракты всех 11 читаются из дерева, а пути самого кандидата покрыты `ALWAYS_ALLOWED` плюс scope'ами фиксов: `release/` и `CHANGELOG.md` — из `ALWAYS_ALLOWED`, `README.md` — из scope CR-234/CR-243, `docs/harness-setup.md`, `docs/proposals/012-...md` и `docs/templates/claude-code-settings.local.json` — из `docs/` в scope CR-244 (правило `_covered` с trailing slash). Демонстрируют механизм `tests/test_release_audit_check.py:740` (`test_passes_with_fixed_finding_covering_change`) и `:765` (`test_main_reports_pass_and_refusals`).

**AC3 (дата релиза, абзац аудит-фиксов, закрывающая строка)** — выполнен. `CHANGELOG.md:11` теперь `## 0.6.0 — 2026-10-26` вместо `unreleased`. Заголовок `:227` называет CR-234…CR-244, и каждый фикс описан из кода, что я сверил построчно: CR-235 — `gate.py` проекция чужих задач; CR-236 — timestamp/artifact refusal и `write_record`, причём сохранена честная оговорка «a failure while writing or closing the created file is not rolled back»; CR-240 — nested record path (`gate.py:89,392-413`); CR-237 — `self-accepted` (`report.py:48,996-1003`, `status_view.py:151-157`) с правильной оговоркой про accepted commit и residue; CR-242 — `self-acknowledged` (`capture.py:449-450`, `gate.py:2394`, `cli.py:1834`); CR-239 — base-tree manifest и NaN; CR-238 — формулировка про personal extension; CR-241 — symlink/staged-bytes/escaping (`outbox.py:164-200`, `_pinned_blob:832-851`, `_run_status:1228+`, `project.py:321-346`); CR-243/CR-244 — документация, включая «thirteen record types», что подтверждается 13 ключами в `attestation.py:62+`. Включение CR-234 поверх названного в контракте диапазона «CR-235 to CR-244» я не считаю отступлением: аудит-файл записывает `AUD-gate-journal-7 → CR-234`, и AC5 контракта CR-234 действительно про release-audit документационные findings, так что без него заголовок противоречил бы записи; последнее предложение абзаца (`:299-303`) описывает именно эту правку. Закрывающая строка `:327` («CR-205, CR-226, CR-230») осталась без изменений и это верно: все задачи, завершившиеся с момента последней ревизии этой строки (CR-237…CR-244), названы в заголовке `:227`, а CR-245 несёт пока только `opened` — то же правило, которым обходились предыдущие ревью CR-234. UPGRADING.md не менялся, и это правильно: правку, которой требовал фикс (personal-extensions bullet), внёс сам CR-238 по своему AC2. Тестов нет — критерий документационный.

**AC4 (README про `off`; 012 про superseded)** — выполнен. `README.md:52-56` больше не говорит «`off` keeps nothing», а разделяет: уровень управляет prose записанного verdict'а, отказанный verdict сохраняет сырой вывод на любом уровне. Сверено с кодом: `prose_capture_level` читается только на пути успешного парса (`review.py:1595,1619-1622`), а `_preserve_output` (`:599-616`) вызывается безусловно из `_reject` (`:813-824`) и даже на dry-run-пути с `preserve_output=False` (`:1279-1288`) — то есть «at any level» точно. `docs/proposals/012-...md:36-37` помечает старую строку «Not yet done» как superseded секцией Where с датой, не переписывая историю; Where (`:41-46`) действительно говорит, что scaffold пришёл в 0.2.0. Тестов нет — документационный критерий.

**AC5 (гранулярность subcommand'ов в harness-setup.md и в шаблоне)** — выполнен. `docs/harness-setup.md:83-102` разносит группы на subcommand'ы: писатели — `outbox new`/`outbox send`, `extension trust`/`untrust`/`disable`/`enable`, `extension switch off`; читатели — `outbox check`, `outbox status`, `extension list`, и явно сказано «The classification is by subcommand, not by group». Проверено по коду: `_run_check` → `_check` зовёт только `git hash-object --stdin` без `-w` (`outbox.py:530-534,832-851`) — записи нет; `_run_status` (`:1228+`) только читает и печатает; `_run_list` (`extension_trust.py:700-743`) читает grants и перехэшивает каталог — ровно то, что заявлено. Шаблон добавляет `Bash(agentmarshal gate)` рядом с `gate *`, как у `status` и `report`, и его `_comment` перечисляет операторские команды по subcommand'ам; набор `extension`-subcommand'ов в комментарии полон относительно `register` (`extension_trust.py:122-154`), а `extension list` не принимает аргументов, поэтому запись без `*` корректна. Мелочь без finding'а: у `outbox status` аргумент `--index` объявлен `required=True` (`outbox.py:137-143`), так что добавленная запись `Bash(agentmarshal outbox status)` никогда не совпадёт с работающей командой — мёртвая, но безвредная строка. Тестов нет — документационный критерий.

**AC6 (никаких других изменений; suite и полный CI)** — по файлам выполнен: diff трогает только `release/audit-0.6.0.toml`, `CHANGELOG.md`, `README.md`, `docs/harness-setup.md`, `docs/proposals/012-upstream-feedback-channel.md`, `docs/templates/claude-code-settings.local.json` — все внутри scope, кода не трогает. CI сам не прогонял (read-only review, песочница отклонила `python3`/`uv`); опираюсь на заявление координатора о прохождении на `b4ee38fa`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b4ee38fa3e071e4b06118e562dab9dbec2e072ba",
  "verdict": "changes_required",
  "findings": ["audit-comment-gate-journal-paths-incomplete"],
  "advisory_findings": ["audit-model-key-covers-fable-audited-area", "commands-4-5-disposition-uncorroborated", "readme-capture-line-not-reflowed"],
  "classes": {
    "audit-comment-gate-journal-paths-incomplete": "claim-accuracy",
    "audit-model-key-covers-fable-audited-area": "claim-accuracy",
    "commands-4-5-disposition-uncorroborated": "claim-accuracy",
    "readme-capture-line-not-reflowed": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -l '\"record_type\": *\"completed\"' over .agentmarshal/journal/tasks/CR-23*/records/*.json and CR-24*/records/*.json", "result": "one completed record for each of CR-234..CR-244; no reopened/abandoned record in any of those directories, so every 'fixed' task's last lifecycle record is 'completed'"},
      {"what": "ls of the records directories of CR-234, CR-235, CR-240, CR-244", "result": "CR-240 and CR-244 carry a session record after completed; session is not in _LIFECYCLE_RECORD_TYPES, so the projection still ends at completed"},
      {"what": "grep -rno 'AUD-[A-Za-z0-9-]*' over the contracts of CR-23*/CR-24*", "result": "AUD-extensions-4/-5, AUD-commands-6, AUD-docs-claims-2-3/-7, AUD-whole-project-3 appear only as advisory/Non-Goal items; AUD-gate-journal-7, AUD-commands-4 and AUD-commands-5 appear in no contract"},
      {"what": "grep -rn 'AUD-' src/ tests/", "result": "AUD-whole-project-1 at gate.py:89,413,1266,2163 and test_gate.py:2066,2084; AUD-gate-journal-4 at report.py:641; AUD-gate-journal-5 at test_self_acceptance_on_every_surface.py:5; AUD-commands-3 at test_self_acknowledgement_mark.py:3; no AUD-commands-4/-5 anywhere"},
      {"what": "sed -n '11,328p' CHANGELOG.md | grep -o 'CR-2[0-9][0-9]' | sort -u", "result": "CR-200..CR-244 all appear in the 0.6.0 section; CR-245 absent, matching the rule earlier CR-234 reviews applied to a task holding only an opened record"},
      {"what": "grep -n 'self-accepted|self-acknowledged' over gate.py, report.py, status_view.py, capture.py, cli.py", "result": "report.py:48,996-1003; status_view.py:151-157,259-262; capture.py:449-450; gate.py:2394; cli.py:1834 — both marks exist as the notes claim"},
      {"what": "grep -n 'preserve_output' src/", "result": "review.py:599-616,813-824,1279-1288 — _preserve_output is unconditional; prose_capture_level is read only at review.py:1595,1619-1622, on the recorded-verdict path"},
      {"what": "sed -n '62,140p' src/agentmarshal/journal/attestation.py | grep -n '^    \"'", "result": "thirteen record-type keys, confirming the notes' 'thirteen record types'"},
      {"what": "read created_at of the completed records of CR-237, CR-240, CR-242", "result": "CR-237 2026-10-24T23:31:56.969397Z; CR-240 2026-10-25T00:42:55.587672Z; CR-242 2026-10-25T05:18:06.933820Z — CR-240 and CR-242 land after the gate-journal fixes and both carry src/agentmarshal/journal/gate.py in scope"}
    ],
    "read": [
      "release/audit-0.6.0.toml",
      "CHANGELOG.md (lines 200-330)",
      "README.md (lines 40-65)",
      "docs/harness-setup.md (lines 60-120)",
      "docs/proposals/012-upstream-feedback-channel.md",
      "docs/templates/claude-code-settings.local.json",
      "CONTRIBUTING.md (Releases section, lines 135-203)",
      ".github/scripts/check_release_audit.py",
      "docs/adr/ADR-0001-governance-plane.md",
      ".agentmarshal/journal/tasks/CR-234/contract.md",
      ".agentmarshal/journal/tasks/CR-235/contract.md",
      ".agentmarshal/journal/tasks/CR-236/contract.md",
      ".agentmarshal/journal/tasks/CR-237/contract.md",
      ".agentmarshal/journal/tasks/CR-238/contract.md",
      ".agentmarshal/journal/tasks/CR-239/contract.md",
      ".agentmarshal/journal/tasks/CR-240/contract.md",
      ".agentmarshal/journal/tasks/CR-241/contract.md",
      ".agentmarshal/journal/tasks/CR-242/contract.md",
      ".agentmarshal/journal/tasks/CR-243/contract.md",
      ".agentmarshal/journal/tasks/CR-244/contract.md",
      ".agentmarshal/journal/tasks/CR-243/records/01M5TJF7GQ44BXHYJSAZ6ZHRS3-completed.json",
      ".agentmarshal/journal/tasks/CR-244/records/01M5VD7YG8Z7SD0Y5HT544TCXD-completed.json",
      ".agentmarshal/journal/tasks/CR-240/records/01M5R85C731RJHFD9KN6ZEJK72-completed.json",
      ".agentmarshal/journal/tasks/CR-242/records/01M5RQX8JNS9H5WX3ZGA47J8VQ-completed.json",
      "src/agentmarshal/outbox.py (register, _locate, _run_check, _check, _git, _pinned_blob, _run_status)",
      "src/agentmarshal/project.py (_scaffold_outbox)",
      "src/agentmarshal/extension_trust.py (register, _resolve, _run_list)",
      "src/agentmarshal/journal/review.py (_preserve_output, _reject, _parse_verdict, dry-run path)",
      "src/agentmarshal/journal/attestation.py (RECORD_TYPES)",
      "UPGRADING.md (0.5.0 -> 0.6.0 section)",
      "tests/test_release_audit_check.py (test name list)"
    ],
    "not_run": [
      {"what": "python3 .github/scripts/check_release_audit.py v0.6.0", "why": "the review snapshot is not a git repository and carries no v0.6.0 tag; the sandbox also refused python3 invocations. AC2 is the implementer's report to show"},
      {"what": "git diff dff244b2df8e8003dad6faa4f7aa2ddd2d25422a <tag> --name-only, and git merge-base --is-ancestor 15af26e dff244b", "why": "no git history in the snapshot; commit ordering was derived from the fix tasks' completed-record timestamps instead"},
      {"what": "tomllib parse of release/audit-0.6.0.toml", "why": "the sandbox refused python3; the file was validated by reading it against check_release_audit.py's rules"},
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review and no runnable toolchain here; the coordinator states the sequence passed on b4ee38fa3e071e4b06118e562dab9dbec2e072ba"}
    ]
  },
  "evidence": {
    "audit-comment-gate-journal-paths-incomplete": "release/audit-0.6.0.toml:6-8 '# Areas: gate-journal ran at 15af26e before the freeze by operator # decision (its paths changed afterwards only by the fixes # CR-235/236/237)'. Counter-examples: .agentmarshal/journal/tasks/CR-240/contract.md:5-8 scope = [src/agentmarshal/journal/gate.py, tests/] with records/01M5R85C731RJHFD9KN6ZEJK72-completed.json created_at 2026-10-25T00:42:55.587672Z, and .agentmarshal/journal/tasks/CR-242/contract.md:5-15 scope including src/agentmarshal/journal/gate.py, status_view.py, report.py with records/01M5RQX8JNS9H5WX3ZGA47J8VQ-completed.json created_at 2026-10-25T05:18:06.933820Z — both later than CR-237's completed created_at 2026-10-24T23:31:56.969397Z. Their edits are visible at src/agentmarshal/journal/gate.py:89,392-413,1263,2162 (CR-240) and src/agentmarshal/journal/gate.py:2381-2394 (CR-242). The 'between 15af26e and the freeze' reading is excluded because CR-238/CR-239 (extensions fixes, audited at the freeze) completed at ULIDs 01M5R37P/01M5R3D4, before CR-237's 01M5R43D",
    "audit-model-key-covers-fable-audited-area": "release/audit-0.6.0.toml:3 'model = \"gpt-6-astra\"' versus :10-12 'docs-claims part 2 ... the area was audited with claude-fable-5-1 at the freeze commit', which sources the fixed findings at :106-114 (AUD-docs-claims-2-1, -2-2); .github/scripts/check_release_audit.py ALLOWED_MODELS = (\"gpt-6-astra\",) reads only the single key, and CONTRIBUTING.md:150-151 names gpt-6-astra as the auditing model. The contract's AC1 prescribes both the key and the disclosure, so this is a coordinator-level note",
    "commands-4-5-disposition-uncorroborated": "release/audit-0.6.0.toml:84-94 maps AUD-commands-4 and AUD-commands-5 to CR-237; .agentmarshal/journal/tasks/CR-237/contract.md:15-16,28 names only AUD-gate-journal-5 and -4, and `grep -rn 'AUD-' src/ tests/` yields AUD-gate-journal-4 at src/agentmarshal/journal/report.py:641, AUD-gate-journal-5 at tests/test_self_acceptance_on_every_surface.py:5 and AUD-commands-3 at tests/test_self_acknowledgement_mark.py:3, with no AUD-commands-4 or -5 anywhere in the repository",
    "readme-capture-line-not-reflowed": "README.md:54 '  reviewer's raw output at any level. Still roadmap: the `economics` and `sessions`' is 83 columns wide, against lines 43-58 of the same bullet which wrap at 78 or less"
  }
}
AGENTMARSHAL_VERDICT_END
