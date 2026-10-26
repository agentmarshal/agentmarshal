## Что проверено

Прочитал diff целиком и сверил каждое новое утверждение с кодом в снапшоте (`src/`, `tests/`, `openspec/specs/`, `CHANGELOG.md`, `docs/adr/`). Ниже — сначала замечания, потом разбор по критериям приёмки.

### Блокирующие

**`docs-base-read-exception-missing`** — зачистка по третьему критерию неполная: исключение операционной полосы добавлено в `docs/threat-model.md:23`, `docs/self-hosting-workflow.md:161`, `docs/sidecar.md:52` и в глоссарий `docs/overview.md:133`, но два места в `docs/` по-прежнему утверждают безусловное «только из базы»: `docs/quickstart.md:323-324` («The gate always reads the contract from the committed base, never from the candidate, so a task can never widen its own scope») и абзац `docs/overview.md:75-77` («reads the contract … at the base from the **base** side, never from the candidate»), то есть в том же overview.md исправлен глоссарий и пропущен текст выше. Код делает исключение: `src/agentmarshal/journal/gate.py:1006-1032` (`_operational_contract` читает `contract.md` из `resolved_commit`, когда база его не держит), тест — `tests/test_gate_operational.py:119 test_a_task_opened_within_the_candidate_reads_the_candidate_contract`. Критерий говорит «and any other place», так что это не вкусовое.

**`threat-model-one-candidate-read-false`** — новая вставка в `docs/threat-model.md:253-255` («the one candidate-side read the gate makes is the operational lane's opening contract») — ложное утверждение о коде, причём именно по теме предложения, к которому пришито: gate читает из дерева кандидата ещё как минимум трижды — `.agentmarshal/switches.toml` кандидата на операционной полосе (`gate.py:1513-1518`, `candidate_source = f"{resolved_commit}:{SWITCHES_RELPATH}"`), полный листинг дерева кандидата для проверки полноты удаления манифеста (`gate.py:1842-1847`, тест `tests/test_gate.py:1418`) и блобы добавленных записей (`gate.py:2169`), плюс содержимое диффа кандидата для leak-scan (`gate.py:2343-2350` → `leak_scan_diff`, `gate.py:1186-1198`). Верно было бы сказать «единственный доверенный governance-вход, читаемый со стороны кандидата», а не «единственное чтение».

**`sidecar-status-transcript-stale`** — пятый критерий требует, чтобы транскрипты `docs/sidecar.md` совпадали с выводом 0.6.0; транскрипт `status` в `docs/sidecar.md:316-329` начинается со stderr-строки `Placement: sidecar`, но не содержит трёх строк, которые 0.6.0 печатает в том же stderr на каждом прогоне `status`: `journal:`, `process log:`, `local state:` (`src/agentmarshal/cli.py:1474` → `src/agentmarshal/journal/status_view.py:852-861`; сам quickstart описывает их в прозе на `docs/quickstart.md:588-591`). В sidecar это ещё и содержательно важно — пути указывают на репозиторий журнала, а не на host. Транскрипт `gate` при этом исправен (см. ниже), так что правка касается одного блока.

### Советующие

**`harness-setup-plan-file-not-shipped`** — `docs/harness-setup.md:38-41` перечисляет среди того, что «holds» локальное состояние, «the plan file». В 0.6.0 его нет: `plan.toml` — только свойство пути (`src/agentmarshal/localstate.py:70-73`), ничего в `src/` его не читает и не пишет, а `CHANGELOG.md:269-272` прямо говорит «nothing reads `plan.toml`»; карта ADR-0014 (`docs/adr/ADR-0014-where-things-live.md:160-166`) под `.git/agentmarshal/` его тоже не называет. Это ровно тот класс утверждения, который убирает второй критерий (нереализованное названо как существующее).

**`harness-setup-framework-scripts-stale`** — в том же файле `docs/harness-setup.md:12` и `:75` остались «the framework scripts» как семейство команд, которое нужно внести в allowlist, хотя этим же диффом из шаблона убраны `./agentmarshal/scripts/*` и `./agentmarshal/bin/*` в пользу `Bash(agentmarshal *)` (`docs/templates/claude-code-settings.local.json:16`); никаких скриптов фреймворк в 0.6.0 не поставляет (`grep -rln am-merge` по репозиторию даёт только docs и журнал).

**`edits-left-unwrapped-prose`** — правки вставлены без переформатирования абзацев, остались висячие короткие строки посреди текста: `docs/github-enforcement.md:95-98` (строка 97 — «that requirement on this»), `docs/self-hosting-workflow.md:99-100` и `:162-165`, `docs/threat-model.md:255-256`. Чисто косметика, но в документе, который правят ради читаемости, заметна.

### Критерии приёмки — где выполнено и чем подтверждается

- **AC1 (типы записей)** — выполнено: `docs/known-defects.md:13` говорит «thirteen», реестр `src/agentmarshal/journal/attestation.py:62-114` объявляет ровно 13 типов (opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext); реестр закреплён тестом `tests/test_attestation.py:142-160` (равенство реестра и производных множеств `status.py`).
- **AC2 (user scope)** — выполнено: `docs/harness-setup.md:34-49` переносит trust/switches/личные расширения под `.git/agentmarshal/` и помечает `~/.config`/`~/.local/share` как «decided but not implemented»; это совпадает с `docs/adr/ADR-0014-where-things-live.md:160-168` («later, when an adopter asks») и `CHANGELOG.md:265-269`; «nothing in the tool reads or writes them» подтверждается тем, что единственные `expanduser`/`Path.home` в `src/` относятся к host сайдкара (`src/agentmarshal/project.py:440`, `src/agentmarshal/journal/placement.py:53`). Расположения локального состояния закреплены тестом `tests/test_localstate.py:110-120`.
- **AC3 (исключение операционной полосы)** — не выполнено полностью, см. `docs-base-read-exception-missing`. Там, где текст добавлен, он точен: условия полосы в `docs/threat-model.md:23-31` (дифф = `switches.toml` + подкаталог задачи; `scope` ровно `[".agentmarshal/switches.toml"]`; в сайдкаре полоса не предлагается) дословно соответствуют `gate.py:1054-1102` и `gate.py:1386-1393`, тесты — `tests/test_gate_operational.py:57 test_the_operational_lane_admits_a_switches_only_candidate`, `:119` и `:205 test_in_a_sidecar_the_operational_lane_is_not_offered`; цитата спецификации «an operational change takes its own gate lane» существует (`openspec/specs/gate-lanes/spec.md:170`).
- **AC4 (write-time и outbox)** — выполнено: четыре таймстемпа и `artifacts.ref` описаны в `docs/threat-model.md:131-137` и реализованы правилами `timestamp-text` (`src/agentmarshal/journal/records.py:618-636`) и `artifact-ref-text` (`records.py:1410-1428`), тесты `tests/test_record_text_safety.py:321` и `:400`; outbox-отказы в `docs/threat-model.md:189-197` реализованы в `src/agentmarshal/outbox.py:174-192` (симлинк на `.agentmarshal` и `upstream` до любой записи), `outbox.py:832-851` + `:704-708` и `:766` (отказ от файла, который git преобразует при staging), `outbox.py:981-1048` (сверка staged-блобов и откат index), тесты `tests/test_outbox.py:1923 test_a_linked_outbox_refuses_a_command_before_it_writes`, `:2114 test_check_refuses_a_draft_a_clean_filter_would_transform`, `:2046` для `send`. Все три цитаты спецификации существуют дословно (`openspec/specs/outbox/spec.md:502`, `:532`, `:181`). Абзац про sidecar-вывод цитирует реальные строки: `src/agentmarshal/journal/placement.py:37,45` и `src/agentmarshal/cli.py:950,993,1005,1204,1206`.
- **AC5 (версии, транскрипты, цитата gate, am-merge)** — выполнено, кроме транскрипта `status` (см. выше). Пины 0.6.0 совпадают с `pyproject.toml:3` / `src/agentmarshal/__init__.py:3`; транскрипт gate в `docs/sidecar.md:226-237` совпадает байт-в-байт с закреплённым фикстуром `tests/fixtures/gate/sidecar-implementation.stdout`, который проверяет `tests/test_gate.py:529 test_default_run_transcript_matches_the_committed_fixture[sidecar-implementation]` (транскрипт gate в quickstart `:468-478` — с `embedded-implementation`); заметка про `doctor` верна — `doctor` зовёт `resolve_placement` без `require_host` (`src/agentmarshal/doctor.py:884` против `placement.py:84-95`), так что host только разрешается в путь; цитата закрывающей строки в `docs/github-enforcement.md:95-96` точна (`src/agentmarshal/cli.py:1007-1008`, тест `tests/test_gate.py:942`/`:973`), и шаблон CI действительно зовёт `--without-review` (`templates/github/agentmarshal-governance.yml:78`); `am-merge`/`mr.sh` в репозитории отсутствуют, так что новая формулировка «operator tooling outside this repository» верна.
- **AC6 (прочее)** — ссылки в изменённых файлах разрешаются (все относительные цели существуют, анкер `#research-findings-loop` есть в `docs/sidecar.md:419`); датированные исторические заметки («since 0.3.0», «Since 0.5.0», амендменты ADR) не тронуты; вне `docs/` дифф ничего не меняет. Полную последовательность CI я не запускал — доверяю зафиксированному факту прохождения на этом коммите; изменение только документационное, тестов на содержимое `docs/` в `tests/` нет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8e5e62120c62c6ab683be13f000a71660f2f5b76",
  "verdict": "changes_required",
  "findings": [
    "docs-base-read-exception-missing",
    "threat-model-one-candidate-read-false",
    "sidecar-status-transcript-stale"
  ],
  "advisory_findings": [
    "harness-setup-plan-file-not-shipped",
    "harness-setup-framework-scripts-stale",
    "edits-left-unwrapped-prose"
  ],
  "classes": {
    "docs-base-read-exception-missing": "contract-mismatch",
    "threat-model-one-candidate-read-false": "claim-accuracy",
    "sidecar-status-transcript-stale": "contract-mismatch",
    "harness-setup-plan-file-not-shipped": "claim-accuracy",
    "harness-setup-framework-scripts-stale": "claim-accuracy",
    "edits-left-unwrapped-prose": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"never from the candidate|from the committed base|never the candidate\" docs/", "result": "hits only at docs/self-hosting-workflow.md:161, docs/threat-model.md:23, docs/threat-model.md:252, docs/quickstart.md:323 — the last one carries no exception"},
      {"what": "grep -rn \"widen its own scope|cannot widen\" docs/", "result": "docs/overview.md:77 states 'never from the candidate, so a change can never widen its own scope' with no exception"},
      {"what": "read src/agentmarshal/journal/attestation.py RECORD_TYPES", "result": "13 entries: opened, review, acceptance, completed, abandoned, reopened, amendment, session, finding, check, agreement, acknowledgement, ext"},
      {"what": "grep -rn \"expanduser|Path.home()|XDG_|APPDATA\" --include=*.py src/", "result": "only project.py:440 and placement.py:53, both the sidecar host — no user-scope directory is read or written"},
      {"what": "diff of docs/sidecar.md gate block against tests/fixtures/gate/sidecar-implementation.stdout", "result": "identical line set, including 'gate: advisory checks passed; decides no merge'"},
      {"what": "grep -rn \"plan_file|plan.toml\" src/ tests/", "result": "src/agentmarshal/localstate.py:70-73 (path property) and two tests only — nothing reads or writes it"},
      {"what": "grep -rln am-merge over the repository", "result": "only docs/ and .agentmarshal/journal evidence — no am-merge or mr.sh file is shipped"},
      {"what": "grep -n '^### Requirement' openspec/specs/outbox/spec.md and gate-lanes/spec.md", "result": "all four quoted requirement titles exist verbatim (outbox:181, :502, :532; gate-lanes:170)"},
      {"what": "relative-link check over the changed docs (grep of link targets + ls of docs/adr, UPGRADING.md)", "result": "every target exists; the one anchor used (#research-findings-loop) matches a heading"}
    ],
    "read": [
      "docs/github-enforcement.md",
      "docs/harness-setup.md",
      "docs/known-defects.md",
      "docs/overview.md (lines 70-140)",
      "docs/quickstart.md (lines 1-30, 240-340, 440-640)",
      "docs/self-hosting-workflow.md",
      "docs/sidecar.md",
      "docs/threat-model.md (lines 15-50, 100-215, 240-340)",
      "docs/templates/claude-code-settings.local.json",
      "docs/adr/ADR-0014-where-things-live.md (section 12)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md (scope table)",
      "CHANGELOG.md (0.6.0 sections)",
      "src/agentmarshal/journal/gate.py (950-1110, 1380-1580, 1838-1860, 2160-2175, 2320-2360)",
      "src/agentmarshal/journal/records.py (580-700, 1405-1430)",
      "src/agentmarshal/journal/placement.py",
      "src/agentmarshal/journal/status_view.py (834-862)",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/outbox.py (1-60, 150-210, 680-720, 820-860, 930-1050)",
      "src/agentmarshal/cli.py (905-1010, 1430-1480)",
      "src/agentmarshal/doctor.py (870-905)",
      "tests/test_gate.py (470-560, 925-975)",
      "tests/fixtures/gate/sidecar-implementation.stdout",
      "tests/fixtures/gate/embedded-implementation.stdout",
      "templates/github/agentmarshal-governance.yml"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review in a non-git snapshot; the coordinator states the full sequence passed on this commit and the diff touches only docs/"},
      {"what": "an end-to-end sidecar run to capture the live status transcript", "why": "no git repository in the snapshot; the stale lines were established from cli.py:1474 and status_view.py:852-861 instead"}
    ]
  },
  "evidence": {
    "docs-base-read-exception-missing": "docs/quickstart.md:323-324 'The gate always reads the contract from the committed base, never from the candidate, so a task can never widen its own scope'; docs/overview.md:75-77 'reads the contract ... at the base from the **base** side, never from the candidate'; the exception they omit is src/agentmarshal/journal/gate.py:1024-1027 (contract read at resolved_commit) with tests/test_gate_operational.py:119",
    "threat-model-one-candidate-read-false": "docs/threat-model.md:253-255 '(the one candidate-side read the gate makes is the operational lane's opening contract ...)' vs src/agentmarshal/journal/gate.py:1513-1518 (candidate's .agentmarshal/switches.toml), gate.py:1842-1847 (ls-tree -r resolved_commit), gate.py:2169 (git show resolved_commit:<record>), gate.py:2343-2350 + gate.py:1186-1198 (leak scan over merge_base..candidate)",
    "sidecar-status-transcript-stale": "docs/sidecar.md:316-329 shows 'Placement: sidecar' then stdout only; src/agentmarshal/cli.py:1474 calls print_paths on every status run and src/agentmarshal/journal/status_view.py:852-861 prints 'journal:', 'process log:', 'local state:' on stderr (described in docs/quickstart.md:588-591)",
    "harness-setup-plan-file-not-shipped": "docs/harness-setup.md:38-41 'That one place holds ... and the plan file' vs CHANGELOG.md:269-272 'there is no agentmarshal next and nothing reads plan.toml'; grep -rn 'plan_file|plan.toml' src/ returns only src/agentmarshal/localstate.py:70-73; ADR-0014's map (docs/adr/ADR-0014-where-things-live.md:160-166) does not list it",
    "harness-setup-framework-scripts-stale": "docs/harness-setup.md:12 'the framework scripts' and :73-75 'and the framework scripts' against docs/templates/claude-code-settings.local.json:16, where this diff replaced './agentmarshal/scripts/*' and './agentmarshal/bin/*' with 'Bash(agentmarshal *)'",
    "edits-left-unwrapped-prose": "docs/github-enforcement.md:97 is the 24-character orphan 'that requirement on this'; same pattern at docs/self-hosting-workflow.md:99-100, :162-165 and docs/threat-model.md:255-256"
  }
}
AGENTMARSHAL_VERDICT_END
