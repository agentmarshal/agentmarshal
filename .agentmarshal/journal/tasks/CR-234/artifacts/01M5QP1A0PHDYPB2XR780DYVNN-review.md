Проверил diff против кода и спецификаций. Ниже — по одной строке прозы на каждый finding, затем разбор критериев приёмки.

## Blocking

**BLK-OPENSPEC-MANIFEST-PATH** (claim-accuracy) — `CHANGELOG.md:193-196` называет манифест, который пинит OpenSpec, по пути `.agentmarshal/extensions/openspec/manifest.toml`; в репозитории такого файла нет — расширение объявлено в file form как `.agentmarshal/extensions/openspec.toml` (`version = "1.15.0"` на строке 20). Сам пин 1.15.0 и регенерация skills под `.agents/skills/` верны, неверен только путь — и именно он единственное проверяемое указание в записи.

**BLK-SWITCH-OFF-CONTRACT-SCOPE** (claim-accuracy) — `CHANGELOG.md:77-79` утверждает, что `extension switch off` открывает operational task, «whose generated contract scopes exactly `.agentmarshal/switches.toml` and the task's own records»; `switch_off.py:463` пишет `scope = [".agentmarshal/switches.toml"]` и только его, а `openspec/specs/gate-lanes/spec.md:177-178` требует scope ровно `[".agentmarshal/switches.toml"]` — контракт с двумя записями на operational lane не попадёт вообще. Следующее предложение (строки 80-81) описывает lane правильно, так что ошибка именно в описании контракта и противоречит ADR-0013 decision 17 в том виде, в каком его зафиксировала спецификация.

**BLK-SESSION-ID-ALREADY-SHIPPED** (claim-accuracy) — `CHANGELOG.md:218-220` в «What 0.6.0 leaves out» пишет, что session-id field из proposal 042 «arrive[s] under a later record schema»; поле `cli_session` — «the CLI session id a resume needs» по ADR-0022:133 — это schema-7 поле, которое уже есть в `records.py:208,520,2288` и во флаге `cli.py:424` (`--cli-session`), и раздел 0.5.0 того же файла (`CHANGELOG.md:336-338`) прямо называет его отгруженным. Абзац, который должен перечислять только решённое-но-неотгруженное, объявляет неотгруженным то, что вышло в 0.5.0.

**BLK-PROPOSAL-040-NOT-SHIPPED** (claim-accuracy) — `docs/proposals/README.md:155` теперь говорит «the checkout-free write shipped in 0.6.0 with the transaction helper of 019 and 035»; proposal 040 просил «journal records without switching the user's working tree … so parallel tasks do not contend on one checkout» (`040-…md:59-64`), а отгруженный `templates/journal-transaction.sh:64-65,116` требует быть на default branch и делает `git switch -c` — он переключает дерево пользователя, то есть ровно то, чего предложение просило избежать. Это строка, которая говорит «shipped» про то, что не отгружено.

**BLK-PROPOSALS-STALE-ROWS** (contract-mismatch) — в `docs/proposals/README.md` остались непоправленными строки, части которых вышли в 0.5.0: `:175` (026) — «`record-session --if-missing` and the per-file leak scan accepted, not yet shipped» и «the `evidence` field accepted with the review-evidentiality decision», тогда как `cli.py:463` даёт `--if-missing`, `records.py:270` — поле `evidence`, а соседняя строка `:152` (037) уже сама признаёт, что per-file leak scan «shipped in 0.5.0»; `:116` (041) — «a "report finished" session flag … not shipped yet» при существующем `report_ready` (`records.py:209`, `cli.py:426`, `status_view.py:688`); `:117` (042) — «the session-id field with the records of a later decision … not shipped yet»; `:174` (025) — «retroactivity accepted as a principle, mechanism undecided», хотя ADR-0015 его решил и 0.5.0 отгрузил (`CHANGELOG.md:250-256`). Критерий 5 требует, чтобы каждое предложение, отгруженное в 0.5.0 или 0.6.0, было показано отгруженным с версией.

**BLK-REPORT-UNMEASURED-RENDERING** (claim-accuracy) — `CHANGELOG.md:185-186` пишет, что `report` «counts them on lines of their own — `unmeasured=<n>` and `unmeasured_without_cost`»; в коде это tab-поле, дописываемое к уже существующим строкам (`report.py:742,779,812`), а спецификация подчёркивает «as its last field and nothing more» (`session-activity/spec.md:506,648`); строки `unmeasured_without_cost` нет ни в одном выводе — это имя поля dataclass (`report.py:139,172`), JSON-режима у `report` нет. Обе половины утверждения об одном и том же выводе неверны.

## Advisory

**ADV-CODE-SPAN-LINE-WRAP** (style) — два inline-code span'а в `CHANGELOG.md` разорваны переводом строки, так что в рендере путь получает пробел внутри: `:164-165` даёт `.agentmarshal/journal/ tasks/<task-id>/`, `:194-195` — `.agentmarshal/extensions/openspec/ manifest.toml`.

**ADV-EXTENSION-LIST-SCOPE** (claim-accuracy) — `CHANGELOG.md:30-34` говорит, что `extension list` печатает `granted` / `not granted` / `changed after approval: <path> (<kind>)` «per shared extension»; `extension_trust.py:719-742` перебирает только каталоги под `.agentmarshal/extensions/` и молча пропускает не-каталог (`continue` на 724-725), так что shared-расширение в file form — как сам `openspec.toml` этого репозитория — не получает строки вовсе.

## Критерии приёмки

- **1 (секция 0.6.0)** — выполнен: `CHANGELOG.md:11-234` стоит выше `## 0.5.0 — 2026-10-23` (:236), каждый заголовок называет свои CR, CR-205…CR-235 покрыты целиком (CR-205, CR-226, CR-230 — закрывающей строкой :234; CR-235 — последняя завершённая задача, у CR-236/CR-237 только `opened`), вводный абзац (:13-24) заявляет отсутствие изменений record/contract-header/manifest schema и ссылается на UPGRADING.md; отсутствие schema 8 подтверждается `records.py:227,239,247,300` (всё ≤ 7). Теста нет — документация.
- **2 (покрытие wave B)** — выполнен по составу и подтверждён кодом: grants (`extension_trust.py:581-599`, тест `tests/test_extension_trust.py`), result-строки `checked` / `failed (exit <n>)` / `did not finish (timeout)` / `not run (<reason>)` / `switched off (…)` (`stages.py:950-962`, `tests/test_extensions.py`), `record-ext` с 64 KiB и `payload_sha256` (`record_ext.py:223-252,314`, `tests/test_ext.py`), `doctor`-проверки `extension manifest <name>` / `extension runtime <name>` (`doctor.py:548-575`, `tests/test_doctor_extensions.py`, `tests/test_doctor_wrapper_runtime.py`), `addressee not found` (`validate.py:188-191`), switches из base и `switched off: <name> since <task> (<reason>)` (`stages.py:1388`, `cli.py:1445`), operational lane и `accept --pause/--operational` (`gate.py:1355`, `acceptance.py:105-153`, `tests/test_gate_operational.py`, `tests/test_pause_and_operational_acceptance.py`), isolation ровно в формулировках threat-model (`docs/threat-model.md:446-467` ↔ `stages.py:1489-1502`, `tests/test_isolation.py`), `complete` со стадиями и `--target` (`cli.py:352-356,1134`, `tests/test_complete_stages.py`), personal extensions (`stages.py:667-675`, `tests/test_personal_extensions.py`), CR-207 (`templates/journal-transaction.sh`, `tests/test_journal_transaction.py`), outbox `skipped as sent: <n>` (`outbox.py:722-723`, `tests/test_outbox.py`), unmeasured (`tests/test_unmeasured_session_usage.py`), release-audit как процесс (`.github/workflows/release.yml:53-62`, `tests/test_release_audit_check.py`). Не выполнен в части «each checked against the code it describes» — BLK-OPENSPEC-MANIFEST-PATH, BLK-SWITCH-OFF-CONTRACT-SCOPE, BLK-REPORT-UNMEASURED-RENDERING.
- **3 (абзац «что не вошло»)** — не выполнен: все шесть пунктов названы с держащим их решением (`CHANGELOG.md:210-232`), ADR-0013:166 действительно говорит «the user scope arrives when an adopter asks», `mode: resolution`/`carried_approval` в коде отсутствуют, `agentmarshal next` и `plan.toml` нигде не читаются — но BLK-SESSION-ID-ALREADY-SHIPPED.
- **4 (UPGRADING 0.5.0 → 0.6.0)** — выполнен: `UPGRADING.md:3-54` над `## 0.4.1 → 0.5.0`; проверил `not run (not granted)` (`stages.py:507`), `changed after approval` (`stages.py:514`), `CI=true` (`stages.py:1124,1215`), PASS-строку operational lane (`gate.py:1355`), `--target` (`cli.py:352-356`), `SENT`/`--index` на `check`/`send`/`status` (`outbox.py:117-141`), пин 1.15.0 (`.agentmarshal/extensions/openspec.toml:20`). Теста нет.
- **5 (индексы и документация)** — выполнен частично: `docs/README.md:87-88` добавляет строки для 044 и 045 в том же виде, что 041-043; threat-model (`docs/threat-model.md:252-269`) называет все четыре command-level refusal'а и они сходятся с `stages.py:1035-1049,1097-1100` и `stages.py:1560-1567`, цитируемые сценарии существуют дословно (`extension-stages/spec.md:80,92,96,308`); README (`README.md:132,161-166`) называет outbox среди записей `init` и это подтверждает `project.py:298-331`; строка 020 больше не говорит «not shipped». Не выполнен — BLK-PROPOSAL-040-NOT-SHIPPED и BLK-PROPOSALS-STALE-ROWS.
- **6 (release-audit findings)** — выполнен: `docs/overview.md:138-147` описывает четыре lane и journal-only как «every changed path sits under `.agentmarshal/journal/`», что совпадает с `gate.py:78,1252`; 0.4.1 больше не называется текущим релизом (`grep` по overview даёт только 0.6.0 и исторический 0.3.0); `docs/self-hosting-workflow.md:37-40,142-146` добавляет операторское acceptance и operational lane, точное покрытие findings подтверждается `gate.py:1770-1771`; поправка `UPGRADING.md:151-157` соответствует `gate.py:2272-2276`; открытый вопрос threat-model (`:520-531`) опирается на `gate-lanes/spec.md:249-250` («a link or a non-blob at the file's path refuses as not a file»). Теста нет.
- **7 (версия)** — выполнен: `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:10` — все `0.6.0`; демонстрируют `tests/test_smoke.py::test_version_is_declared` (:47-48) и `tests/test_smoke.py::test_console_version_prints_package_version` (:51-58, через `-m agentmarshal --version`).
- **8 (история, ссылки, границы)** — выполнен в части ссылок и границ: все добавленные ссылки резолвятся (`docs/adr/ADR-0013-…md`, `UPGRADING.md`, `proposals/044-…md`, `proposals/045-…md`, `../adr/ADR-0018-…md`), изменены только файлы из scope, `0.6.0.dev0` остался лишь в append-only записях журнала; единственная правка истории — разрешённая поправка 0.4.1 → 0.5.0. Полную CI-последовательность не запускал (read-only snapshot, не git-репозиторий) — опираюсь на утверждение координатора.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "f1f8af8df098a009b0dfad3b24413e183033eaf0",
  "verdict": "changes_required",
  "findings": [
    "BLK-OPENSPEC-MANIFEST-PATH",
    "BLK-SWITCH-OFF-CONTRACT-SCOPE",
    "BLK-SESSION-ID-ALREADY-SHIPPED",
    "BLK-PROPOSAL-040-NOT-SHIPPED",
    "BLK-PROPOSALS-STALE-ROWS",
    "BLK-REPORT-UNMEASURED-RENDERING"
  ],
  "advisory_findings": [
    "ADV-CODE-SPAN-LINE-WRAP",
    "ADV-EXTENSION-LIST-SCOPE"
  ],
  "classes": {
    "BLK-OPENSPEC-MANIFEST-PATH": "claim-accuracy",
    "BLK-SWITCH-OFF-CONTRACT-SCOPE": "claim-accuracy",
    "BLK-SESSION-ID-ALREADY-SHIPPED": "claim-accuracy",
    "BLK-PROPOSAL-040-NOT-SHIPPED": "claim-accuracy",
    "BLK-PROPOSALS-STALE-ROWS": "contract-mismatch",
    "BLK-REPORT-UNMEASURED-RENDERING": "claim-accuracy",
    "ADV-CODE-SPAN-LINE-WRAP": "style",
    "ADV-EXTENSION-LIST-SCOPE": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "ls .agentmarshal/extensions/ and grep version in .agentmarshal/extensions/openspec.toml", "result": "only openspec.toml (file form); line 20 version = \"1.15.0\"; no openspec/manifest.toml directory exists"},
      {"what": "grep -n scope src/agentmarshal/switch_off.py", "result": "line 463: scope = [\".agentmarshal/switches.toml\"] — the only scope line in the generated contract"},
      {"what": "grep -rn 'cli_session|report_ready' src/agentmarshal/journal/records.py src/agentmarshal/cli.py", "result": "records.py:208,209,520,521,840,848,2288,2289,2335,2336; cli.py:424 --cli-session, cli.py:426 --report-ready"},
      {"what": "read templates/journal-transaction.sh", "result": "lines 64-65 refuse unless on the default branch; line 116 git switch -c \"$branch\" switches the working tree"},
      {"what": "grep -rn 'if-missing' src/agentmarshal/cli.py; grep -n evidence src/agentmarshal/journal/records.py", "result": "cli.py:463 --if-missing; records.py:270 review optional fields include 'evidence'"},
      {"what": "read _cost_lines and format_report in src/agentmarshal/journal/report.py", "result": "report.py:730-747,778-779,811-812 append \\tunmeasured=<n> to existing lines; 'unmeasured_without_cost' appears only as a dataclass field name; no json/asdict in the module"},
      {"what": "grep -rn 'operational transaction|journal-only transaction|changes_required verdicts' src/agentmarshal", "result": "gate.py:1352,1355 the two PASS lines verbatim; gate.py:2262-2276 the WARN/INFO count lines"},
      {"what": "grep -n '^### |^#### ' openspec/specs/extension-stages/spec.md and gate-lanes/spec.md", "result": "all scenario titles the threat model cites exist verbatim (lines 80, 92, 96, 276, 308, 476); gate-lanes requirement at 241 with 'a link or a non-blob at the file's path refuses as not a file' at 249-250"},
      {"what": "grep -n 'not granted|changed after approval|switched off (|shared switches file unreadable|skipped as sent|tokens=unmeasured|Reviewed commit' across src/", "result": "every quoted result line in the notes matches the code: stages.py:507,514,961,962,1388; extension_trust.py:733,741; outbox.py:723; status_view.py:317,684,692; cli.py:1445"},
      {"what": "ls .agentmarshal/journal/tasks/CR-2*/records to find the last completed task", "result": "CR-233 and CR-235 carry completed records; CR-236 and CR-237 carry only opened — so CR-235 is the last completed task before CR-234"},
      {"what": "grep -rn '0\\.6\\.0' pyproject.toml src/agentmarshal/__init__.py uv.lock tests/test_smoke.py", "result": "pyproject.toml:3, __init__.py:3, uv.lock:10 and tests/test_smoke.py:48 all 0.6.0; no 0.6.0.dev0 outside append-only journal records"},
      {"what": "existence check of every link added by the diff", "result": "docs/adr/ADR-0013-…md, docs/adr/ADR-0018-…md, docs/proposals/044-…md, docs/proposals/045-…md, UPGRADING.md all exist"}
    ],
    "read": [
      "CHANGELOG.md (0.6.0 section and 0.5.0 section)",
      "UPGRADING.md",
      "README.md",
      "docs/threat-model.md",
      "docs/proposals/README.md",
      "docs/README.md",
      "docs/overview.md",
      "docs/self-hosting-workflow.md",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/journal/gate.py (lanes, lifecycle, warn and count blocks)",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/journal/status_view.py",
      "src/agentmarshal/journal/records.py (schema constants and field registries)",
      "src/agentmarshal/project.py (outbox scaffold)",
      "src/agentmarshal/record_ext.py",
      "src/agentmarshal/journal/validate.py",
      "src/agentmarshal/cli.py (accept, complete, status --base, record-session)",
      "templates/journal-transaction.sh",
      ".github/scripts/check_release_audit.py",
      ".github/workflows/release.yml",
      "openspec/specs/extension-stages/spec.md",
      "openspec/specs/gate-lanes/spec.md",
      "openspec/specs/session-activity/spec.md (unmeasured requirements)",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0018-governing-the-contract.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md",
      "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md",
      "docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md",
      "tests/test_smoke.py",
      "tests/test_unmeasured_session_usage.py"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review of a snapshot that is not a git repository; the coordinator states the full sequence passed on the reviewed commit and the diff is documentation plus a version bump"}
    ]
  },
  "evidence": {
    "BLK-OPENSPEC-MANIFEST-PATH": "CHANGELOG.md:193-196 names `.agentmarshal/extensions/openspec/manifest.toml`; `ls .agentmarshal/extensions/` -> `openspec.toml` only, and `.agentmarshal/extensions/openspec.toml:18-20` is schema = 1 / name = \"openspec\" / version = \"1.15.0\"",
    "BLK-SWITCH-OFF-CONTRACT-SCOPE": "CHANGELOG.md:77-79 vs src/agentmarshal/switch_off.py:463 (`scope = [{json.dumps(SWITCHES_RELPATH)}]`, the only scope line, SWITCHES_RELPATH = \".agentmarshal/switches.toml\" per switches.py:49) and openspec/specs/gate-lanes/spec.md:177-178,188-190 (`declares scope exactly [\".agentmarshal/switches.toml\"]`; any other scope takes the lane it takes today)",
    "BLK-SESSION-ID-ALREADY-SHIPPED": "CHANGELOG.md:218-220 vs docs/adr/ADR-0022-…md:133 (`cli_session` — the CLI session id a resume needs | proposal 042), src/agentmarshal/journal/records.py:208,520,2288,2335, src/agentmarshal/cli.py:424 (`--cli-session`) and CHANGELOG.md:336-338 (0.5.0: \"`commit`, `model`, `trace`, `cli_session`, `report_ready` and `fallback_reason`. `record-session` writes them all through new flags\")",
    "BLK-PROPOSAL-040-NOT-SHIPPED": "docs/proposals/README.md:155 (\"the checkout-free write shipped in 0.6.0\") vs docs/proposals/040-…md:59-64 (\"without switching the user's working tree … so parallel tasks do not contend on one checkout\") and templates/journal-transaction.sh:64-65 (refuses unless on the default branch) and :116 (`git switch -c \"$branch\"`)",
    "BLK-PROPOSALS-STALE-ROWS": "docs/proposals/README.md:175 (026: \"`record-session --if-missing` and the per-file leak scan accepted, not yet shipped\"; the `evidence` field) vs cli.py:463, records.py:270 and the same file's row :152 (037) which says the leak scan shipped in 0.5.0; :116 (041 \"report finished session flag … not shipped yet\") vs records.py:209 + cli.py:426; :117 (042 \"the session-id field … not shipped yet\") vs records.py:208 + cli.py:424; :174 (025 \"mechanism undecided\") vs docs/adr/ADR-0015-…md:1-17 and CHANGELOG.md:250-256",
    "BLK-REPORT-UNMEASURED-RENDERING": "CHANGELOG.md:185-186 vs src/agentmarshal/journal/report.py:730-734 (`unmeasured_field = f\"\\tunmeasured={sums.unmeasured_without_cost}\"`), :742 (`lines.append(line + unmeasured_field)`), :779, :812, and openspec/specs/session-activity/spec.md:506,648 (\"`unmeasured=<n>` as its last field and nothing more\"); `unmeasured_without_cost` is printed nowhere and report.py has no json output",
    "ADV-CODE-SPAN-LINE-WRAP": "CHANGELOG.md:164-165 (`` `.agentmarshal/journal/\\ntasks/<task-id>/` ``) and CHANGELOG.md:194-195 (`` `.agentmarshal/extensions/openspec/\\nmanifest.toml` ``) — inline code spanning a newline renders with a space inside the path",
    "ADV-EXTENSION-LIST-SCOPE": "CHANGELOG.md:30-34 (\"per shared extension\") vs src/agentmarshal/extension_trust.py:719-742, where `if not entry.is_dir(): continue` (724-725) skips a file-form extension such as .agentmarshal/extensions/openspec.toml, and extension_trust.py:13-15 scopes `list` to \"each directory-form extension's state\""
  }
}
AGENTMARSHAL_VERDICT_END
