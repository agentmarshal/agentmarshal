Проверил контракт CR-246 против снапшота на `c9ac48782a8a6a2db5692de04a8e783f64d6805f`.

## Что критерии закрывают

**Критерий 1 (file-form manifest читается base-tree reader'ом) — выполнен.** `_base_extensions` заменён на `_base_manifests` (`src/agentmarshal/stages.py:335-351`), который читает `_manifest_from_tree` для *каждого* имени из `_extension_names_at_tree(...)[0]`, включая file-form. Отказ приходит из самого reader'а и называет extension и его tree source (`src/agentmarshal/journal/gate.py:662-731`), а «file-form не планирует stage» держится структурно: `_refuse_single_file_directory_paths` (`src/agentmarshal/journal/extensions.py:525-545`) отвергает любой file-form manifest, назвавший хоть один путь под `bin/`/`lock/`, а `stage.command` — всегда такой путь, так что file-form либо не имеет stage, либо отказан. Демонстрируют `tests/test_stages.py:361` (broken) и `tests/test_stages.py:392` (command-declaring), общий runner через `complete` — `tests/test_complete_stages.py:261`; старый `tests/test_stages.py:331` (schema-1 file-form без stage) остаётся зелёным.

**Критерий 2 (маскирование пути в диагностике leak-scan) — выполнен.** `src/agentmarshal/cli.py:1788-1792`: `escape_for_display(safe_path(str(error), markers))`, порядок правильный (сначала маскирование, потом escape), `markers` к этому моменту уже прочитаны с trusted-стороны (`cli.py:1735-1741`). Демонстрирует `tests/test_leak_scan_acknowledgements.py:305`.

**Критерий 3 (`--skip-ext` с shared-именем на operational lane) — выполнен.** Отказ вынесен из-под второго `try` и поставлен перед operational-ветвью (`src/agentmarshal/stages.py:1061-1073`), решается только по именам из `_extension_names_at_tree`, манифесты не читаются. Это ровно то, что требует ADR-0013 решение 16 («ни флаг, ни локальная настройка») и spec `openspec/specs/extension-stages/spec.md:1712-1723`. Демонстрируют `tests/test_gate_operational.py:746` (`stage run`) и `tests/test_gate_operational.py:779` (`complete`), оба с намеренно битым манифестом и проверкой `"invalid TOML" not in captured.err`.

**Критерий 4 (раскрытие нереализованного runtime lookup) — выполнен.** `docs/threat-model.md:506-513` и `CHANGELOG.md:320-326`. Оба утверждения проверил по коду: `extension runtime <name>` действительно существует и только в doctor (`src/agentmarshal/doctor.py:523-575`), `PATH` стадии фиксирован `/usr/bin:/bin` (`src/agentmarshal/stages.py:180,707`), цитата спеки «the command runs as an argv process under the core's interpreter» существует (`openspec/specs/extension-stages/spec.md:164`). Тестом не покрывается — это prose.

**Критерий 5 (git 2.31) — выполнен.** `README.md:117-121`, `docs/quickstart.md:19-22`, `docs/sidecar.md:83-86`. Сходится с `src/agentmarshal/project.py:400-407` (`rev-parse --path-format=absolute`) и с собственным порогом doctor'а `MINIMUM_GIT_VERSION = (2, 31)` (`src/agentmarshal/doctor.py:70-73`). Тестом не покрывается — prose.

## Блокирующие находки

**CR-246-01-audit-record-missing** — критерий 6 не выполнен вообще. `release/audit-0.6.0.toml` не изменён: ни одного `[[finding]]` с id `SOL-extensions-1`, `SOL-extensions-2`, `SOL-commands-2`, `SOL-docs-claims-1-1`, `SOL-docs-claims-1-3`, ни строки `task = "CR-246"`, ни комментария про gpt-6.1-sol-прогон; файл кончается на `AUD-whole-project-1` (строка 133). И `CHANGELOG.md:227` по-прежнему перечисляет только CR-234…CR-244. Следствие проверяемое: `python3 .github/scripts/check_release_audit.py v0.6.0` не напечатает `release audit: passed` — `ALWAYS_ALLOWED` (строки 35-43) не покрывает `src/agentmarshal/stages.py`, `docs/quickstart.md` и `docs/sidecar.md`, и ни один из перечисленных в аудите task'ов не держит их в scope (CR-242 даёт только `cli.py` и `tests/`; `stages.py` упомянут в CR-234 лишь в prose критериев, не в `scope`), так что проверка diff'а на строках 348-355 выдаст по отказу на каждый из трёх путей.

**CR-246-02-upgrading-outbox-note-missing** — критерий 7, первая половина, не выполнена. `UPGRADING.md` входит в scope (поправка контракта от 2026-10-26), но не изменён: в разделе `0.5.0 → 0.6.0` про outbox есть только пункт «skip files already sent» (`UPGRADING.md:50`), и ни слова про отказ на файле, байты которого git застейджил бы иначе, ни про `core.autocrlf` / `text`-`eol`-атрибут / clean filter, ни про лекарство `.agentmarshal/upstream/** -text`. Поведение при этом реально отгружено и описывать его есть что: `src/agentmarshal/outbox.py:756-765` печатает «git would transform it on staging», причина берётся из `_transform_cause` (`outbox.py:883-917`), который разбирает `check-attr filter/text/eol` и `core.autocrlf`.

**CR-246-03-readme-capture-sentence-unchanged** — критерий 7, вторая половина, не выполнена, и формулировка остаётся неточной. `README.md:53-54` всё ещё читается «a verdict that is refused keeps the reviewer's raw output at any level». Контракт требует сказать именно про отказ launcher'а на malformed reviewer output — и так оно и есть в коде: сырой вывод сохраняет `_preserve_output` (`src/agentmarshal/journal/review.py:599-616`), вызываемый только из `_reject` (`review.py:813-824`) и `review.py:1284`, то есть на пути `ReviewLaunchError`. Записанный verdict `changes_required` ничего такого не сохраняет, так что текущая фраза описывает поведение, которого нет.

## Advisory

**CR-246-A1-spec-operational-lane-unreconciled** — `openspec/specs/extension-stages/spec.md:44-52` требует про operational lane: «One exception precedes the manifest read for `--phase pre-gate` … SHALL print one line … and SHALL run no stage … returning success» — безусловно. После диффа это перестало быть верным для `--skip-ext <shared name>`: отказ опережает lane и даёт exit 1 без этой строки (`src/agentmarshal/stages.py:1061-1073`, и так же утверждает `tests/test_gate_operational.py:766-774`). Два требования спеки теперь противоречат друг другу на этом входе; `openspec/` не в scope контракта, а править `openspec/specs/` руками AGENTS.md запрещает — но тогда это следовало назвать departure'ом в отчёте, чего в диффе не видно. Нужен openspec change, который сузит формулировку lane'а.

Полную CI-последовательность я не запускал — выполнение команд в этой сессии недоступно; про прохождение CI на этом коммите опираюсь на твою вводную.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "c9ac48782a8a6a2db5692de04a8e783f64d6805f",
  "verdict": "changes_required",
  "findings": [
    "CR-246-01-audit-record-missing",
    "CR-246-02-upgrading-outbox-note-missing",
    "CR-246-03-readme-capture-sentence-unchanged"
  ],
  "advisory_findings": [
    "CR-246-A1-spec-operational-lane-unreconciled"
  ],
  "classes": {
    "CR-246-01-audit-record-missing": "contract-mismatch",
    "CR-246-02-upgrading-outbox-note-missing": "contract-mismatch",
    "CR-246-03-readme-capture-sentence-unchanged": "claim-accuracy",
    "CR-246-A1-spec-operational-lane-unreconciled": "scope"
  },
  "verification": {
    "executed": [
      {"what": "grep -n 'CR-246|SOL-' release/audit-0.6.0.toml", "result": "no match; file unchanged, 133 lines, last finding AUD-whole-project-1"},
      {"what": "grep -o 'task = \"CR-[0-9]*\"' release/audit-0.6.0.toml", "result": "CR-234..CR-244 only; no CR-246"},
      {"what": "grep -n 'CR-24[0-9]' CHANGELOG.md", "result": "line 227 only: 'Fixes from the release audit (CR-234 ... CR-244)'"},
      {"what": "grep -n 'autocrlf|-text|clean filter' UPGRADING.md", "result": "no match"},
      {"what": "grep -n 'a verdict that is refused keeps' README.md", "result": "README.md:53 unchanged"},
      {"what": "grep -n 'stages.py\"|cli.py\"|quickstart.md\"|sidecar.md\"|\"tests/\"' over the contracts of every task listed in release/audit-0.6.0.toml", "result": "only tests/ (CR-235/236/237/239/240/241/242) and src/agentmarshal/cli.py (CR-242); stages.py, docs/quickstart.md, docs/sidecar.md uncovered"},
      {"what": "grep -rn 'extension runtime' src/ docs/", "result": "doctor.py:524,575 and threat-model.md:510 — the check exists only in doctor"},
      {"what": "grep -rn '_MINIMAL_PATH' src/agentmarshal/", "result": "stages.py:180 = '/usr/bin:/bin', used at stages.py:707"},
      {"what": "grep -rn 'path-format' src/ docs/ README.md", "result": "project.py:407, doctor.py:70-151, README.md:120, quickstart.md:21, sidecar.md:85"},
      {"what": "grep -rn '_base_extensions|_base_manifests' src/ tests/", "result": "only the three new call sites in stages.py; no stale caller"},
      {"what": "grep -rn '_preserve_output' src/agentmarshal/journal/review.py", "result": "defined 599, called only at 821 (_reject) and 1284 — launcher paths"}
    ],
    "read": [
      "src/agentmarshal/stages.py:330-360, 980-1200",
      "src/agentmarshal/cli.py:1700-1815",
      "src/agentmarshal/journal/gate.py:600-735, 949-1004",
      "src/agentmarshal/journal/extensions.py:500-586",
      "src/agentmarshal/journal/capture.py:312-332",
      "src/agentmarshal/journal/review.py:590-625, 806-830",
      "src/agentmarshal/doctor.py:60-80, 505-580",
      "src/agentmarshal/outbox.py:740-775, 830-920",
      "src/agentmarshal/project.py:388-420",
      ".github/scripts/check_release_audit.py (whole file)",
      "release/audit-0.6.0.toml (whole file)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:225-290",
      "openspec/specs/extension-stages/spec.md:40-95, 1705-1745",
      "docs/threat-model.md:278-305, 495-520",
      "CHANGELOG.md:220-335",
      "README.md:40-125",
      "UPGRADING.md:1-90",
      "docs/quickstart.md:14-25",
      "docs/sidecar.md:78-90",
      "tests/test_stages.py:28-160, 330-420",
      "tests/test_complete_stages.py:1-120, 258-300",
      "tests/test_gate_operational.py:20-80, 740-820",
      "tests/test_leak_scan_acknowledgements.py:300-330",
      "tests/test_personal_extensions.py:90-175, 860-905",
      ".agentmarshal/journal/tasks/CR-234/contract.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "command execution is unavailable in this read-only session (no approval for uv/python3); relying on the coordinator's statement that the sequence passed at this commit"},
      {"what": "python3 .github/scripts/check_release_audit.py v0.6.0 in a throwaway clone with a local tag", "why": "the snapshot is not a git repository and command execution is unavailable; the refusal is derived by reading the script's ALWAYS_ALLOWED list and the listed tasks' contract scopes"}
    ]
  },
  "evidence": {
    "CR-246-01-audit-record-missing": "release/audit-0.6.0.toml ends at line 133 with AUD-whole-project-1; `grep -n 'CR-246\\|SOL-' release/audit-0.6.0.toml` -> no output. CHANGELOG.md:227 names CR-234..CR-244 only. .github/scripts/check_release_audit.py:35-43 (ALWAYS_ALLOWED) and :348-355 (per-path refusal) vs. the listed tasks' scopes, which cover neither src/agentmarshal/stages.py nor docs/quickstart.md nor docs/sidecar.md.",
    "CR-246-02-upgrading-outbox-note-missing": "UPGRADING.md:50 is the only outbox item in the 0.5.0 → 0.6.0 section; `grep -n 'autocrlf\\|-text\\|clean filter' UPGRADING.md` -> no output. The undocumented behaviour: src/agentmarshal/outbox.py:756-765 and _transform_cause at outbox.py:883-917.",
    "CR-246-03-readme-capture-sentence-unchanged": "README.md:53-54 'the level governs a recorded verdict's prose; a verdict that is refused keeps the reviewer's raw output at any level' — unchanged by the diff, while src/agentmarshal/journal/review.py:599-616 is reached only through _reject (review.py:813-824) and review.py:1284, i.e. a ReviewLaunchError on malformed reviewer output.",
    "CR-246-A1-spec-operational-lane-unreconciled": "openspec/specs/extension-stages/spec.md:44-52 ('One exception precedes the manifest read ... SHALL print one line ... returning success') vs. src/agentmarshal/stages.py:1061-1073 and tests/test_gate_operational.py:766-774 (exit 1, no operational line, captured.out == '')."
  }
}
AGENTMARSHAL_VERDICT_END
